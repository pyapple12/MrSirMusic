# 拖放契约（A12.4）：物品拖放 mime 类型常量与编解码（置物架卡片/物品库列表 → 唱机）

from PySide6.QtCore import QMimeData

# 物品拖放 mime 类型（携带物品 id）
ITEM_MIME_TYPE = "application/x-mrsirmusic-item"


def encode_item_id(item_id: str) -> bytes:
    # 物品 id → mime 载荷（UTF-8 编码）
    return item_id.encode("utf-8")


def decode_item_id(mime: QMimeData) -> str | None:
    # mime → 物品 id（非本类型返回 None）
    if not mime.hasFormat(ITEM_MIME_TYPE):
        return None
    try:
        return bytes(mime.data(ITEM_MIME_TYPE)).decode("utf-8")
    except Exception:
        return None


def is_item_drag(mime: QMimeData) -> bool:
    # 拖放判定：携带本物品 mime 类型即视为物品拖放
    return mime.hasFormat(ITEM_MIME_TYPE)


# ===== ui/dnd.py 函数/常量说明 =====
# ITEM_MIME_TYPE: 物品拖放 mime 类型（自定义格式，携带 item id）
# encode_item_id(id) -> bytes: id 编码（UTF-8）
# decode_item_id(mime) -> str | None: 解码（类型不符/损坏返回 None）
# is_item_drag(mime) -> bool: 判定（拖入唱机时 dragEnterEvent 用）
#   设计理由：mime 契约独立成模块，置物架/物品库（拖出）与唱机（拖入）共用
#   关联配置：无（纯 Qt mime 契约）
