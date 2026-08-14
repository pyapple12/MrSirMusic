# 删除模块（A8.4/B0.3）：库删除 + 封面实体文件删除（仅当无其他物品引用同一封面）

import sqlite3
from pathlib import Path

from modules.items.model import Item
from modules.library.repository import delete_item, get_db_path


def _cover_referenced(cover_path: str, exclude_item_id: str) -> bool:
    # 查询库中是否有其他物品引用同一封面路径（排除自身）；查询失败保守返回 True（不删文件，防误删共享封面）
    try:
        conn = sqlite3.connect(get_db_path())
        try:
            row = conn.execute(
                "SELECT COUNT(*) FROM items WHERE cover_path=? AND id!=?",
                (cover_path, exclude_item_id),
            ).fetchone()
            return bool(row and row[0] > 0)
        finally:
            conn.close()
    except Exception:
        return True


def delete(item: Item) -> None:
    # 删除物品：库删除（级联 tracks）+ 封面实体文件删除（仅当无其他物品引用，且路径在 covers 目录内）
    cover_path = item.cover_path
    delete_item(item.id)
    if cover_path and not _cover_referenced(cover_path, item.id):
        from modules.cover.providers import COVERS_DIR

        try:
            candidate = Path(cover_path).resolve()
            if candidate.parent == COVERS_DIR.resolve():
                candidate.unlink(missing_ok=True)
        except Exception:
            pass


# ===== modules/generator/delete.py 函数说明 =====
# _cover_referenced(cover_path, exclude_item_id) -> bool: 封面引用检查
#   逻辑：SQLite 直连（独立连接，避免仓储事务嵌套）查 items 中同 cover_path 且 id != 自身
#   异常：连接失败保守返回 True（视为有引用，不删文件——B0.3 修正，防误删共享封面）
# delete(item) -> None: 删除
#   逻辑：delete_item（外键级联删 tracks）→ 无引用且路径在 COVERS_DIR 内 → 删封面文件
#   安全：unlink 前校验 resolve 后父目录 == COVERS_DIR（防 DB 被篡改时删除任意文件）
#   关联配置：get_db_path（repository 单点，B0.3）、COVERS_DIR（providers.py）
