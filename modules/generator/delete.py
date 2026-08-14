# 删除模块（A8.4）：库删除 + 封面实体文件删除（仅当无其他物品引用同一封面）

from pathlib import Path

from modules.items.model import Item
from modules.library.repository import DB_PATH, delete_item, load_item


def _cover_referenced(cover_path: str, exclude_item_id: str) -> bool:
    # 查询库中是否有其他物品引用同一封面路径（排除自身）
    import sqlite3

    try:
        conn = sqlite3.connect(DB_PATH)
        try:
            row = conn.execute(
                "SELECT COUNT(*) FROM items WHERE cover_path=? AND id!=?",
                (cover_path, exclude_item_id),
            ).fetchone()
            return bool(row and row[0] > 0)
        finally:
            conn.close()
    except Exception:
        return False


def delete(item: Item) -> None:
    # 删除物品：库删除（级联 tracks）+ 封面实体文件删除（仅当无其他物品引用）；封面文件不存在忽略
    cover_path = item.cover_path
    delete_item(item.id)
    if cover_path and not _cover_referenced(cover_path, item.id):
        try:
            Path(cover_path).unlink(missing_ok=True)
        except Exception:
            pass


# ===== modules/generator/delete.py 函数说明 =====
# _cover_referenced(cover_path, exclude_item_id) -> bool: 封面引用检查
#   逻辑：SQLite 直连（独立连接，避免仓储事务嵌套）查 items 中同 cover_path 且 id != 自身
#   异常：连接失败返回 False（保守：视为无引用，允许删文件）
# delete(item) -> None: 删除
#   逻辑：delete_item（外键级联删 tracks）→ 若有 cover_path 且无其他引用 → 删封面文件
#   设计理由：封面文件可能被多物品共享（用户复用同一封面），无引用才清理（A8.4 定案）
#   关联配置：DB_PATH（schema.py）、封面目录（providers.py）
