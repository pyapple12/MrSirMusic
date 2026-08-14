# 主窗口（A11.2/A14.1）：三视图容器 + 菜单栏 + 状态栏；播放路由/导入/启动加载（A14 集成）

from PySide6.QtWidgets import (
    QMainWindow,
    QSplitter,
    QStatusBar,
    QTabWidget,
    QMenuBar,
    QLabel,
    QInputDialog,
)

from config.settings import add_change_listener, load_config
from config.static.static_config import get_static_config
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

        self._items: list[Item] = []
        self.bridge = EventBridge()
        self.engine = PlaybackEngine()
        self.reporter = ProgressReporter(self.engine)
        self.reporter.start()

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
        # 播放路由：唱机按钮 → 引擎；三视图选择/拖放 → _play_item；右键编辑/刻录/删除 → 业务（B0.6）
        self.deck_view.play_clicked.connect(self.engine.play)
        self.deck_view.pause_clicked.connect(self.engine.pause)
        self.deck_view.next_clicked.connect(self.engine.play_next)
        self.deck_view.prev_clicked.connect(self.engine.play_prev)
        self.deck_view.flip_clicked.connect(self.engine.flip)
        self.library_view.play_requested.connect(self._play_item)
        self.library_view.edit_requested.connect(self._edit_item)
        self.library_view.regenerate_requested.connect(self._regenerate_item)
        self.library_view.delete_requested.connect(self._delete_item)
        self.shelf_view.item_clicked.connect(self._play_item)
        self.deck_view.item_dropped.connect(self._play_item)
        self.bridge.signals.state_changed.connect(self._on_state_changed)
        self.bridge.signals.error.connect(self._on_error)

    def _apply_realism(self, level: str) -> None:
        # 应用拟真度档位到唱机控件（效果器叠加 + 动画开关；B0.4 档位接线）
        apply_effects_level(self.deck_view.record_widget, level)
        self.deck_view.deck_widget.set_animations_enabled(animations_enabled(level))

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
        # 重新刻录：复用原歌池生成新 id 物品 → 刷新（E3.1 顶层 import）
        item = next((i for i in self._items if i.id == item_id), None)
        if item is None:
            return
        regenerate_item(item)
        self.refresh_library(load_all())

    def _delete_item(self, item_id: str) -> None:
        # 删除物品（库级联 + 封面引用检查）→ 刷新（E3.1 顶层 import）
        item = next((i for i in self._items if i.id == item_id), None)
        if item is None:
            return
        delete_item(item)
        self.refresh_library(load_all())

    def _play_item(self, item_id: str) -> None:
        # 播放指定物品：加载到唱机视图 → 引擎 load + play（缺失曲目播放时引擎发 ERROR）
        item = next((i for i in self._items if i.id == item_id), None)
        if item is None:
            return
        self.deck_view.load_item(item)
        self.engine.load_item(item)
        self.engine.play()

    def _on_state_changed(self, state: str) -> None:
        # 播放状态 → 状态栏（playing/paused/stopped）
        labels = {
            "playing": "播放中",
            "paused": "已暂停",
            "stopped": "已停止",
            "ended": "播放结束",
        }
        self.state_label.setText(labels.get(state, state))

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
        # 关闭清理：停上报器 + 退订桥（防悬挂回调）
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
#   _play_item(id): 三视图选择与拖放统一入口（load_item + play）
#   _on_state_changed/_on_error: 状态栏更新（错误提示不崩溃，A14.3）
#   _open_import/_open_settings: 导入对话框（生成后刷新）/设置面板
#   refresh_library(items|None): 数据注入（默认重载 + mark_missing）
#   closeEvent: reporter.shutdown + bridge.shutdown（生命周期）
#   关联配置：base.json/ui.json；引擎（A9）、桥（A10）、导入（A11）、设置（A13）
