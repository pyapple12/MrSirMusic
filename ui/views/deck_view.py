# 唱机视图（A11.5）：封面大图 + 播放控制 + 进度条 + 翻面按钮，绑定桥信号更新

from pathlib import Path

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QProgressBar,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from modules.cover.providers import resolve_cover
from modules.items.model import Item
from ui.bridge.event_bridge import EventBridge
from ui.dnd import decode_item_id, is_item_drag


class DeckView(QWidget):
    # 唱机视图：封面/曲名 + 播放/暂停/上下曲 + 进度条 + 翻面；桥信号驱动 UI 更新；接受物品拖放
    play_clicked = Signal()
    pause_clicked = Signal()
    next_clicked = Signal()
    prev_clicked = Signal()
    flip_clicked = Signal()
    item_dropped = Signal(str)

    def __init__(self, bridge: EventBridge, parent: QWidget | None = None) -> None:
        # 初始化：控件布局 + 绑定桥信号（state/track/progress/side）+ 接受拖放
        super().__init__(parent)
        self._bridge = bridge
        self._item: Item | None = None
        self.setAcceptDrops(True)

        self.cover_label = QLabel("无封面")
        self.cover_label.setFixedSize(200, 200)
        self.cover_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.track_label = QLabel("未载入物品")
        self.track_label.setWordWrap(True)

        self.play_button = QPushButton("播放")
        self.prev_button = QPushButton("上一首")
        self.next_button = QPushButton("下一首")
        self.flip_button = QPushButton("A 面")
        self.flip_button.setCheckable(True)

        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)

        controls = QHBoxLayout()
        controls.addWidget(self.prev_button)
        controls.addWidget(self.play_button)
        controls.addWidget(self.next_button)
        controls.addWidget(self.flip_button)

        layout = QVBoxLayout(self)
        layout.addWidget(self.cover_label)
        layout.addWidget(self.track_label)
        layout.addLayout(controls)
        layout.addWidget(self.progress_bar)

        self.play_button.clicked.connect(self._on_play_clicked)
        self.prev_button.clicked.connect(self.prev_clicked.emit)
        self.next_button.clicked.connect(self.next_clicked.emit)
        self.flip_button.clicked.connect(self.flip_clicked.emit)

        bridge.signals.state_changed.connect(self._on_state)
        bridge.signals.track_changed.connect(self._on_track)
        bridge.signals.progress.connect(self._on_progress)
        bridge.signals.side_flipped.connect(self._on_side)

    def load_item(self, item: Item) -> None:
        # 载入物品：更新封面与面按钮（随 ItemType.sides 显示 A/B）
        self._item = item
        cover = resolve_cover(item)
        if cover and Path(cover).is_file():
            pixmap = QPixmap(cover)
            if not pixmap.isNull():
                self.cover_label.setPixmap(
                    pixmap.scaled(200, 200, Qt.AspectRatioMode.KeepAspectRatio)
                )
        labels = "/".join(item.type.sides)
        self.flip_button.setText(f"{labels} 面")
        self.flip_button.setChecked(False)

    def _on_play_clicked(self) -> None:
        # 播放按钮：按当前文本分发（播放/暂停），发对应信号
        if self.play_button.text() == "播放":
            self.play_clicked.emit()
        else:
            self.pause_clicked.emit()

    def _on_state(self, state: str) -> None:
        # 桥 state_changed → 按钮文本与状态
        self.play_button.setText("暂停" if state == "playing" else "播放")

    def _on_track(self, payload) -> None:
        # 桥 track_changed → 曲目标签（payload.track 为项目模型或 None）
        track = getattr(payload, "track", None)
        if track is not None:
            self.track_label.setText(f"{track.title}\n{track.artist or '未知艺人'}")
        else:
            self.track_label.setText("未载入物品")

    def _on_progress(self, position_ms: int, duration_ms: int) -> None:
        # 桥 progress → 进度条百分比（总时长 0 时归零）
        if duration_ms > 0:
            self.progress_bar.setValue(int(position_ms * 100 / duration_ms))
        else:
            self.progress_bar.setValue(0)

    def _on_side(self, side: str) -> None:
        # 桥 side_flipped → 翻面按钮显示当前面
        self.flip_button.setText(f"{side} 面")
        self.flip_button.setChecked(True)

    def dragEnterEvent(self, event) -> None:
        # 拖入：物品 mime 才接受（其他忽略）
        if is_item_drag(event.mimeData()):
            event.acceptProposedAction()

    def dropEvent(self, event) -> None:
        # 放下：解析物品 id → item_dropped 信号（交 main_window 路由播放）
        item_id = decode_item_id(event.mimeData())
        if item_id is not None:
            self.item_dropped.emit(item_id)
            event.acceptProposedAction()


# ===== ui/views/deck_view.py 类/函数说明 =====
# DeckView(QWidget): 唱机视图（封面/曲名/控制/进度/翻面）
#   load_item(item): 封面 + 面按钮（sides 拼接如 "A/B 面"）
#   _on_play_clicked: 播放/暂停按文本分发（play/pause_clicked 信号）
#   _on_state/_on_track/_on_progress/_on_side: 桥信号驱动 UI（按钮文本/曲名/进度/翻面）
#   信号：play/pause/next/prev/flip_clicked（交 main_window 路由到引擎）
#   设计理由：视图只发信号不直接操作引擎；进度百分比换算（0-100）
#   关联配置：封面服务（resolve_cover 兜底）、事件桥（ui/bridge）
