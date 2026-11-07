# 唱机绘制（H4 拟物升级 / PL002 形态分化）：按载体类型三分形态——
# vinyl 黑胶转盘（唱针真实几何 + 拖拽寻曲）/ cassette 磁带仓（观察窗双卷轴 + 双飞轮）/ cd 碟舱（中心孔 + 封面环带）
# 转盘旋转惯性缓动启停；唱针角映射面内播放进度（仅黑胶）；动画时长读 ui.json；类型级转速经 set_spin_ms 注入

import math

from PySide6.QtCore import QPointF, QRectF, Qt, QTimer, Signal
from PySide6.QtGui import QColor, QPainter, QPainterPath, QPen, QPixmap, QRadialGradient
from PySide6.QtWidgets import QWidget

from config.static.static_config import get_static_config
from modules.items.model import Item
from ui.widgets.parts import (
    REEL_BASE_SPEED,
    REEL_RADIUS_MAX,
    REEL_RADIUS_MIN,
    draw_reel,
    reel_factor,
    texture_enabled,
    texture_pixmap,
)
from utils.logger import get_logger

# 模块日志（FIX006.7：未知形态回退告警——容错登记制条目⑥可观测）
_logger = get_logger("ui.deck_widget")

# 静态配置一次解包
_SC = get_static_config()

# 唱针几何常量（视觉常量豁免先例：绘制几何不外置配置；坐标均为控件矩形比例）
_PIVOT_X = 0.88  # 唱臂枢轴 x（矩形宽比例，盘缘右上外侧）
_PIVOT_Y = 0.10  # 唱臂枢轴 y（矩形高比例，顶部）
_ARM_LENGTH = 0.78  # 臂长（矩形宽比例）
_ANGLE_START = 8.0  # 落针角（度）：唱针落在盘缘外圈（面内进度 0）
_ANGLE_RANGE = 24.0  # 扫过角（度）：面内进度 0→1 的角度跨度（盘缘→盘标边缘）
_ANGLE_REST = -4.0  # 静息角（度）：唱针抬起停在盘外
_DRAG_MIN = -8.0  # 拖拽角度下钳制（度）
_DRAG_MAX = _ANGLE_START + _ANGLE_RANGE + 12.0  # 拖拽角度上钳制（度）
_DROP_MIN = _ANGLE_START - 2.0  # 有效落针角下界（度）
_DROP_MAX = _ANGLE_START + _ANGLE_RANGE + 2.0  # 有效落针角上界（度）
_HIT_RADIUS = 27.0  # 唱针命中半径（像素，以唱针尖端为圆心）
_NEEDLE_FINE_STEP = 0.1  # Shift 精调系数（拖拽增量缩放）
_SPIN_EASE = 2.2  # 转盘惯性趋近系数（speed += (target-speed)*min(1, dt*k)）
# 磁带仓观察窗卷轴基准角速度：走 parts.REEL_BASE_SPEED 单源（FIX006.9 收敛）


class DeckWidget(QWidget):
    # 唱机绘制控件：转盘按播放态旋转（惯性缓动），唱针按面内进度落针（可拖拽寻曲）

    needle_drag_started = Signal()  # 拖针开始（路由方接 engine.pause，拖拽期间静音/暂停）
    needle_dropped = Signal(float)  # 落针（面内比例 0-1；路由方接 engine.seek_side）

    def __init__(self, item: Item | None = None, parent: QWidget | None = None) -> None:
        # 初始化：角度/唱针状态；30ms 定时器驱动动画；时长读 ui.json；动画开关默认开
        super().__init__(parent)
        self._item = item
        self._playing = False
        self._item_type = "vinyl"  # PL002：载体形态（vinyl/cassette/cd，set_item_type 注入）
        self._cover: QPixmap | None = None  # PL002：CD 封面环带用（deck_view 注入）
        self._angle = 0.0
        self._spin_speed = 0.0  # 转盘角速度（度/秒，惯性缓动）
        self._reel_angle_l = 0.0  # PL002 磁带仓观察窗左卷轴角（度）
        self._reel_angle_r = 0.0  # 右卷轴角（度）
        self._tonearm_pos = 0.0  # 0=抬起 1=落下
        self._side_progress = 0.0  # 面内进度 0-1（唱针落针角映射源）
        self._dragging = False  # 拖针进行中（唱针角度直接跟随鼠标）
        self._drag_angle = _ANGLE_REST  # 拖拽当前角度（度）
        self._last_pointer_angle = 0.0  # 上一帧指针绕枢轴角（度，解卷用）
        self._animations_enabled = True
        self._texture_on = False  # PL005.4 贴图打底开关（set_realism 随档位更新）
        self._realism_level = ""  # 当前拟真度档位名（refined/realistic 差异化叠加用）
        ui = _SC.ui
        anim = ui.get("animation", {}) if isinstance(ui, dict) else {}
        self._spin_ms = max(
            1, int(anim.get("record_spin_ms", 2000))
        )  # E0.3 对称保护（防除零）；默认值被 set_spin_ms 类型级覆盖
        self._drop_ms = int(anim.get("tonearm_drop_ms", 500))
        self._tick_ms = int(ui.get("spin_tick_ms", 30))
        self.timer = QTimer(self)
        self.timer.setInterval(self._tick_ms)
        self.timer.timeout.connect(self._tick)

    def set_animations_enabled(self, enabled: bool) -> None:
        # 动画开关（A13.3 档位联动/C0.1）：关闭时停定时器 + 唱针瞬时落位；播放中重新启用时重启定时器
        # 拖拽寻曲是交互不是动画：关闭档位下拖拽仍可用（松手瞬时归位不走缓动）
        self._animations_enabled = enabled
        if not enabled:
            self.timer.stop()
            if self._playing:
                self._tonearm_pos = 1.0
            self.update()
        elif self._playing:
            self.timer.start()

    @property
    def angle(self) -> float:
        # 当前转盘角度（测试断言用）
        return self._angle

    @property
    def tonearm_position(self) -> float:
        # 唱针位置 0-1（测试断言用）
        return self._tonearm_pos

    def set_realism(self, level: str) -> None:
        # 拟真度档位注入（PL005.4）：贴图打底开关随 effects.json levels[level].texture；
        # refined = 贴图打底（跳手绘纹理细节）；realistic = 贴图 + 手绘纹理层全开；缺失档宽容关闭
        self._realism_level = str(level)
        self._texture_on = texture_enabled(self._realism_level)
        self.update()

    def set_spin_ms(self, spin_ms: int) -> None:
        # 类型级转速（H2：item_types.spin_ms_per_rev；载入物品时注入，非法回退默认）
        try:
            value = int(spin_ms)
        except (TypeError, ValueError):
            value = 0
        if value > 0:
            self._spin_ms = value

    def set_item_type(self, key: str, cover: QPixmap | None = None) -> None:
        # 载体形态切换（PL002）：vinyl/cassette/cd 三分绘制；CD 附封面环带 pixmap（可 None）
        # 未知键回退 vinyl（宽容，FIX006.7：告警一次——容错登记制条目⑥）；切换后重绘
        normalized = str(key)
        if normalized not in ("vinyl", "cassette", "cd"):
            _logger.warning("未知载体类型键（按黑胶绘制兜底）: %s", key)
            normalized = "vinyl"
        self._item_type = normalized
        self._cover = cover
        self.update()

    def set_progress(self, fraction: float) -> None:
        # 面内进度注入（H4：唱针落针角映射源；拖拽中不覆盖预览角）
        if isinstance(fraction, (int, float)) and not isinstance(fraction, bool):
            self._side_progress = min(1.0, max(0.0, float(fraction)))
            if not self._dragging:
                self.update()

    def set_playing(self, playing: bool) -> None:
        # 播放态切换：播放 → 定时器启动（动画关时瞬时落针不转）；停止 → 定时器停止 + 唱针瞬时抬起
        # 拖拽中不抢唱针控制权（抬起/落下渲染让位于拖拽预览，松手后由拖拽收尾逻辑归位）
        self._playing = playing
        if self._dragging:
            return
        if playing:
            if self._animations_enabled:
                self.timer.start()
            else:
                self._tonearm_pos = 1.0
                self.update()
        else:
            self.timer.stop()
            self._tonearm_pos = 0.0
            self.update()

    def _tick(self) -> None:
        # 动画帧：转盘角速度向目标（播放=3600000/spin_ms，停止=0）惯性趋近（H4 缓动启停）；
        # 唱针向目标（播放 1/停止 0）插值逼近
        dt = self._tick_ms / 1000.0
        if self._playing and self._animations_enabled:
            target_speed = 3600000.0 / self._spin_ms
        else:
            target_speed = 0.0
        self._spin_speed += (target_speed - self._spin_speed) * min(
            1.0, dt * _SPIN_EASE
        )
        if abs(self._spin_speed) > 0.02:
            self._angle = (self._angle + self._spin_speed * dt) % 360.0
        # PL002 磁带仓卷轴：播放中按恒线速推进（观察窗卷轴转动视觉）
        if self._item_type == "cassette" and self._playing and self._animations_enabled:
            self._reel_angle_l = (
                self._reel_angle_l - dt * REEL_BASE_SPEED / reel_factor(1.0 - self._side_progress)
            ) % 360.0
            self._reel_angle_r = (
                self._reel_angle_r - dt * REEL_BASE_SPEED / reel_factor(self._side_progress)
            ) % 360.0
        target = 1.0 if self._playing else 0.0
        step = self._tick_ms / max(1, self._drop_ms)
        if self._tonearm_pos < target:
            self._tonearm_pos = min(target, self._tonearm_pos + step)
        elif self._tonearm_pos > target:
            self._tonearm_pos = max(target, self._tonearm_pos - step)
        # FIX006.5（A006-P3-①）：收敛自停——拖针取消/暂停中落针等路径下定时器
        # 无外部停止信号，各量归位后自停（30ms 空重绘耗 CPU）；播放中/拖拽中不停
        if (
            not self._playing
            and not self._dragging
            and abs(self._spin_speed) <= 0.02
            and self._tonearm_pos == target
        ):
            self.timer.stop()
        self.update()

    def _arm_rect(self) -> QRectF:
        # 唱臂布局矩形（与 paintEvent 一致的内缩区域）
        return QRectF(self.rect()).adjusted(8, 8, -8, -8)

    def _pivot_point(self, rect: QRectF) -> QPointF:
        # 唱臂枢轴坐标（盘缘右上外侧）
        return QPointF(
            rect.left() + rect.width() * _PIVOT_X, rect.top() + rect.height() * _PIVOT_Y
        )

    def _tip_point(self, rect: QRectF, angle_deg: float) -> QPointF:
        # 唱针尖端坐标：枢轴 + 臂长 × (-sin 角, +cos 角)（角 0 = 正下方，负角摆向盘外）
        pivot = self._pivot_point(rect)
        rad = math.radians(angle_deg)
        length = rect.width() * _ARM_LENGTH
        return QPointF(
            pivot.x() - length * math.sin(rad), pivot.y() + length * math.cos(rad)
        )

    def _visual_angle(self) -> float:
        # 当前渲染角（度）：拖拽中 = 拖拽角；否则 = 静息角与落针角按 _tonearm_pos 插值
        if self._dragging:
            return self._drag_angle
        engaged = _ANGLE_START + _ANGLE_RANGE * self._side_progress
        return _ANGLE_REST + (engaged - _ANGLE_REST) * self._tonearm_pos

    def mousePressEvent(self, event) -> None:
        # 拖针开始：命中唱针尖端 27px 圆域才进入拖拽；记录指针绕枢轴角（解卷基准），
        # 发 needle_drag_started（路由方接 engine.pause——提针即停转）；
        # PL002：非黑胶形态无唱针，命中测试直接失败（零信号）
        if event.button() != Qt.MouseButton.LeftButton or self._item_type != "vinyl":
            super().mousePressEvent(event)
            return
        rect = self._arm_rect()
        tip = self._tip_point(rect, self._visual_angle())
        pos = QPointF(event.position())
        dx = pos.x() - tip.x()
        dy = pos.y() - tip.y()
        if dx * dx + dy * dy > _HIT_RADIUS * _HIT_RADIUS:
            super().mousePressEvent(event)
            return
        self._dragging = True
        self._drag_angle = self._visual_angle()
        pivot = self._pivot_point(rect)
        self._last_pointer_angle = self._pointer_angle(pivot, pos)
        self.needle_drag_started.emit()
        self.update()

    def mouseMoveEvent(self, event) -> None:
        # 拖拽中：指针绕枢轴角增量（±180° 解卷）驱动唱针角；Shift 缩为 0.1 精调；
        # 角度钳制在 [_DRAG_MIN, _DRAG_MAX]
        if not self._dragging:
            super().mouseMoveEvent(event)
            return
        pivot = self._pivot_point(self._arm_rect())
        pointer = self._pointer_angle(pivot, QPointF(event.position()))
        delta = pointer - self._last_pointer_angle
        if delta > 180.0:
            delta -= 360.0
        elif delta < -180.0:
            delta += 360.0
        self._last_pointer_angle = pointer
        if event.modifiers() & Qt.KeyboardModifier.ShiftModifier:
            delta *= _NEEDLE_FINE_STEP
        self._drag_angle = min(
            _DRAG_MAX, max(_DRAG_MIN, self._drag_angle + delta)
        )
        self.update()

    def mouseReleaseEvent(self, event) -> None:
        # 落针判定：角度在有效窗 [_DROP_MIN, _DROP_MAX] 内 → 发 needle_dropped（面内比例）；
        # 窗外（甩出/放回盘外）→ 静默取消，唱针按当前播放态归位
        if not self._dragging:
            super().mouseReleaseEvent(event)
            return
        self._dragging = False
        angle = self._drag_angle
        fraction = min(
            1.0, max(0.0, (angle - _ANGLE_START) / _ANGLE_RANGE)
        )
        if _DROP_MIN <= angle <= _DROP_MAX:
            self.needle_dropped.emit(fraction)
        # 收尾：动画开 → 定时器驱动唱针缓动归位（转盘惯性减速）；动画关 → 瞬时归位
        if self._animations_enabled:
            self.timer.start()
        else:
            self._tonearm_pos = 1.0 if self._playing else 0.0
            self.update()
        super().mouseReleaseEvent(event)

    @staticmethod
    def _pointer_angle(pivot: QPointF, pos: QPointF) -> float:
        # 指针绕枢轴角（度）：atan2(枢轴x-指针x, 指针y-枢轴y)，与唱针角坐标系同源
        return math.degrees(math.atan2(pivot.x() - pos.x(), pos.y() - pivot.y()))

    def paintEvent(self, event) -> None:
        # 绘制（PL002 分形态）：vinyl 转盘 + 唱针 / cassette 磁带仓 / cd 碟舱
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        rect = self._arm_rect()
        if self._item_type == "cassette":
            self._paint_cassette_deck(painter, rect)
        elif self._item_type == "cd":
            self._paint_cd(painter, rect)
        else:
            self._paint_vinyl(painter, rect)
        painter.end()

    def _paint_vinyl(self, painter: QPainter, rect: QRectF) -> None:
        # 黑胶形态（H4 现状 / PL005.4 贴图分层）：转盘（贴图或矢量槽纹）+ 唱针（真实几何）
        painter.save()
        painter.translate(rect.center())
        painter.rotate(self._angle)
        tex = texture_pixmap("vinyl_disc") if self._texture_on else None
        if tex is not None:
            # 贴图打底：盘面照片纹理（沟槽/高光已烘焙），随转盘角旋转；贴图自带透明边与盘缘
            painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform, True)
            painter.drawPixmap(
                QRectF(-rect.width() / 2, -rect.height() / 2, rect.width(), rect.height()),
                tex,
                QRectF(tex.rect()),
            )
            if self._realism_level == "realistic":
                # realistic 全量：手绘槽纹圈叠加（refined 跳过，防与烘焙沟槽打架）
                painter.setPen(QPen(QColor(34, 34, 34, 70), 1))
                painter.setBrush(Qt.BrushStyle.NoBrush)
                for i in range(4):
                    f = 0.55 + i * 0.08
                    painter.drawEllipse(
                        QRectF(
                            -rect.width() * f / 2,
                            -rect.height() * f / 2,
                            rect.width() * f,
                            rect.height() * f,
                        )
                    )
        else:
            gradient = QRadialGradient(0, 0, rect.width() / 2)
            gradient.setColorAt(0.0, QColor("#3a3a3a"))
            gradient.setColorAt(1.0, QColor("#0d0d0d"))
            painter.setBrush(gradient)
            painter.setPen(QPen(QColor("#555555"), 1))
            painter.drawEllipse(
                QRectF(-rect.width() / 2, -rect.height() / 2, rect.width(), rect.height())
            )
            painter.setPen(QPen(QColor("#222222"), 1))
            for i in range(4):
                f = 0.55 + i * 0.08
                painter.drawEllipse(
                    QRectF(
                        -rect.width() * f / 2,
                        -rect.height() * f / 2,
                        rect.width() * f,
                        rect.height() * f,
                    )
                )
        painter.restore()
        self._paint_tonearm(painter, rect)

    def _paint_cassette_deck(self, painter: QPainter, rect: QRectF) -> None:
        # 磁带仓形态（PL002.3）：深色壳 + 中央观察窗（共享卷轴，半径随面内进度胀缩）
        # + 双飞轮（角度随转盘角加速旋转，播放视觉）+ 底部走带路径 + 四角螺丝
        painter.save()
        # 外壳（PL005.4：贴图打底裁圆角矩形；回退深色渐变，拟磁带仓机身）
        shell_tex = texture_pixmap("cassette_shell") if self._texture_on else None
        if shell_tex is not None:
            shell_path = QPainterPath()
            shell_path.addRoundedRect(rect, 10, 10)
            painter.setClipPath(shell_path)
            painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform, True)
            painter.drawPixmap(rect, shell_tex, QRectF(shell_tex.rect()))
            painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.setPen(QPen(QColor("#55556a"), 1))
            painter.drawRoundedRect(rect, 10, 10)
        else:
            shell = QRadialGradient(rect.center(), rect.width() * 0.75)
            shell.setColorAt(0.0, QColor("#3d3d46"))
            shell.setColorAt(1.0, QColor("#1e1e26"))
            painter.setBrush(shell)
            painter.setPen(QPen(QColor("#55556a"), 1))
            painter.drawRoundedRect(rect, 10, 10)
        # 四角螺丝
        painter.setBrush(QColor("#777788"))
        painter.setPen(QPen(QColor("#44445a"), 1))
        offset = 12.0
        for cx, cy in (
            (rect.left() + offset, rect.top() + offset),
            (rect.right() - offset, rect.top() + offset),
            (rect.left() + offset, rect.bottom() - offset),
            (rect.right() - offset, rect.bottom() - offset),
        ):
            painter.drawEllipse(QPointF(cx, cy), 2.5, 2.5)
        # 观察窗（内嵌深色，窗内两卷轴经共享绘制；fill 左=1-进度 右=进度）
        win = QRectF(
            rect.left() + rect.width() * 0.16,
            rect.top() + rect.height() * 0.18,
            rect.width() * 0.68,
            rect.height() * 0.40,
        )
        painter.setBrush(QColor(20, 20, 26))
        painter.setPen(QPen(QColor("#55556a"), 1))
        painter.drawRoundedRect(win, 4, 4)
        r_max = win.height() * 0.42
        r_min = r_max * 0.42
        hub = r_min * 0.62
        centers = (
            QPointF(win.left() + win.width() * 0.26, win.center().y()),
            QPointF(win.left() + win.width() * 0.74, win.center().y()),
        )
        fills = (1.0 - self._side_progress, self._side_progress)
        angles = (self._reel_angle_l, self._reel_angle_r)
        for center, fill, angle in zip(centers, fills, angles):
            t = (reel_factor(fill) - REEL_RADIUS_MIN) / (REEL_RADIUS_MAX - REEL_RADIUS_MIN)
            draw_reel(painter, center, r_min + (r_max - r_min) * t, hub, angle)
        # 走带路径（窗内底部横线）
        painter.setPen(QPen(QColor("#4a3f36"), 1))
        painter.drawLine(
            QPointF(win.left() + win.width() * 0.12, win.bottom() - 3.0),
            QPointF(win.right() - win.width() * 0.12, win.bottom() - 3.0),
        )
        # 双飞轮（观察窗下方两侧，播放时随 _angle 加速旋转——辐条 3 根示意转动）
        fly_y = rect.top() + rect.height() * 0.72
        fly_r = rect.width() * 0.055
        fly_angle = self._angle * 1.8
        for cx in (
            rect.left() + rect.width() * 0.22,
            rect.right() - rect.width() * 0.22,
        ):
            center = QPointF(cx, fly_y)
            painter.setBrush(QColor("#8a8a9a"))
            painter.setPen(QPen(QColor("#55556a"), 1))
            painter.drawEllipse(center, fly_r, fly_r)
            painter.save()
            painter.translate(center)
            painter.rotate(fly_angle)
            painter.setPen(QPen(QColor("#3a3a46"), 1))
            for _ in range(3):
                painter.rotate(120.0)
                painter.drawLine(QPointF(0, 0), QPointF(0, -fly_r * 0.85))
            painter.restore()
        # 品牌标签条（壳体上部窄横条，拟磁带仓铭牌）
        painter.setBrush(QColor("#2a2a34"))
        painter.setPen(QPen(QColor("#44445a"), 1))
        painter.drawRect(
            QRectF(
                rect.left() + rect.width() * 0.3,
                rect.top() + rect.height() * 0.06,
                rect.width() * 0.4,
                rect.height() * 0.05,
            )
        )
        painter.restore()

    def _paint_cd(self, painter: QPainter, rect: QRectF) -> None:
        # CD 碟舱形态（PL002.4 / PL005.4 贴图分层）：碟面（贴图含孔镂空，或 OddEven 矢量）
        # + 封面环带 + 3 夹持爪 + 淡槽纹（realistic）
        center = rect.center()
        radius = rect.width() / 2
        painter.save()
        painter.translate(center)
        painter.rotate(self._angle)
        hole_r = radius * 0.08
        disc_tex = texture_pixmap("cd_disc") if self._texture_on else None
        if disc_tex is not None:
            # 贴图打底：碟面照片纹理（彩虹反射 + 中心孔透明已烘焙），随转盘角旋转
            painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform, True)
            painter.drawPixmap(
                QRectF(-radius, -radius, radius * 2, radius * 2),
                disc_tex,
                QRectF(disc_tex.rect()),
            )
        else:
            # 碟面：OddEven 双圆路径（外缘 + 中心孔）——孔洞真透出窗底色（非画深色圆模拟）
            disc = QPainterPath()
            disc.addEllipse(QPointF(0, 0), radius, radius)
            disc.addEllipse(QPointF(0, 0), hole_r, hole_r)
            disc.setFillRule(Qt.FillRule.OddEvenFill)
            disc_gradient = QRadialGradient(0, 0, radius)
            disc_gradient.setColorAt(0.0, QColor("#e2e6ec"))
            disc_gradient.setColorAt(0.6, QColor("#c8ccd4"))
            disc_gradient.setColorAt(1.0, QColor("#7a8088"))
            painter.setBrush(disc_gradient)
            painter.setPen(QPen(QColor("#5a5f66"), 1))
            painter.drawPath(disc)
        # 封面环带（r 22%..55% 环形裁剪内画封面；无封面画素色环 + 中心纹样）
        ring = QPainterPath()
        ring.addEllipse(QPointF(0, 0), radius * 0.55, radius * 0.55)
        ring.addEllipse(QPointF(0, 0), radius * 0.22, radius * 0.22)
        ring.setFillRule(Qt.FillRule.OddEvenFill)
        painter.save()
        painter.setClipPath(ring)
        if self._cover is not None:
            half = radius * 0.55
            painter.drawPixmap(
                QRectF(-half, -half, half * 2, half * 2).toRect(), self._cover
            )
        else:
            painter.setBrush(QColor("#8a9098"))
            painter.setPen(QPen(QColor("#6a6f76"), 1))
            painter.drawEllipse(QPointF(0, 0), radius * 0.55, radius * 0.55)
            painter.setPen(QPen(QColor("#6a6f76"), 1))
            painter.drawEllipse(QPointF(0, 0), radius * 0.34, radius * 0.34)
        painter.restore()
        # 淡槽纹两圈（封面环带外缘的盘面细纹；refined 贴图下跳过防与烘焙纹理打架）
        if not (disc_tex is not None and self._realism_level == "refined"):
            painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.setPen(QPen(QColor(90, 95, 102, 120), 1))
            painter.drawEllipse(QPointF(0, 0), radius * 0.66, radius * 0.66)
            painter.drawEllipse(QPointF(0, 0), radius * 0.78, radius * 0.78)
        # 夹持爪（孔缘 3 个 120° 短爪）+ 中轴环
        painter.setPen(QPen(QColor("#4a4f56"), 1))
        painter.setBrush(QColor("#6a6f76"))
        for i in range(3):
            painter.save()
            painter.rotate(i * 120.0)
            painter.drawRect(QRectF(-hole_r * 0.5, -hole_r * 1.9, hole_r, hole_r * 1.5))
            painter.restore()
        painter.setBrush(QColor("#3a3f46"))
        painter.drawEllipse(QPointF(0, 0), hole_r * 0.8, hole_r * 0.8)
        painter.restore()

    def _paint_tonearm(self, painter: QPainter, rect: QRectF) -> None:
        # 唱针绘制（H4 真实几何）：枢轴底座 + 配重（反向短臂）+ 臂杆（硬阴影双层）+ 唱头（尖端）
        angle_deg = self._visual_angle()
        pivot = self._pivot_point(rect)
        tip = self._tip_point(rect, angle_deg)
        rad = math.radians(angle_deg)
        # 配重：枢轴反方向短臂（模拟唱臂后端平衡锤）
        counter = QPointF(
            pivot.x() + rect.width() * 0.10 * math.sin(rad),
            pivot.y() - rect.height() * 0.10 * math.cos(rad),
        )
        # 硬阴影层（拟物立体感，Spun 2D 同款技法：偏移深色线代替模糊阴影）
        shadow = QPointF(tip.x() + 2.0, tip.y() + 2.0)
        shadow_pivot = QPointF(pivot.x() + 2.0, pivot.y() + 2.0)
        painter.setPen(QPen(QColor(0, 0, 0, 90), 5))
        painter.drawLine(shadow_pivot, shadow)
        # 臂杆主体
        painter.setPen(QPen(QColor("#c8c8c8"), 4))
        painter.drawLine(pivot, tip)
        # 枢轴底座 + 配重锤
        painter.setPen(QPen(QColor("#666666"), 1))
        painter.setBrush(QColor("#9a9a9a"))
        painter.drawEllipse(pivot, 6.0, 6.0)
        painter.setBrush(QColor("#7a7a7a"))
        painter.drawEllipse(counter, 5.0, 5.0)
        # 唱头（尖端小矩形，沿臂方向）
        painter.save()
        painter.translate(tip)
        painter.rotate(-angle_deg)
        painter.setBrush(QColor("#b0b0b0"))
        painter.setPen(QPen(QColor("#555555"), 1))
        painter.drawRect(QRectF(-3.0, -6.0, 6.0, 12.0))
        # 唱针尖（金属小点）
        painter.setBrush(QColor("#e8e8e8"))
        painter.drawEllipse(QPointF(0.0, 6.0), 1.8, 1.8)
        painter.restore()


# ===== ui/widgets/deck_widget.py 类/函数说明 =====
# _SC: 静态配置单例（动画时长）
# 几何常量（视觉常量豁免先例）：_PIVOT_X/_PIVOT_Y/_ARM_LENGTH 布局比例、
#   _ANGLE_START/_ANGLE_RANGE 落针角与扫过角、_ANGLE_REST 静息角、拖拽钳制/命中半径
# DeckWidget(QWidget): 唱机绘制（PL002 三形态分派：vinyl 转盘唱针 / cassette 磁带仓 / cd 碟舱）
#   set_item_type(key, cover): 载体形态切换（未知键回退 vinyl；CD 附封面环带 pixmap）
#   set_realism(level): 拟真度档位注入（PL005.4：贴图打底开关随 effects.json texture 键；
#     refined 跳手绘纹理细节防打架，realistic 全量叠加）
#   needle_drag_started/needle_dropped(float): 唱针交互信号（仅 vinyl；非 vinyl 命中直接失败）
#   set_playing(playing): 定时器启停（拖拽中不抢唱针控制权）
#   set_animations_enabled(enabled): 档位联动（拖拽属交互不受档位限制）
#   set_spin_ms(spin_ms): 类型级转速注入（item_types.spin_ms_per_rev，H2）
#   set_progress(fraction): 面内进度注入（唱针角/磁带仓卷轴胀缩共用，H4）
#   _tick(): 转盘角速度惯性趋近（缓动启停）+ 唱针位置插值
#   _visual_angle(): 渲染角（拖拽角优先，否则静息↔落针按 _tonearm_pos 插值）
#   mousePress/Move/ReleaseEvent: 拖针交互（27px 命中 → atan2 解卷拖拽 → 有效窗落针/窗外取消）
#   _paint_vinyl: 贴图盘面（回退矢量槽纹）+ realistic 槽纹圈叠加 + _paint_tonearm
#   _paint_cassette_deck: 仓壳（贴图裁圆角，回退渐变）+ 观察窗卷轴 + 双飞轮 + 走带线 + 螺丝
#   _paint_cd: 贴图碟面（回退 OddEven 镂空）+ 封面环带（22%..55%）+ 3 夹持爪 + 淡槽纹（refined 跳过）
#   angle/tonearm_position: 状态只读（验证断言）
#   设计理由：形态随载体切换消除语义冲突（磁带时右侧不再是无唱针的黑胶转盘）；
#     拖拽暂停/落针跳转全部经信号外抛（控件零业务依赖）；卷轴/带卷物理与贴图加载复用 ui/widgets/parts；
#     贴图缺失回退矢量绘制（装饰层不阻断，容错登记制）
#   关联配置：config/static/ui.json（animation.record_spin_ms/tonearm_drop_ms/spin_tick_ms）；
#     类型转速 item_types.json spin_ms_per_rev（set_spin_ms 注入）；
#     effects.json levels[].texture（贴图开关）+ data/textures/*.png（PL005.3 烘焙产物）
