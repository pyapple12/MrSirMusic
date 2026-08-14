# 唱机视图（A11.5/B0.14）：拟物控件接入（RecordWidget 封面形态 + DeckWidget 转盘 + ProgressWidget 进度）
# 桥信号驱动 UI 更新；状态字段驱动播放/暂停分发（B0.11）；拖放三事件完整（B0.13）

from pathlib import Path

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import QHBoxLayout, QLabel, QPushButton, QVBoxLayout, QWidget

from modules.cover.providers import resolve_cover
from modules.items.model import Item
from config.static.static_config import get_static_config
from ui.bridge.event_bridge import EventBridge
from ui.dnd import decode_item_id, is_item_drag
from ui.widgets.deck_widget import DeckWidget
from ui.widgets.progress_widget import ProgressWidget
from ui.widgets.record_widget import RecordWidget

# 静态配置一次解包（拟物控件尺寸走 ui.json，B2.8）
_SC = get_static_config()


class DeckView(QWidget):
    # 唱机视图：拟物绘制区（物品形态 + 转盘）+ 播放控制 + 进度；桥信号驱动；接受物品拖放
    play_clicked = Signal()
    pause_clicked = Signal()
    next_clicked = Signal()
    prev_clicked = Signal()
    flip_clicked = Signal()
    item_dropped = Signal(str)

    def __init__(self, bridge: EventBridge, parent: QWidget | None = None) -> None:
        # 初始化：拟物控件布局 + 绑定桥信号（state/track/progress/side）+ 接受拖放
        super().__init__(parent)
        self._bridge = bridge
        self._item: Item | None = None
        self._playing = False
        self.setAcceptDrops(True)

        self.record_widget = RecordWidget()
        self.record_widget.setFixedSize(
            int(_SC.ui.get("record_widget_size", 200)),
            int(_SC.ui.get("record_widget_size", 200)),
        )
        self.deck_widget = DeckWidget()
        self.deck_widget.setFixedSize(
            int(_SC.ui.get("deck_widget_size", 220)),
            int(_SC.ui.get("deck_widget_size", 220)),
        )

        self.track_label = QLabel("未载入物品")
        self.track_label.setWordWrap(True)

        self.play_button = QPushButton("播放")
        self.prev_button = QPushButton("上一首")
        self.next_button = QPushButton("下一首")
        self.flip_button = QPushButton("A 面")
        self.flip_button.setCheckable(True)

        self.progress_widget = ProgressWidget()
        self.progress_bar = self.progress_widget.bar  # 兼容别名（进度条实例）

        art_row = QHBoxLayout()
        art_row.addWidget(self.record_widget)
        art_row.addWidget(self.deck_widget)
        art_row.addStretch(1)

        controls = QHBoxLayout()
        controls.addWidget(self.prev_button)
        controls.addWidget(self.play_button)
        controls.addWidget(self.next_button)
        controls.addWidget(self.flip_button)

        layout = QVBoxLayout(self)
        layout.addLayout(art_row)
        layout.addWidget(self.track_label)
        layout.addLayout(controls)
        layout.addWidget(self.progress_widget)

        self.play_button.clicked.connect(self._on_play_clicked)
        self.prev_button.clicked.connect(self.prev_clicked.emit)
        self.next_button.clicked.connect(self.next_clicked.emit)
        self.flip_button.clicked.connect(self.flip_clicked.emit)

        bridge.signals.state_changed.connect(self._on_state)
        bridge.signals.track_changed.connect(self._on_track)
        bridge.signals.progress.connect(self._on_progress)
        bridge.signals.side_flipped.connect(self._on_side)

    def load_item(self, item: Item) -> None:
        # 载入物品：形态/封面（RecordWidget 全量重绘，无封面不残留旧图）+ 面按钮 + 首曲标题
        self._item = item
        self.record_widget.set_item(item)
        labels = "/".join(item.type.sides)
        self.flip_button.setText(f"{labels} 面")
        self.flip_button.setChecked(False)
        self.flip_button.setEnabled(
            len(item.type.sides) > 1
        )  # E0.4：单面（CD）翻面无意义
        first = item.side_for(item.type.sides[0]) if item.type.sides else None
        if first is not None and first.tracks:
            self.track_label.setText(
                f"{first.tracks[0].title}\n{first.tracks[0].artist or '未知艺人'}"
            )
        else:
            self.track_label.setText("（空物品）")

    def _on_play_clicked(self) -> None:
        # 播放按钮：按显式状态字段分发（B0.11，不依赖按钮文本回读）
        if self._playing:
            self.pause_clicked.emit()
        else:
            self.play_clicked.emit()

    def _on_state(self, state: str) -> None:
        # 桥 state_changed → 状态字段 + 按钮文本 + 转盘动画联动（B0.14）
        self._playing = state == "playing"
        self.play_button.setText("暂停" if self._playing else "播放")
        self.deck_widget.set_playing(self._playing)

    def _on_track(self, payload) -> None:
        # 桥 track_changed → 曲目标签 + 翻面按钮态同步（E0.4：A 面复位/B 面禁用）
        track = getattr(payload, "track", None)
        if track is not None:
            self.track_label.setText(f"{track.title}\n{track.artist or '未知艺人'}")
        else:
            self.track_label.setText("未载入物品")
        side = getattr(payload, "side", None)
        if side == "A":
            self.flip_button.setText("A 面")
            self.flip_button.setChecked(False)
            self.flip_button.setEnabled(True)
        elif side == "B":
            self.flip_button.setText("B 面")
            self.flip_button.setChecked(True)
            self.flip_button.setEnabled(False)

    def _on_progress(self, position_ms: int, duration_ms: int) -> None:
        # 桥 progress → ProgressWidget（百分比 + mm:ss 时间，B0.14）
        self.progress_widget.on_progress(position_ms, duration_ms)

    def _on_side(self, side: str) -> None:
        # 桥 side_flipped → 翻面按钮显示当前面
        self.flip_button.setText(f"{side} 面")
        self.flip_button.setChecked(True)

    def dragEnterEvent(self, event) -> None:
        # 拖入：物品 mime 才接受（其他忽略）
        if is_item_drag(event.mimeData()):
            event.acceptProposedAction()

    def dragMoveEvent(self, event) -> None:
        # 拖动中持续接受（B0.13：防部分平台拖放中断）
        if is_item_drag(event.mimeData()):
            event.acceptProposedAction()

    def dropEvent(self, event) -> None:
        # 放下：解析物品 id → item_dropped 信号（交 main_window 路由播放）
        item_id = decode_item_id(event.mimeData())
        if item_id is not None:
            self.item_dropped.emit(item_id)
            event.acceptProposedAction()


# ===== ui/views/deck_view.py 类/函数说明 =====
# DeckView(QWidget): 唱机视图（B0.14 拟物控件接入）
#   record_widget: 物品形态/封面绘制（set_item + 档位效果器叠加）
#   deck_widget: 转盘/唱针动画（set_playing 联动，set_animations_enabled 随档位）
#   progress_widget: 进度条 + mm:ss（on_progress；progress_bar 为兼容别名）
#   load_item(item): 形态/面按钮/首曲标题（RecordWidget 全量重绘，B0.8 无旧封面残留）
#   _on_play_clicked: 按 _playing 状态字段分发（B0.11）
#   _on_state: 状态字段 + 按钮文本 + deck_widget.set_playing（B0.14）
#   _on_track/_on_progress/_on_side: 桥信号驱动（progress 走 ProgressWidget）
#   dragEnterEvent/dragMoveEvent/dropEvent: 物品拖放三事件（B0.13）
#   信号：play/pause/next/prev/flip/item_dropped（交 main_window 路由）
#   关联配置：封面服务（resolve_cover）、事件桥（ui/bridge）、拟物控件（ui/widgets）
