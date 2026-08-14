# 唱机绘制（A12.2）：转盘旋转（QTimer + QPainter）+ 唱针落下/抬起（插值动画），时长读 ui.json

from PySide6.QtCore import QRectF, QTimer
from PySide6.QtGui import QColor, QPainter, QPen, QRadialGradient
from PySide6.QtWidgets import QWidget

from config.static.static_config import get_static_config
from modules.items.model import Item

# 静态配置一次解包
_SC = get_static_config()


class DeckWidget(QWidget):
    # 唱机绘制控件：转盘按播放态旋转（record_spin_ms/圈），唱针按目标位置插值（tonearm_drop_ms）

    def __init__(self, item: Item | None = None, parent: QWidget | None = None) -> None:
        # 初始化：角度/唱针状态；30ms 定时器驱动动画；时长读 ui.json；动画开关默认开
        super().__init__(parent)
        self._item = item
        self._playing = False
        self._angle = 0.0
        self._tonearm_pos = 0.0  # 0=抬起 1=落下
        self._animations_enabled = True
        ui = _SC.ui
        anim = ui.get("animation", {}) if isinstance(ui, dict) else {}
        self._spin_ms = int(anim.get("record_spin_ms", 2000))
        self._drop_ms = int(anim.get("tonearm_drop_ms", 500))
        self._tick_ms = int(ui.get("spin_tick_ms", 30))
        self.timer = QTimer(self)
        self.timer.setInterval(self._tick_ms)
        self.timer.timeout.connect(self._tick)

    def set_animations_enabled(self, enabled: bool) -> None:
        # 动画开关（A13.3 档位联动/C0.1）：关闭时停定时器 + 唱针瞬时落位；播放中重新启用时重启定时器
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

    def set_playing(self, playing: bool) -> None:
        # 播放态切换：播放 → 定时器启动（动画关时瞬时落针不转）；停止 → 定时器停止 + 唱针瞬时抬起
        self._playing = playing
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
        # 动画帧：动画开启且播放中角度按 spin_ms 推进；唱针向目标（播放 1/停止 0）插值逼近
        if self._playing and self._animations_enabled:
            self._angle = (self._angle + 360.0 * self._tick_ms / self._spin_ms) % 360.0
        target = 1.0 if self._playing else 0.0
        step = self._tick_ms / max(1, self._drop_ms)
        if self._tonearm_pos < target:
            self._tonearm_pos = min(target, self._tonearm_pos + step)
        elif self._tonearm_pos > target:
            self._tonearm_pos = max(target, self._tonearm_pos - step)
        self.update()

    def paintEvent(self, event) -> None:
        # 绘制：转盘（旋转画槽纹）+ 唱针（按位置旋转的针形）
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        rect = QRectF(self.rect()).adjusted(8, 8, -8, -8)
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
        # 唱针（右上方，按 tonearm_pos 旋转角度）
        painter.save()
        painter.translate(rect.center().x() + rect.width() * 0.35, rect.top())
        painter.rotate(20 + (1.0 - self._tonearm_pos) * 55)
        painter.setBrush(QColor("#c8c8c8"))
        painter.setPen(QPen(QColor("#666666"), 1))
        painter.drawRect(QRectF(-3, 0, 6, rect.height() * 0.45))
        painter.restore()
        painter.end()


# ===== ui/widgets/deck_widget.py 类/函数说明 =====
# _SC: 静态配置单例（动画时长）
# DeckWidget(QWidget): 唱机绘制（转盘旋转 + 唱针插值）
#   set_playing(playing): 定时器启停（播放驱动角度推进）
#   _tick(): 角度 += 360*tick/spin_ms；唱针位置向目标（1/0）按 drop_ms 步进插值
#   paintEvent: 转盘（rotate 后画同心圆）+ 唱针（按 tonearm_pos 旋转角度）
#   angle/tonearm_position: 状态只读（验证断言）
#   设计理由：动画时长全部来自 ui.json（AGENTS.md 参数外置）；QTimer 30ms 帧
#   关联配置：config/static/ui.json（animation.record_spin_ms/tonearm_drop_ms）
