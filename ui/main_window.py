# 主窗口（A11.2/A14.1）：三视图容器 + 菜单栏 + 状态栏；播放路由/导入/启动加载（A14 集成）

from PySide6.QtGui import QKeySequence, QShortcut
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QMainWindow,
    QSplitter,
    QStatusBar,
    QTabWidget,
    QMenuBar,
    QLabel,
    QInputDialog,
    QMessageBox,
)

from config.settings import add_change_listener, load_config
from config.static.static_config import get_static_config
from modules.generator.generator import GenerateError
from modules.items.model import Item
from modules.library.path_check import mark_missing
from modules.library.repository import load_all
from modules.generator.delete import delete as delete_item
from modules.generator.edit import rename_item
from modules.generator.regenerate import regenerate as regenerate_item
from modules.playback.engine import PlaybackEngine
from modules.playback.progress import ProgressReporter
from ui.bridge.event_bridge import EventBridge
from ui.effects.registry import animations_enabled, apply as apply_effects_level
from ui.import_dialog import ImportDialog
from ui.settings_dialog import SettingsDialog
from ui.sounds import SoundKit
from ui.views.deck_view import DeckView
from ui.views.library_view import LibraryView
from ui.views.shelf_view import ShelfView

# 静态配置一次解包
_SC = get_static_config()


class MainWindow(QMainWindow):
    # 主窗口：左（物品库/置物架页签）+ 右（唱机）；菜单栏；状态栏；播放路由与数据加载

    def __init__(self) -> None:
        # 初始化：窗口/桥/引擎/上报器 → 三视图 → 菜单 → 状态栏 → 播放路由 → 启动加载
        super().__init__()
        base = _SC.base
        ui = _SC.ui
        self.setWindowTitle(
            f"{base.get('app_name', 'MrSirMusic')} {base.get('version', '')}"
        )
        self.resize(
            int(ui.get("window_width", 1100)), int(ui.get("window_height", 720))
        )
        # PL001.5：最小窗口约束（拟物控件 200+220 固定宽 + 列表可读下限，窄于此布局挤坏）
        self.setMinimumSize(980, 640)

        self._items: list[Item] = []
        self._current_item: Item | None = None  # H3 音效门控（载体类型/落针音判定源）
        self._last_state = "stopped"  # H3 落针音判定（非播放态→播放态的迁移沿）
        self.bridge = EventBridge()
        self.engine = PlaybackEngine()
        self.reporter = ProgressReporter(self.engine)
        self.reporter.start()
        self.sound_kit = SoundKit(self)  # H3 拟物音效（fail-soft，无声卡自动禁用）

        self.library_view = LibraryView()
        self.shelf_view = ShelfView()
        self.deck_view = DeckView(self.bridge)

        tabs = QTabWidget()
        tabs.addTab(self.library_view, "物品库")
        tabs.addTab(self.shelf_view, "置物架")

        splitter = QSplitter()
        splitter.addWidget(tabs)
        splitter.addWidget(self.deck_view)
        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 1)
        self.setCentralWidget(splitter)

        self._build_menu_bar()
        self._build_status_bar()
        self._wire_playback()
        add_change_listener(self._on_settings_changed)
        self._apply_realism(load_config().realism_level)
        self.refresh_library(load_all())
        # PL004.1：初始焦点显式落物品库列表（主内容件优先——缺省首焦点会被 QTabBar 捕获）
        self.library_view.list.setFocus()

    def _build_menu_bar(self) -> None:
        # 菜单栏：文件（导入/生成、退出）、视图、设置（设置面板 A13.4）
        menu_bar = self.menuBar()
        file_menu = menu_bar.addMenu("文件")
        import_action = file_menu.addAction("导入/生成物品…")
        import_action.triggered.connect(self._open_import)
        file_menu.addSeparator()
        exit_action = file_menu.addAction("退出")
        exit_action.triggered.connect(self.close)
        settings_menu = menu_bar.addMenu("设置")
        settings_action = settings_menu.addAction("设置…")
        settings_action.triggered.connect(self._open_settings)

    def _build_status_bar(self) -> None:
        # 状态栏（E0.5 双 label）：左侧版本，右侧消息（错误提示，不被状态覆盖）+ 播放状态
        version_label = QLabel(f"版本 {_SC.base.get('version', '')}")
        self.message_label = QLabel("")
        self.state_label = QLabel("未播放")
        status = self.statusBar()
        status.addWidget(version_label)
        status.addPermanentWidget(self.message_label)
        status.addPermanentWidget(self.state_label)

    def _wire_playback(self) -> None:
        # 播放路由：唱机按钮 → 引擎；三视图选择/拖放 → _play_item；右键编辑/刻录/删除 → 业务（B0.6）；
        # H4/H5 寻曲路由（滑条 seek 秒数 / 唱针 seek_side 面内比例）+ H3 音效事件订阅
        self.deck_view.play_clicked.connect(self.engine.play)
        self.deck_view.pause_clicked.connect(self.engine.pause)
        self.deck_view.next_clicked.connect(self.engine.play_next)
        self.deck_view.prev_clicked.connect(self.engine.play_prev)
        self.deck_view.flip_clicked.connect(self.engine.flip)
        self.deck_view.seek_requested.connect(self._on_seek)
        self.deck_view.seek_side_requested.connect(self._on_seek_side)
        self.library_view.play_requested.connect(self._play_item)
        self.library_view.edit_requested.connect(self._edit_item)
        self.library_view.regenerate_requested.connect(self._regenerate_item)
        self.library_view.delete_requested.connect(self._delete_item)
        self.shelf_view.item_clicked.connect(self._play_item)
        self.deck_view.item_dropped.connect(self._play_item)
        self.bridge.signals.state_changed.connect(self._on_state_changed)
        self.bridge.signals.track_changed.connect(self._on_track_changed)
        self.bridge.signals.side_flipped.connect(self._on_side_flipped)
        self.bridge.signals.error.connect(self._on_error)
        self._wire_shortcuts()

    def _wire_shortcuts(self) -> None:
        # 桌面快捷键（PL003.5）：空格=播放/暂停、←/→=上下曲、F=翻面（窗口级）；
        # 播放控制按钮已在 deck_view 设 NoFocus——防空格落在聚焦按钮上双触发
        specs = (
            (Qt.Key.Key_Space, self._on_shortcut_play_pause),
            (Qt.Key.Key_Left, self.engine.play_prev),
            (Qt.Key.Key_Right, self.engine.play_next),
            (Qt.Key.Key_F, self.engine.flip),
        )
        self._shortcuts = []
        for key, slot in specs:
            shortcut = QShortcut(QKeySequence(key), self)
            shortcut.setContext(Qt.ShortcutContext.WindowShortcut)
            shortcut.activated.connect(slot)
            self._shortcuts.append(shortcut)

    def _on_shortcut_play_pause(self) -> None:
        # 空格：按唱机视图当前态分发（与播放按钮同路由语义，B0.11 状态字段分发）；
        # FIX006.16：走公开 toggle_play（不跨类调私有方法）
        self.deck_view.toggle_play()

    def _apply_realism(self, level: str) -> None:
        # 应用拟真度档位到唱机控件（效果器叠加 + 动画开关；B0.4 档位接线）+ 音效响度（H3）
        apply_effects_level(self.deck_view.record_widget, level)
        self.deck_view.deck_widget.set_animations_enabled(animations_enabled(level))
        self.sound_kit.set_level(level)

    def _on_settings_changed(self, cfg) -> None:
        # 设置变更实时应用档位（settings 变更回调）
        self._apply_realism(cfg.realism_level)

    def _edit_item(self, item_id: str) -> None:
        # 编辑物品（第一版：改名对话框 → rename_item → 刷新；E3.1 顶层 import）
        item = next((i for i in self._items if i.id == item_id), None)
        if item is None:
            return
        name, ok = QInputDialog.getText(self, "编辑物品", "新名称：", text=item.name)
        if ok and name.strip():
            rename_item(item, name.strip())
            self.refresh_library(load_all())

    def _regenerate_item(self, item_id: str) -> None:
        # 重新刻录：复用原歌池生成新 id 物品 → 刷新（E3.1 顶层 import）；
        # FIX006.1 配套：GenerateError（容量不足丢弃/校验未通过）→ 分类提示不炸槽
        item = next((i for i in self._items if i.id == item_id), None)
        if item is None:
            return
        try:
            regenerate_item(item)
        except GenerateError as exc:
            QMessageBox.warning(self, "重新刻录", str(exc))
            return
        self.refresh_library(load_all())

    def _delete_item(self, item_id: str) -> None:
        # 删除物品（库级联 + 封面引用检查）→ 刷新（E3.1 顶层 import）
        item = next((i for i in self._items if i.id == item_id), None)
        if item is None:
            return
        delete_item(item)
        self.refresh_library(load_all())

    def _play_item(self, item_id: str) -> None:
        # 播放指定物品：清除错误提示（G3.2）→ 加载到唱机视图 → 引擎 load + play（缺失曲目播放时引擎发 ERROR）；
        # H3 记录当前物品 + 音效载体类型切换（黑胶底噪/磁带机械声的门控源）
        item = next((i for i in self._items if i.id == item_id), None)
        if item is None:
            return
        self._current_item = item
        self.sound_kit.set_media_kind(item.type.key)
        self.message_label.clear()
        self.deck_view.load_item(item)
        self.engine.load_item(item)
        self.engine.play()

    def _on_seek(self, seconds: int) -> None:
        # 滑条 scrub 松手（H5）：目标曲内秒数 → 引擎 seek
        self.engine.seek(float(max(0, seconds)))

    def _on_seek_side(self, fraction: float) -> None:
        # 唱针落针（H4）：面内比例 → 引擎面内寻曲（同曲 seek / 跨曲换曲）
        self.engine.seek_side(float(fraction))

    def _on_track_changed(self, payload) -> None:
        # 曲目切换（H3）：播放中且载体是磁带 → 换曲机械声（黑胶走底噪/落针音，CD 数字静音）
        if (
            self.engine.state == "playing"
            and self._current_item is not None
            and self._current_item.type.key == "cassette"
        ):
            self.sound_kit.play_tape_mech()

    def _on_side_flipped(self, side: str) -> None:
        # 翻面（H3）：黑胶翻面 = 提针→翻盘→落针 → 播放落针刮擦音
        if self._current_item is not None and self._current_item.type.key == "vinyl":
            self.sound_kit.play_needle_drop()

    def _on_state_changed(self, state: str) -> None:
        # 播放状态 → 状态栏（playing/paused/stopped）；H3 音效联动
        labels = {
            "playing": "播放中",
            "paused": "已暂停",
            "stopped": "已停止",
            "ended": "播放结束",
        }
        self.state_label.setText(labels.get(state, state))
        self._apply_state_sounds(state)

    def _apply_state_sounds(self, state: str) -> None:
        # H3 播放态音效联动：底噪随播放态启停（黑胶由 SoundKit 内部按载体门控）；
        # 落针音仅在"非播放态 → 播放态"迁移沿播放（切歌时唱针不离盘，不出刮擦声）
        if state == "playing":
            self.sound_kit.set_active(True)
            if self._last_state != "playing" and self._is_vinyl():
                self.sound_kit.play_needle_drop()
        else:
            self.sound_kit.set_active(False)
        self._last_state = state

    def _is_vinyl(self) -> bool:
        # 当前物品是否黑胶（音效门控：底噪/落针音仅黑胶；CD 数字静音、磁带走机械声）
        return self._current_item is not None and self._current_item.type.key == "vinyl"

    def _on_error(self, category: str, message: str) -> None:
        # 播放错误 → 消息 label 提示（E0.5：独立于状态 label，不被后续状态更新覆盖）
        self.message_label.setText(f"提示：{message}")

    def _open_import(self) -> None:
        # 打开导入对话框：生成成功 → 刷新物品库/置物架
        dialog = ImportDialog(self)
        if dialog.exec():
            self.refresh_library(load_all())

    def _open_settings(self) -> None:
        # 打开设置面板（档位/自动翻面；保存走 settings.save_config + 变更通知）
        SettingsDialog(self).exec()

    def refresh_library(self, items: list[Item] | None = None) -> None:
        # 刷新物品库与置物架视图：默认重载库并标记缺失文件（不阻塞）
        if items is None:
            items = load_all()
        for item in items:
            mark_missing(item)
        self._items = items
        self.library_view.set_items(items)
        self.shelf_view.set_items(items)

    def closeEvent(self, event) -> None:
        # 关闭清理：停引擎（H0.3：关闭瞬间音频仍在路由，先停保证即时静音）+ 停上报器 + 退订桥
        self.engine.stop()
        self.reporter.shutdown()
        self.bridge.shutdown()
        super().closeEvent(event)


# ===== ui/main_window.py 类/函数说明 =====
# _SC: 静态配置单例（窗口尺寸/标题/版本）
# MainWindow(QMainWindow): 主窗口
#   __init__: 桥/引擎/上报器 → 三视图 → 菜单/状态栏 → 播放路由 → 启动加载（load_all + mark_missing）
#   _build_menu_bar: 文件（导入/生成、退出）/视图/设置（SettingsDialog A13.4）
#   _build_status_bar: 版本 + 播放状态标签
#   _wire_playback: 按钮/右键/拖放 → 引擎；桥 state/error → 状态栏
#   _play_item(id): 三视图选择与拖放统一入口（load_item + play + 音效载体切换 H3）
#   _on_seek(seconds): 滑条 scrub 松手 → 引擎 seek（H5）
#   _on_seek_side(fraction): 唱针落针 → 引擎面内寻曲（H4）
#   _on_track_changed(payload): 播放中磁带换曲 → 机械声（H3）
#   _on_side_flipped(side): 黑胶翻面 → 落针刮擦音（H3）
#   _on_state_changed/_apply_state_sounds/_is_vinyl: 状态栏 + 音效联动（底噪启停/落针迁移沿，H3）
#   _on_error: 状态栏错误提示（错误提示不崩溃，A14.3/E0.5）
#   _open_import/_open_settings: 导入对话框（生成后刷新）/设置面板
#   refresh_library(items|None): 数据注入（默认重载 + mark_missing）
#   closeEvent: engine.stop（H0.3）+ reporter.shutdown + bridge.shutdown（生命周期）
#   关联配置：base.json/ui.json/effects.json；引擎（A9）、桥（A10）、导入（A11）、设置（A13）、音效（ui/sounds.py）
