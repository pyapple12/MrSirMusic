# 置物架视图（A11.4/A12.4）：按 Tag 分组陈列物品卡片（QGroupBox 组 + 可拖卡片按钮）

from collections import defaultdict

from PySide6.QtCore import QMimeData, QPoint, Qt, Signal
from PySide6.QtGui import QDrag, QMouseEvent
from PySide6.QtWidgets import (
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from modules.items.model import Item
from config.static.static_config import get_static_config
from ui.dnd import ITEM_MIME_TYPE, encode_item_id

# 静态配置一次解包（卡片尺寸/拖拽阈值走 ui.json，B2.8）
_SC = get_static_config()


class DraggableCardButton(QPushButton):
    # 置物架物品卡片：支持按住拖动（QDrag 携带物品 id，拖入唱机触发播放）

    def __init__(self, text: str, item_id: str, parent: QWidget | None = None) -> None:
        # 初始化：记录物品 id，启动拖拽的按下位置置空
        super().__init__(text, parent)
        self._item_id = item_id
        self._press_pos: QPoint | None = None

    def mousePressEvent(self, event: QMouseEvent) -> None:
        # 记录按下位置（左键）
        if event.button() == Qt.MouseButton.LeftButton:
            self._press_pos = event.position().toPoint()
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event: QMouseEvent) -> None:
        # 按住移动超阈值 → 启动 QDrag（mime 带物品 id）
        if self._press_pos is not None and event.buttons() & Qt.MouseButton.LeftButton:
            threshold = int(_SC.ui.get("drag_threshold", 8))
            if (
                event.position().toPoint() - self._press_pos
            ).manhattanLength() > threshold:
                drag = QDrag(self)
                mime = QMimeData()
                mime.setData(ITEM_MIME_TYPE, encode_item_id(self._item_id))
                drag.setMimeData(mime)
                drag.exec(Qt.DropAction.CopyAction)
                self._press_pos = None
                return
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event: QMouseEvent) -> None:
        # 释放时清除按下位置
        self._press_pos = None
        super().mouseReleaseEvent(event)


class ShelfView(QWidget):
    # 置物架视图：按 Tag 分组（每组 QGroupBox，组内物品卡片按钮）；点击卡片发播放信号
    item_clicked = Signal(str)

    def __init__(self, parent: QWidget | None = None) -> None:
        # 初始化：滚动区 + 分组容器（set_items 时重建）
        super().__init__(parent)
        self._items: list[Item] = []
        self._container = QWidget()
        self._shelf_layout = QVBoxLayout(self._container)
        self._shelf_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setWidget(self._container)
        layout = QVBoxLayout(self)
        layout.addWidget(scroll)

    def set_items(self, items: list[Item]) -> None:
        # 注入物品：按 tag 分组重建（无 Tag 归入"未分类"）
        self._items = items
        while self._shelf_layout.count():
            item = self._shelf_layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()
        groups: dict[str, list[Item]] = defaultdict(list)
        for item in items:
            groups[item.tag or "未分类"].append(item)
        if not groups:
            # B3.18：空标签每次重建（不 deleteLater 复用，防空→有→空时序 RuntimeError）
            self._shelf_layout.addWidget(QLabel("置物架空荡荡——先生成一件物品吧"))
            return
        for tag, tagged in sorted(groups.items()):
            box = QGroupBox(tag)
            row = QHBoxLayout(box)
            for item in tagged:
                btn = DraggableCardButton(f"{item.name}\n{item.type.name}", item.id)
                card_w, card_h = _SC.ui.get("card_size", [110, 90])
                btn.setFixedSize(int(card_w), int(card_h))
                btn.clicked.connect(
                    lambda _=False, iid=item.id: self.item_clicked.emit(iid)
                )
                row.addWidget(btn)
            row.addStretch(1)
            self._shelf_layout.addWidget(box)


# ===== ui/views/shelf_view.py 类/函数说明 =====
# ShelfView(QWidget): 置物架视图（按 Tag 分组陈列）
#   set_items(items): 分组重建（tag 分组 → QGroupBox + 卡片 QPushButton；无 Tag → 未分类）
#   item_clicked(str): 卡片点击信号（交 main_window 路由到唱机播放）
#   设计理由：陈列视图不持久化数据（物品的家是物品库）；分组仅视图逻辑
#   关联配置：物品模型（modules/items）
