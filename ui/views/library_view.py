# 物品库视图（A11.3）：物品列表（封面缩略 + 元信息）+ 选中详情面板 + 右键菜单

from pathlib import Path

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QAction, QPixmap
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QMenu,
    QVBoxLayout,
    QWidget,
)

from modules.cover.providers import resolve_cover
from modules.items.model import Item
from config.static.static_config import get_static_config
from ui.dnd import ITEM_MIME_TYPE, encode_item_id
from utils.convert import format_duration

# 静态配置一次解包（缩略图尺寸走 ui.json，B2.8）
_SC = get_static_config()


class _ItemList(QListWidget):
    # 物品列表：拖出时附加自定义 mime（物品 id，供唱机拖入解析）

    def mimeData(self, items):
        # 在默认 mime 基础上附加物品 id 自定义格式
        mime = super().mimeData(items)
        if items:
            item_id = items[0].data(Qt.ItemDataRole.UserRole)
            if item_id:
                mime.setData(ITEM_MIME_TYPE, encode_item_id(str(item_id)))
        return mime


class LibraryView(QWidget):
    # 物品库视图：左列表（封面缩略 + 名称/类型/Tag/播放次数）、右详情面板、右键菜单
    play_requested = Signal(str)
    edit_requested = Signal(str)
    regenerate_requested = Signal(str)
    delete_requested = Signal(str)

    def __init__(self, parent: QWidget | None = None) -> None:
        # 初始化：列表 + 详情面板布局；自定义右键菜单策略
        super().__init__(parent)
        self._items: list[Item] = []
        self.list = _ItemList()
        self.list.setDragEnabled(True)
        # PL001.5 配套：行内长文本裁切优于横向滚动（窄窗可读性；竖滚保留）
        self.list.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.list.currentItemChanged.connect(self._on_selection_changed)
        self.list.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.list.customContextMenuRequested.connect(self._on_context_menu)
        self.detail_label = QLabel("未选中物品")
        self.detail_label.setWordWrap(True)
        layout = QHBoxLayout(self)
        layout.addWidget(self.list, 1)
        layout.addWidget(self.detail_label, 1)

    def set_items(self, items: list[Item]) -> None:
        # 注入物品列表：刷新列表项（封面缩略图标 + PL002 两行文本：名称主行 / 形态·Tag·时长次行）
        self._items = items
        self.list.clear()
        for item in items:
            text = (
                f"{item.name}\n"
                f"{item.type.name}·{item.tag or '未分类'}·"
                f"{format_duration(item.total_seconds())}"
            )
            entry = QListWidgetItem(text)
            cover = resolve_cover(item)
            if cover and Path(cover).is_file():
                pixmap = QPixmap(cover)
                if not pixmap.isNull():
                    thumb = int(_SC.ui.get("thumbnail_size", 32))
                    entry.setIcon(
                        pixmap.scaled(thumb, thumb, Qt.AspectRatioMode.KeepAspectRatio)
                    )
            entry.setData(Qt.ItemDataRole.UserRole, item.id)
            self.list.addItem(entry)
        if items:
            self.list.setCurrentRow(0)

    def _on_selection_changed(
        self, current: QListWidgetItem | None, _prev=None
    ) -> None:
        # 选中变化 → 详情面板更新（名称/类型/Tag/面与曲目/封面）
        if current is None:
            self.detail_label.setText("未选中物品")
            return
        item = self._item_by_id(current.data(Qt.ItemDataRole.UserRole))
        if item is None:
            return
        lines = [
            f"名称：{item.name}",
            f"类型：{item.type.name}",
            f"Tag：{item.tag or '（无）'}",
            f"播放次数：{item.play_count}",
            f"总时长：{int(item.total_seconds())} 秒",
        ]
        for label, side in item.sides.items():
            lines.append(f"{label} 面：{len(side.tracks)} 首")
        self.detail_label.setText("\n".join(lines))

    def _item_by_id(self, item_id: str) -> Item | None:
        # 按 id 取物品（None 时忽略）
        for item in self._items:
            if item.id == item_id:
                return item
        return None

    def _on_context_menu(self, pos) -> None:
        # 右键菜单弹出：播放/编辑/重新刻录/删除（信号交 main_window 路由）
        menu = self._build_context_menu()
        menu.exec(self.list.mapToGlobal(pos))

    def _build_context_menu(self) -> QMenu:
        # 构建右键菜单（独立方法便于测试）：四项 action 发对应信号
        menu = QMenu(self)
        current = self.list.currentItem()
        item_id = current.data(Qt.ItemDataRole.UserRole) if current else None
        if item_id is None:
            return menu
        act_play = QAction("播放", menu)
        act_play.triggered.connect(lambda: self.play_requested.emit(item_id))
        act_edit = QAction("编辑", menu)
        act_edit.triggered.connect(lambda: self.edit_requested.emit(item_id))
        act_reg = QAction("重新刻录", menu)
        act_reg.triggered.connect(lambda: self.regenerate_requested.emit(item_id))
        act_del = QAction("删除", menu)
        act_del.triggered.connect(lambda: self.delete_requested.emit(item_id))
        menu.addAction(act_play)
        menu.addAction(act_edit)
        menu.addAction(act_reg)
        menu.addSeparator()
        menu.addAction(act_del)
        return menu


# ===== ui/views/library_view.py 类/函数说明 =====
# LibraryView(QWidget): 物品库视图
#   set_items(items): 全量刷新（列表 + 封面缩略；保持首项选中）
#   _on_selection_changed: 详情面板（名称/类型/Tag/次数/面曲目数）
#   _item_by_id(id): 列表 id 反查
#   _on_context_menu(pos): 右键菜单弹出（exec 阻塞式，仅在真实交互触发）
#   _build_context_menu() -> QMenu: 菜单构建（播放/编辑/重新刻录/删除 → 信号）
#   信号：play/edit/regenerate/delete_requested（交 main_window 路由）
#   设计理由：视图只发信号不执行业务；封面走 resolve_cover（placeholder 兜底）
#   关联配置：封面服务（modules/cover）、物品模型（modules/items）
