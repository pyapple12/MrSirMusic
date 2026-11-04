# 唱机绘制（H4 拟物升级）：转盘旋转（惯性缓动启停）+ 唱针真实几何（枢轴/臂杆/唱头）
# 唱针角度映射面内播放进度，支持拖拽寻曲（按下暂停 → 绕枢轴拖动 → 松手落针按比例跳转）
# 动画时长读 ui.json；类型级转速经 set_spin_ms 注入（item_types.json spin_ms_per_rev）

import math

from PySide6.QtCore import QPointF, QRectF, Qt, QTimer, Signal
from PySide6.QtGui import QColor, QPainter, QPen, QRadialGradient
from PySide6.QtWidgets import QWidget

from config.static.static_config import get_static_config
from modules.items.model import Item

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


class DeckWidget(QWidget):
    # 唱机绘制控件：转盘按播放态旋转（惯性缓动），唱针按面内进度落针（可拖拽寻曲）

    needle_drag_started = Signal()  # 拖针开始（路由方接 engine.pause，拖拽期间静音/暂停）
    needle_dropped = Signal(float)  # 落针（面内比例 0-1；路由方接 engine.seek_side）

    def __init__(self, item: Item | None = None, parent: QWidget | None = None) -> None:
        # 初始化：角度/唱针状态；30ms 定时器驱动动画；时长读 ui.json；动画开关默认开
        super().__init__(parent)
        self._item = item
        self._playing = False
        self._angle = 0.0
        self._spin_speed = 0.0  # 转盘角速度（度/秒，惯性缓动）
        self._tonearm_pos = 0.0  # 0=抬起 1=落下
        self._side_progress = 0.0  # 面内进度 0-1（唱针落针角映射源）
        self._dragging = False  # 拖针进行中（唱针角度直接跟随鼠标）
        self._drag_angle = _ANGLE_REST  # 拖拽当前角度（度）
        self._last_pointer_angle = 0.0  # 上一帧指针绕枢轴角（度，解卷用）
        self._animations_enabled = True
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

    def set_spin_ms(self, spin_ms: int) -> None:
        # 类型级转速（H2：item_types.spin_ms_per_rev；载入物品时注入，非法回退默认）
        try:
            value = int(spin_ms)
        except (TypeError, ValueError):
            value = 0
        if value > 0:
            self._spin_ms = value

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
        target = 1.0 if self._playing else 0.0
        step = self._tick_ms / max(1, self._drop_ms)
        if self._tonearm_pos < target:
            self._tonearm_pos = min(target, self._tonearm_pos + step)
        elif self._tonearm_pos > target:
            self._tonearm_pos = max(target, self._tonearm_pos - step)
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
        # 发 needle_drag_started（路由方暂停——拟物语义：提针即停转）
        if event.button() != Qt.MouseButton.LeftButton:
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
        # 绘制：转盘（旋转画槽纹）+ 唱针（枢轴/臂杆/唱头/配重，按视觉角摆动）
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        rect = self._arm_rect()
        painter.save()
        painter.translate(rect.center())
        painter.rotate(self._angle)
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
        painter.end()

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
# DeckWidget(QWidget): 唱机绘制（转盘惯性旋转 + 唱针真实几何 + 拖拽寻曲）
#   needle_drag_started: 拖针开始信号（路由方接 engine.pause——提针停转）
#   needle_dropped(float): 落针信号（面内比例 0-1，路由方接 engine.seek_side）
#   set_playing(playing): 定时器启停（拖拽中不抢唱针控制权）
#   set_animations_enabled(enabled): 档位联动（拖拽属交互不受档位限制）
#   set_spin_ms(spin_ms): 类型级转速注入（item_types.spin_ms_per_rev，H2）
#   set_progress(fraction): 面内进度注入（唱针落针角映射源，H4）
#   _tick(): 转盘角速度惯性趋近（缓动启停）+ 唱针位置插值
#   _visual_angle(): 渲染角（拖拽角优先，否则静息↔落针按 _tonearm_pos 插值）
#   mousePress/Move/ReleaseEvent: 拖针交互（27px 命中 → atan2 解卷拖拽 → 有效窗落针/窗外取消）
#   _paint_tonearm: 枢轴/配重/臂杆（硬阴影）/唱头绘制
#   angle/tonearm_position: 状态只读（验证断言）
#   设计理由：唱针角 ↔ 面内进度线性映射（角度几何参考拟物唱机实物比例）；
#     拖拽暂停/落针跳转全部经信号外抛（控件零业务依赖）
#   关联配置：config/static/ui.json（animation.record_spin_ms/tonearm_drop_ms/spin_tick_ms）；
#     类型转速 item_types.json spin_ms_per_rev（set_spin_ms 注入）
