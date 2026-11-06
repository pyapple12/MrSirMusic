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
from utils.convert import ms_from_seconds

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
    seek_requested = Signal(int)  # H5：进度滑条 scrub 松手（目标曲内秒数）
    seek_side_requested = Signal(float)  # H4：唱针落针（面内比例 0-1，跨曲由引擎定位）

    def __init__(self, bridge: EventBridge, parent: QWidget | None = None) -> None:
        # 初始化：拟物控件布局 + 绑定桥信号（state/track/progress/side）+ 接受拖放
        super().__init__(parent)
        self._bridge = bridge
        self._item: Item | None = None
        self._playing = False
        # H4/H5 寻曲状态：面内偏移/总时长（TRACK_CHANGED 附带）、最近曲时长、scrub 方向基准
        self._side_offset: float | None = None
        self._side_total: float | None = None
        self._last_duration_ms = 0
        self._scrub_last_value = 0
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
        self.track_label.setAlignment(Qt.AlignmentFlag.AlignHCenter)  # PL001.3：随居中构图

        self.play_button = QPushButton("播放")
        self.prev_button = QPushButton("上一首")
        self.next_button = QPushButton("下一首")
        self.flip_button = QPushButton("A 面")
        self.flip_button.setCheckable(True)
        # PL003.5：播放控制按钮不参与焦点链（空格快捷键不会落在聚焦按钮上双触发）
        for button in (
            self.play_button,
            self.prev_button,
            self.next_button,
            self.flip_button,
        ):
            button.setFocusPolicy(Qt.FocusPolicy.NoFocus)

        self.progress_widget = ProgressWidget()
        self.progress_bar = self.progress_widget.bar  # 兼容别名（进度条实例）
        # PL001.3：滑条区限宽居中（不再全宽拉伸）
        self.progress_widget.setMaximumWidth(420)

        # PL001.3：拟物控件组水平居中（两侧对称留白 = 有意呼吸，替代原左对齐 + 右侧大片空洞）
        art_row = QHBoxLayout()
        art_row.addStretch(1)
        art_row.addWidget(self.record_widget)
        art_row.addSpacing(16)
        art_row.addWidget(self.deck_widget)
        art_row.addStretch(1)

        # PL001.3：按钮固定宽居中成排（替代原全宽拉伸巨条）
        for button in (
            self.prev_button,
            self.play_button,
            self.next_button,
            self.flip_button,
        ):
            button.setFixedWidth(96)
        controls = QHBoxLayout()
        controls.setSpacing(12)
        controls.addStretch(1)
        controls.addWidget(self.prev_button)
        controls.addWidget(self.play_button)
        controls.addWidget(self.next_button)
        controls.addWidget(self.flip_button)
        controls.addStretch(1)

        # PL001.3：滑条行与按钮行同宽居中（时间标签随行）
        progress_row = QHBoxLayout()
        progress_row.addStretch(1)
        progress_row.addWidget(self.progress_widget)
        progress_row.addStretch(1)

        layout = QVBoxLayout(self)
        layout.addSpacing(8)
        layout.addLayout(art_row)
        layout.addSpacing(16)
        layout.addWidget(self.track_label)
        layout.addSpacing(12)
        layout.addLayout(controls)
        layout.addSpacing(8)
        layout.addLayout(progress_row)

        self.play_button.clicked.connect(self._on_play_clicked)
        self.prev_button.clicked.connect(self.prev_clicked.emit)
        self.next_button.clicked.connect(self.next_clicked.emit)
        self.flip_button.clicked.connect(self.flip_clicked.emit)

        # H4/H5 拟物交互接线：拖针 → 暂停；落针 → 面内寻曲；scrub 三态 → seek + 磁带 wind
        self.deck_widget.needle_drag_started.connect(self.pause_clicked.emit)
        self.deck_widget.needle_dropped.connect(self.seek_side_requested.emit)
        self.progress_widget.scrub_started.connect(self._on_scrub_started)
        self.progress_widget.scrub_moved.connect(self._on_scrub_moved)
        self.progress_widget.scrub_released.connect(self._on_scrub_released)

        bridge.signals.state_changed.connect(self._on_state)
        bridge.signals.track_changed.connect(self._on_track)
        bridge.signals.progress.connect(self._on_progress)
        bridge.signals.side_flipped.connect(self._on_side)

    def load_item(self, item: Item) -> None:
        # 载入物品：形态/封面（RecordWidget 全量重绘，无封面不残留旧图）+ 面按钮 + 首曲标题；
        # H2 类型级转速注入 + H4 面内寻曲状态复位 + PL002 唱机形态/封面切换
        self._item = item
        self.record_widget.set_item(item)
        self.deck_widget.set_spin_ms(item.type.spin_ms_per_rev)
        cover_pixmap: QPixmap | None = None
        cover = resolve_cover(item)
        if cover and Path(cover).is_file():
            pixmap = QPixmap(cover)
            if not pixmap.isNull():
                cover_pixmap = pixmap
        self.deck_widget.set_item_type(item.type.key, cover_pixmap)
        self._side_offset = None
        self._side_total = None
        self._last_duration_ms = 0
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

    def toggle_play(self) -> None:
        # 公开播放/暂停切换入口（FIX006.16：快捷键等外部调用方走此公开方法，不触私有）
        self._on_play_clicked()

    def _on_play_clicked(self) -> None:
        # 播放按钮：按显式状态字段分发（B0.11，不依赖按钮文本回读）
        if self._playing:
            self.pause_clicked.emit()
        else:
            self.play_clicked.emit()

    def _on_state(self, state: str) -> None:
        # 桥 state_changed → 状态字段 + 按钮文本 + 转盘动画联动（B0.14）+ 磁带卷轴联动（H6）
        self._playing = state == "playing"
        self.play_button.setText("暂停" if self._playing else "播放")
        self.deck_widget.set_playing(self._playing)
        self.record_widget.set_playing(self._playing)

    def _on_track(self, payload) -> None:
        # 桥 track_changed → 曲目标签 + 翻面按钮态同步（E0.4：A 面复位/B 面禁用）；
        # H4 记录面内偏移/总时长（唱针映射源）并即时同步唱针/卷轴位置
        track = getattr(payload, "track", None)
        if track is not None:
            self.track_label.setText(f"{track.title}\n{track.artist or '未知艺人'}")
            self._last_duration_ms = ms_from_seconds(
                float(getattr(track, "duration_seconds", 0.0) or 0.0)
            )
        else:
            self.track_label.setText("未载入物品")
        offset = getattr(payload, "side_offset_seconds", None)
        total = getattr(payload, "side_total_seconds", None)
        self._side_offset = float(offset) if isinstance(offset, (int, float)) else None
        self._side_total = float(total) if isinstance(total, (int, float)) else None
        self.deck_widget.set_progress(self._side_fraction(0))
        self.record_widget.set_reel_progress(self._side_fraction(0))
        side = getattr(payload, "side", None)
        if side == "A":
            self.flip_button.setText("A 面")
            self.flip_button.setChecked(False)
            # F0.4：单面载体（CD）保持禁用（load_item 语义不被覆盖）
            self.flip_button.setEnabled(len(self._item.type.sides) > 1)
        elif side == "B":
            self.flip_button.setText("B 面")
            self.flip_button.setChecked(True)
            self.flip_button.setEnabled(False)

    def _on_progress(self, position_ms: int, duration_ms: int) -> None:
        # 桥 progress → ProgressWidget（百分比 + mm:ss 时间，B0.14）；
        # H4/H6 唱针面内进度 + 磁带卷轴进度联动（面内时长可用时用面内比例，否则退单曲比例）
        self.progress_widget.on_progress(position_ms, duration_ms)
        if duration_ms > 0:
            self._last_duration_ms = duration_ms
        fraction = self._side_fraction(position_ms / 1000.0)
        self.deck_widget.set_progress(fraction)
        self.record_widget.set_reel_progress(fraction)

    def _side_fraction(self, position_seconds: float) -> float:
        # 面内比例换算（H4）：(面内偏移 + 当前曲内秒) / 面总时长；
        # 面时长缺失（降级链）→ 退化为当前曲目内比例（对负值钳 0）
        if (
            self._side_offset is not None
            and self._side_total is not None
            and self._side_total > 0
        ):
            return min(1.0, max(0.0, (self._side_offset + position_seconds) / self._side_total))
        if self._last_duration_ms > 0:
            return min(1.0, max(0.0, position_seconds / (self._last_duration_ms / 1000.0)))
        return 0.0

    def _on_scrub_started(self) -> None:
        # 滑条按下（H5）：记录方向判定基准（磁带 wind 用）
        self._scrub_last_value = self.progress_widget.bar.value()

    def _on_scrub_moved(self, value: int) -> None:
        # 滑条拖动（H5）：磁带卷轴 wind 视觉按拖动方向（快进/倒带）
        delta = value - self._scrub_last_value
        if delta != 0:
            self.record_widget.set_wind(1.0 if delta > 0 else -1.0)
            self._scrub_last_value = value

    def _on_scrub_released(self, value: int) -> None:
        # 滑条松手（H5）：滑条值（0-1000）换算曲内秒数 → seek_requested；wind 复位
        self.record_widget.set_wind(0.0)
        seconds = int(self._last_duration_ms / 1000.0 * value / 1000.0)
        self.seek_requested.emit(max(0, seconds))

    def _on_side(self, side: str) -> None:
        # 桥 side_flipped → 翻面按钮显示当前面（F0.4：B 面禁用，与 _on_track 一致）
        self.flip_button.setText(f"{side} 面")
        self.flip_button.setChecked(True)
        self.flip_button.setEnabled(side == "A" and len(self._item.type.sides) > 1)

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
# DeckView(QWidget): 唱机视图（B0.14 拟物控件接入；H4-H6 拟物交互汇聚点）
#   record_widget: 物品形态/封面绘制（set_item + 档位效果器叠加 + 磁带卷轴动画联动）
#   deck_widget: 转盘/唱针动画（set_playing/set_progress/set_spin_ms；拖拽寻曲信号源）
#   progress_widget: 可拖动进度滑条 + mm:ss（on_progress；progress_bar 为兼容别名）
#   load_item(item): 形态/面按钮/首曲标题/类型级转速（RecordWidget 全量重绘，B0.8）
#   _on_play_clicked: 按 _playing 状态字段分发（B0.11）
#   _on_state: 状态字段 + 按钮文本 + deck/record 控件播放态联动（B0.14/H6）
#   _on_track: 曲目标签 + 面按钮态（E0.4）+ 面内偏移记录 + 唱针/卷轴位置同步（H4）
#   _on_progress: ProgressWidget + 唱针/卷轴面内比例联动（H4/H6）
#   _side_fraction(seconds): 面内比例换算（面时长缺失退单曲比例，宽容降级）
#   _on_scrub_started/moved/released: 滑条 scrub 三态（方向 → wind 视觉；松手 → seek_requested）
#   dragEnterEvent/dragMoveEvent/dropEvent: 物品拖放三事件（B0.13）
#   信号：play/pause/next/prev/flip/item_dropped（交 main_window 路由）；
#     seek_requested(int 曲内秒)/seek_side_requested(float 面内比例)（H4/H5 寻曲出口）
#   关联配置：封面服务（resolve_cover）、事件桥（ui/bridge）、拟物控件（ui/widgets）
