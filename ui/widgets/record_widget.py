# 物品拟物绘制（A12.1）：按 ItemType.shape 绘制形态（circle 黑胶/CD、rect 磁带盒），渐变+阴影质感
# H6/PL002.1 磁带动画：卷轴随播放旋转（恒线速模型 + 带卷胀缩），仅唱机实例驱动（置物架卡片保持静态）

from pathlib import Path

from PySide6.QtCore import QPointF, QRectF, QTimer
from PySide6.QtGui import (
    QColor,
    QLinearGradient,
    QPainter,
    QPen,
    QPixmap,
    QRadialGradient,
)
from PySide6.QtWidgets import QWidget

from config.static.static_config import get_static_config
from modules.cover.providers import resolve_cover
from modules.items.model import Item
from ui.widgets.parts import REEL_RADIUS_MAX, REEL_RADIUS_MIN, draw_reel, reel_factor

# 静态配置一次解包
_SC = get_static_config()

# 卷轴动画常量（视觉常量豁免先例）：基准角速度（度/秒）按带卷半径因子衰减（恒线速拟真）
_REEL_BASE_SPEED = 240.0  # 播放基准角速度（度/秒，除以半径因子）
_REEL_WIND_SPEED = 900.0  # 快进/倒带角速度基准（度/秒，scrub 拖动时）


class RecordWidget(QWidget):
    # 物品拟物绘制控件：circle（黑胶同心圆 + 封面中心）/ rect（磁带盒 + 卷轴动画）

    def __init__(self, item: Item | None = None, parent: QWidget | None = None) -> None:
        # 初始化：绑定物品 + 加载封面（resolve_cover 兜底占位图）+ 效果器列表空；
        # H6 卷轴动画状态（仅唱机实例经 set_playing 启动定时器，置物架卡片保持静态）
        super().__init__(parent)
        self._item = item
        self._cover: QPixmap | None = None
        self._effects: list = []
        self._playing = False
        self._animations_enabled = True
        self._reel_progress = 0.0  # 面内进度 0-1（左卷满→右卷满）
        self._reel_angle_l = 0.0  # 左卷轴角度（度）
        self._reel_angle_r = 0.0  # 右卷轴角度（度）
        self._wind = 0.0  # wind 方向（scrub 拖动 ±1，静止 0）
        self._tick_ms = int(_SC.ui.get("spin_tick_ms", 30))
        self.timer = QTimer(self)
        self.timer.setInterval(self._tick_ms)
        self.timer.timeout.connect(self._tick)
        if item is not None:
            self.set_item(item)

    def set_effects(self, effects: list) -> None:
        # 设置效果器列表（A13.1 registry.apply 装配；绘制时叠加）并重绘
        self._effects = list(effects)
        self.update()

    def effects(self) -> list:
        # 当前效果器列表（验证断言用）
        return self._effects

    def set_item(self, item: Item) -> None:
        # 换物品：先清空封面（C0.3 防旧封面残留）→ 重新加载有效封面 → 重绘；
        # H6 换物品复位卷轴动画状态（进度/风向归零）
        self._item = item
        self._cover = None
        self._reel_progress = 0.0
        self._wind = 0.0
        cover = resolve_cover(item)
        if cover and Path(cover).is_file():
            pixmap = QPixmap(cover)
            if not pixmap.isNull():
                self._cover = pixmap
        self.update()

    def set_playing(self, playing: bool) -> None:
        # H6 播放态切换：播放且动画开且当前是磁带 → 定时器启动；停止 → 停定时器 + 风向复位
        # （置物架卡片实例从不调本方法，保持静态）
        self._playing = playing
        if playing and self._animations_enabled and self._is_cassette():
            self.timer.start()
        elif not playing:
            self.timer.stop()
            self._wind = 0.0
            self.update()

    def set_animations_enabled(self, enabled: bool) -> None:
        # H6 档位联动：关闭时停定时器（卷轴冻结）；播放中重新启用且是磁带时重启
        self._animations_enabled = enabled
        if not enabled:
            self.timer.stop()
        elif self._playing and self._is_cassette():
            self.timer.start()

    def set_reel_progress(self, fraction: float) -> None:
        # H6 面内进度注入：卷带胀缩映射源（左卷满→右卷满；越界钳制）
        if isinstance(fraction, (int, float)) and not isinstance(fraction, bool):
            self._reel_progress = min(1.0, max(0.0, float(fraction)))

    def set_wind(self, direction: float) -> None:
        # H6 scrub 拖动方向（+1 快进 / -1 倒带 / 0 复位）：卷轴按 wind 速度旋转
        value = float(direction)
        self._wind = min(1.0, max(-1.0, value))

    def _is_cassette(self) -> bool:
        # 当前物品是否磁带形态（rect 才有卷轴动画）
        return self._item is not None and self._item.type.shape == "rect"

    def _tick(self) -> None:
        # H6 动画帧：恒线速模型——角速度 = 基准 / 半径因子（卷多的盘转得慢，拟物物理）；
        # scrub 风向非零时覆盖基准速度（快进/倒带视觉）；角度取模累计
        dt = self._tick_ms / 1000.0
        factor_l = reel_factor(1.0 - self._reel_progress)
        factor_r = reel_factor(self._reel_progress)
        base = (
            self._wind * _REEL_WIND_SPEED
            if abs(self._wind) > 0.01
            else _REEL_BASE_SPEED
        )
        self._reel_angle_l = (self._reel_angle_l - dt * base / factor_l) % 360.0
        self._reel_angle_r = (self._reel_angle_r - dt * base / factor_r) % 360.0
        self.update()

    def pixmap_image(self) -> QPixmap:
        # 当前渲染结果（验证用：非空断言）
        return self.grab()

    def paintEvent(self, event) -> None:
        # 绘制入口：按 shape 分派（circle 黑胶 / rect 磁带盒 / 其他占位）+ 效果器叠加
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        rect = QRectF(self.rect()).adjusted(6, 6, -6, -6)
        shape = self._item.type.shape if self._item is not None else "circle"
        if shape == "rect":
            self._paint_cassette(painter, rect)
        else:
            self._paint_record(painter, rect)
        for effect in self._effects:
            effect.apply(painter, rect)
        painter.end()

    def _paint_record(self, painter: QPainter, rect: QRectF) -> None:
        # 黑胶/CD：径向渐变圆盘 + 同心槽纹 + 中心封面圆
        painter.save()
        gradient = QRadialGradient(rect.center(), rect.width() / 2)
        gradient.setColorAt(0.0, QColor("#3a3a3a"))
        gradient.setColorAt(1.0, QColor("#0d0d0d"))
        painter.setBrush(gradient)
        painter.setPen(QPen(QColor("#555555"), 1))
        painter.drawEllipse(rect)
        # 槽纹（同心细圈）
        painter.setPen(QPen(QColor("#222222"), 1))
        for i in range(4):
            factor = 0.55 + i * 0.08
            r = QRectF(
                rect.center().x() - rect.width() * factor / 2,
                rect.center().y() - rect.height() * factor / 2,
                rect.width() * factor,
                rect.height() * factor,
            )
            painter.drawEllipse(r)
        # 中心封面圆
        cover_size = rect.width() * 0.4
        cover_rect = QRectF(
            rect.center().x() - cover_size / 2,
            rect.center().y() - cover_size / 2,
            cover_size,
            cover_size,
        )
        painter.save()
        painter.setClipPath(self._round_rect_path(cover_rect, cover_size / 2))
        if self._cover is not None:
            painter.drawPixmap(cover_rect.toRect(), self._cover)
        else:
            painter.fillRect(cover_rect, QColor("#8B6F47"))
        painter.restore()
        painter.restore()

    def _paint_cassette(self, painter: QPainter, rect: QRectF) -> None:
        # 磁带盒：圆角矩形渐变壳 + 上窗口（半透明）+ 底部标签（色块占位；B3.2 注释修正）
        painter.save()
        gradient = QLinearGradient(rect.topLeft(), rect.bottomLeft())
        gradient.setColorAt(0.0, QColor("#4a4a55"))
        gradient.setColorAt(1.0, QColor("#23232a"))
        painter.setBrush(gradient)
        painter.setPen(QPen(QColor("#666677"), 1))
        painter.drawRoundedRect(rect, 10, 10)
        # 上窗口
        win = QRectF(
            rect.left() + rect.width() * 0.25,
            rect.top() + rect.height() * 0.15,
            rect.width() * 0.5,
            rect.height() * 0.35,
        )
        painter.setBrush(QColor(30, 30, 30, 200))
        painter.drawRoundedRect(win, 4, 4)
        # H6 观察窗内容：双卷轴（带卷胀缩 + 花键 hub 旋转）+ 走带路径
        self._paint_reels(painter, win)
        # 底部标签
        label_rect = QRectF(
            rect.left() + rect.width() * 0.15,
            rect.top() + rect.height() * 0.62,
            rect.width() * 0.7,
            rect.height() * 0.28,
        )
        painter.setBrush(QColor("#8B6F47"))
        painter.drawRoundedRect(label_rect, 4, 4)
        painter.restore()

    @staticmethod
    def _round_rect_path(rect: QRectF, radius: float):
        # 圆角矩形裁剪路径（封面圆形裁剪用）
        from PySide6.QtGui import QPainterPath

        path = QPainterPath()
        path.addRoundedRect(rect, radius, radius)
        return path

    def _paint_reels(self, painter: QPainter, win: QRectF) -> None:
        # H6/PL002.1 卷带绘制（共享 parts.draw_reel）：两卷带圆（半径按带卷物理胀缩）
        # + 底部走带路径细线；fill 左卷 = 1-进度、右卷 = 进度（播放推进左→右）
        r_max = win.height() * 0.44
        r_min = r_max * (REEL_RADIUS_MIN / REEL_RADIUS_MAX)
        hub = r_min * 0.62
        centers = (
            QPointF(win.left() + win.width() * 0.25, win.center().y()),
            QPointF(win.left() + win.width() * 0.75, win.center().y()),
        )
        fills = (1.0 - self._reel_progress, self._reel_progress)
        angles = (self._reel_angle_l, self._reel_angle_r)
        for center, fill, angle in zip(centers, fills, angles):
            factor = reel_factor(fill)
            t = (factor - REEL_RADIUS_MIN) / (REEL_RADIUS_MAX - REEL_RADIUS_MIN)
            radius = r_min + (r_max - r_min) * t
            draw_reel(painter, center, radius, hub, angle)
        # 走带路径（两卷下方横线，模拟带体路径）
        painter.setPen(QPen(QColor("#4a3f36"), 1))
        painter.drawLine(
            QPointF(win.left() + win.width() * 0.25, win.bottom() - 2.0),
            QPointF(win.left() + win.width() * 0.75, win.bottom() - 2.0),
        )


# ===== ui/widgets/record_widget.py 类/函数说明 =====
# RecordWidget(QWidget): 物品拟物绘制（H6 磁带卷轴动画；circle/rect 双形态）
#   set_item(item): 换物品（resolve_cover 加载封面 → update；卷轴状态复位）
#   set_playing(playing): 播放态联动（播放 + 动画开 + 磁带 → 定时器启动；仅唱机实例被调）
#   set_animations_enabled(enabled): 档位联动（关闭冻结卷轴）
#   set_reel_progress(fraction): 面内进度注入（卷带胀缩）
#   set_wind(direction): scrub 风向（±1 快进/倒带视觉，0 复位）
#   _tick(): 恒线速卷轴动画帧（角速度 = 基准/半径因子，卷多转慢）
#   _is_cassette(): 当前物品是否 rect 形态
#   paintEvent: 按 shape 分派（circle → _paint_record，rect → _paint_cassette）+ 效果器叠加
#   _paint_record: 径向渐变圆盘 + 4 圈槽纹 + 中心封面圆（QPainterPath 圆形裁剪）
#   _paint_cassette: 圆角渐变壳 + 半透明上窗（内绘卷轴）+ 底部封面标签
#   _paint_reels: 双卷带圆（胀缩 + 缠绕纹理）+ 花键 hub 3 齿 + 走带路径
#   pixmap_image(): grab 渲染结果（验证用）
#   设计理由：绘制纯 QPainter，质感来自渐变/阴影；封面经 resolve_cover 兜底；
#     动画定时器仅由 set_playing(True) 启动（置物架卡片保持静态，无批量 tick 开销）
#   关联配置：ItemType.shape（item_types.json）、封面服务（modules/cover）、
#     ui.json spin_tick_ms（动画帧间隔）
