# 物品拟物绘制（A12.1）：按 ItemType.shape 绘制形态（circle 黑胶/CD、rect 磁带盒），渐变+阴影质感，无动画

from pathlib import Path

from PySide6.QtCore import QRectF, Qt
from PySide6.QtGui import (
    QColor,
    QLinearGradient,
    QPainter,
    QPen,
    QPixmap,
    QRadialGradient,
)
from PySide6.QtWidgets import QWidget

from modules.cover.providers import resolve_cover
from modules.items.model import Item


class RecordWidget(QWidget):
    # 物品拟物绘制控件：circle（黑胶同心圆 + 封面中心）/ rect（磁带盒造型）；基础质感

    def __init__(self, item: Item | None = None, parent: QWidget | None = None) -> None:
        # 初始化：绑定物品 + 加载封面（resolve_cover 兜底占位图）+ 效果器列表空
        super().__init__(parent)
        self._item = item
        self._cover: QPixmap | None = None
        self._effects: list = []
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
        # 换物品：刷新封面并重绘
        self._item = item
        cover = resolve_cover(item)
        if cover and Path(cover).is_file():
            pixmap = QPixmap(cover)
            if not pixmap.isNull():
                self._cover = pixmap
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
        # 磁带盒：圆角矩形渐变壳 + 上窗口（半透明）+ 底部标签（封面或色块）
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


# ===== ui/widgets/record_widget.py 类/函数说明 =====
# RecordWidget(QWidget): 物品拟物绘制（无动画，基础质感）
#   set_item(item): 换物品（resolve_cover 加载封面 → update）
#   paintEvent: 按 shape 分派（circle → _paint_record，rect → _paint_cassette）
#   _paint_record: 径向渐变圆盘 + 4 圈槽纹 + 中心封面圆（QPainterPath 圆形裁剪）
#   _paint_cassette: 圆角渐变壳 + 半透明上窗 + 底部封面标签
#   pixmap_image(): grab 渲染结果（验证用）
#   设计理由：绘制纯 QPainter（无动画），质感来自渐变/阴影；封面经 resolve_cover 兜底
#   关联配置：ItemType.shape（item_types.json）、封面服务（modules/cover）
