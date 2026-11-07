# 置物架视图（A11.4/A12.4）：按 Tag 分组陈列物品卡片（QGroupBox 组 + 可拖卡片按钮）
# PL001.4 卡片重设计：封面缩略图标 + 名称/形态·曲数两行文本；组框边距修溢出

from collections import defaultdict
from pathlib import Path

from PySide6.QtCore import QRect, QSize, QMimeData, QPoint, Qt, Signal
from PySide6.QtGui import QDrag, QIcon, QMouseEvent, QPixmap
from PySide6.QtWidgets import (
    QGroupBox,
    QLabel,
    QLayout,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from modules.cover.providers import resolve_cover
from modules.items.model import Item
from config.static.static_config import get_static_config
from ui.dnd import ITEM_MIME_TYPE, encode_item_id
from ui.widgets.parts import TEXTURES_DIR, texture_enabled, texture_pixmap

# 静态配置一次解包（卡片尺寸/拖拽阈值走 ui.json，B2.8）
_SC = get_static_config()


class DraggableCardButton(QPushButton):
    # 置物架物品卡片（PL001.4 重设计）：封面缩略图标 + 名称/形态·曲数两行文本，支持按住拖动

    def __init__(self, item: Item, item_id: str, parent: QWidget | None = None) -> None:
        # 初始化：按物品装配内容（缩略图 + 两行文本），记录物品 id，启动拖拽的按下位置置空；
        # 缩略图尺寸走 ui.json（FIX006.10：thumbnail 配置契约）
        total = sum(len(side.tracks) for side in item.sides.values())
        super().__init__(f"{item.name}\n{item.type.name}·{total}曲", parent)
        self._item_id = item_id
        self._press_pos: QPoint | None = None
        self._texture_on = False  # PL005.5 卡片贴图底开关（ShelfView.set_realism 同步）
        # PL004.1：空格已被全局播放/暂停快捷键占用、回车在非对话框不触发按钮——
        # 卡片没有键盘激活路径，不进焦点链（防"聚焦却不可激活"歧义）；激活走鼠标点击/拖放
        self.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        thumb = max(
            1, int(_SC.ui.get("shelf_thumbnail_size", 56))
        )  # max(1) 防除零惯例
        cover = resolve_cover(item)
        if cover and Path(cover).is_file():
            pixmap = QPixmap(cover)
            if not pixmap.isNull():
                thumbnail = pixmap.scaled(
                    thumb,
                    thumb,
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation,
                )
                self.setIcon(QIcon(thumbnail))
                self.setIconSize(QSize(thumb, thumb))

    def set_texture(self, on: bool) -> None:
        # 卡片贴图底开关（PL005.5，ShelfView.set_realism 同步）：经 QSS background-image 打底
        # （走 Qt 原生绘制路径——QSS 按钮层级内自绘 paintEvent 有崩溃面，2026-11-07 bisect 实证）；
        # 关闭/贴图缺失 → 清组件样式表回主题默认
        tex = texture_pixmap("walnut_panel") if on else None
        if tex is not None:
            url = (TEXTURES_DIR / "walnut_panel.png").as_posix()
            self.setStyleSheet(f"QPushButton {{ background-image: url({url}); }}")
        else:
            self.setStyleSheet("")
        self._texture_on = bool(tex is not None)

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


class _FlowLayout(QLayout):
    # 流式布局（PL004.2）：固定尺寸卡片按容器宽度自动换行——替代不换行的 QHBoxLayout，
    # 修最小窗下多卡溢出成横向滚动条；Qt FlowLayout 惯用算法的等价实现

    def __init__(self, parent: QWidget | None = None) -> None:
        # 初始化：条目列表 + 边距（PL001.4 沿革：上边距给组框标题留位）+ 行间距
        super().__init__(parent)
        self._items: list = []
        self.setContentsMargins(12, 20, 12, 12)
        self.setSpacing(10)

    def addItem(self, item: object) -> None:
        # 布局条目入列（addWidget 经此进入）
        self._items.append(item)

    def count(self) -> int:
        # 条目数
        return len(self._items)

    def itemAt(self, index: int) -> object | None:
        # 按索引取条目（越界 None）
        if 0 <= index < len(self._items):
            return self._items[index]
        return None

    def takeAt(self, index: int) -> object | None:
        # 按索引移除条目（组框重建时随 deleteLater 走释放链）
        if 0 <= index < len(self._items):
            return self._items.pop(index)
        return None

    def expandingDirections(self) -> Qt.Orientations:
        # 不主动吃额外空间（纵横皆 0——高度由 heightForWidth 决定）
        return Qt.Orientations()

    def hasHeightForWidth(self) -> bool:
        # 高随宽变声明（换行语义；滚动区 widgetResizable 据此撑容器高）
        return True

    def heightForWidth(self, width: int) -> int:
        # 给定宽度所需高度（只排布不落位）
        return self._arrange(QRect(0, 0, width, 0), test_only=True)

    def setGeometry(self, rect: QRect) -> None:
        # 实际排布：惯例先调父类，再按矩形真实落位
        super().setGeometry(rect)
        self._arrange(rect, test_only=False)

    def sizeHint(self) -> QSize:
        # 期望尺寸 = 最小尺寸（卡片恒定尺寸，两者一致）
        return self.minimumSize()

    def minimumSize(self) -> QSize:
        # 最小尺寸：单卡最大宽高 + 边距（可换行收缩的下限）
        margins = self.contentsMargins()
        max_w = 0
        max_h = 0
        for item in self._items:
            hint = item.sizeHint()
            max_w = max(max_w, hint.width())
            max_h = max(max_h, hint.height())
        return QSize(
            max_w + margins.left() + margins.right(),
            max_h + margins.top() + margins.bottom(),
        )

    def _arrange(self, rect: QRect, test_only: bool) -> int:
        # 换行排布核心：逐卡摆位，超出右缘折行；test_only 只算所需高度不落位
        margins = self.contentsMargins()
        spacing = self.spacing()
        avail_right = rect.right() - margins.right()
        x = rect.x() + margins.left()
        y = rect.y() + margins.top()
        row_height = 0
        for item in self._items:
            hint = item.sizeHint()
            next_x = x + hint.width() + spacing
            if next_x - spacing > avail_right and row_height > 0:
                # 折行：回到左缘、下移一行
                x = rect.x() + margins.left()
                y = y + row_height + spacing
                row_height = 0
                next_x = x + hint.width() + spacing
            if not test_only:
                item.setGeometry(QRect(QPoint(x, y), hint))
            x = next_x
            row_height = max(row_height, hint.height())
        return y + row_height + margins.bottom() - rect.y()


class ShelfView(QWidget):
    # 置物架视图：按 Tag 分组（每组 QGroupBox，组内物品卡片按钮）；点击卡片发播放信号
    item_clicked = Signal(str)

    def __init__(self, parent: QWidget | None = None) -> None:
        # 初始化：滚动区 + 分组容器（set_items 时重建）
        super().__init__(parent)
        self._items: list[Item] = []
        self._texture_on = False  # PL005.5 卡片贴图底开关（set_realism 注入）
        self._container = QWidget()
        self._shelf_layout = QVBoxLayout(self._container)
        self._shelf_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self._shelf_layout.setSpacing(10)  # PL001.4：组间距收敛
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setWidget(self._container)
        self.scroll = scroll  # 滚动区引用（验证断言用，PL004.2 横向滚动条检查）
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
            # PL004.2：组内卡片改流式布局（自动换行；边距/间距在 _FlowLayout 构造内定）
            flow = _FlowLayout(box)
            for item in tagged:
                btn = DraggableCardButton(item, item.id)
                card_w, card_h = _SC.ui.get("card_size", [110, 90])
                btn.setFixedSize(int(card_w), int(card_h))
                btn.set_texture(self._texture_on)
                btn.clicked.connect(
                    lambda _=False, iid=item.id: self.item_clicked.emit(iid)
                )
                flow.addWidget(btn)
            self._shelf_layout.addWidget(box)

    def set_realism(self, level: str) -> None:
        # 拟真度档位注入（PL005.5）：卡片贴图底开关随 effects.json texture 键，
        # 存档位供后续重建卡片继承 + 传播到在架卡片重绘
        self._texture_on = texture_enabled(str(level))
        for btn in self.findChildren(DraggableCardButton):
            btn.set_texture(self._texture_on)


# ===== ui/views/shelf_view.py 类/函数说明 =====
# _FlowLayout(QLayout): 流式布局（PL004.2）——固定尺寸卡片按容器宽度自动换行
#   _arrange(rect, test_only) -> int: 换行排布核心（test_only 只算所需高度；超出右缘折行）
#   heightForWidth/hasHeightForWidth: 高随宽变声明（滚动区 widgetResizable 据此撑容器高）
#   minimumSize/sizeHint: 单卡最大宽高 + 边距（可换行收缩的下限）
# DraggableCardButton(QPushButton): 物品卡片（缩略图 + 两行文本 + 按住拖动）
#   NoFocus（PL004.1）：空格被全局播放/暂停占用、回车非对话框不触发——无键盘激活路径不进焦点链
#   set_texture(on): 贴图底经 QSS background-image 打底（PL005.5；不走自绘——QSS 按钮层级
#     自绘 paintEvent 存在 C++ 崩溃面（bisect 实证），原生绘制路径稳定性已由全部现有视图证明）
# ShelfView(QWidget): 置物架视图（按 Tag 分组陈列）
#   scroll: 滚动区引用（验证断言用，PL004.2）
#   set_items(items): 分组重建（tag 分组 → QGroupBox + _FlowLayout 卡片流；无 Tag → 未分类）
#   set_realism(level): 拟真度档位注入（PL005.5：卡片贴图底开关，传播在架卡片 + 重建继承）
#   item_clicked(str): 卡片点击信号（交 main_window 路由到唱机播放）
#   设计理由：陈列视图不持久化数据（物品的家是物品库）；分组仅视图逻辑；
#     组内行布局改流式（PL004.2：原 QHBoxLayout 不换行，最小窗多卡溢出横向滚动条）
#   关联配置：物品模型（modules/items）
