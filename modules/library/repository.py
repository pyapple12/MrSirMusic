# 物品库仓储模块（A6.2）：CRUD 事务读写（items + tracks 组装/持久化），外键级联删除

import sqlite3
from pathlib import Path

from modules.items.model import Item, ItemType, Side, Track
from modules.library.migration import migrate
from modules.library.schema import DB_PATH

# 载体类型配置（加载 Item 时重建 ItemType）
from config.static.static_config import get_static_config

_ITEM_TYPES_CFG = get_static_config().item_types


def _connect() -> sqlite3.Connection:
    # 打开物品库连接：外键开启 + Row 工厂 + 迁移确保 schema（用户库走事务写）
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    migrate(conn)
    return conn


def _item_to_rows(item: Item) -> tuple[tuple, list[tuple]]:
    # 物品 → (items 行, tracks 行列表)：tracks 含面 label 与面内 position
    item_row = (
        item.id,
        item.name,
        item.type.key,
        item.cover_source,
        item.cover_path,
        item.tag,
        item.created_at,
        item.play_count,
    )
    track_rows = []
    for side_label, side in item.sides.items():
        for pos, t in enumerate(side.tracks):
            track_rows.append(
                (
                    item.id,
                    side_label,
                    pos,
                    t.path,
                    t.title,
                    t.artist,
                    t.album,
                    t.duration_seconds,
                    t.format,
                )
            )
    return item_row, track_rows


def _row_to_item(item_row: sqlite3.Row, track_rows: list[sqlite3.Row]) -> Item:
    # 数据行 → Item：重建 ItemType + 按面分组组装 Side（position 排序）
    item_type = ItemType.from_config(
        item_row["type"], _ITEM_TYPES_CFG.get(item_row["type"], {})
    )
    item = Item(
        id=item_row["id"],
        name=item_row["name"],
        type=item_type,
        cover_source=item_row["cover_source"],
        cover_path=item_row["cover_path"],
        tag=item_row["tag"],
        created_at=item_row["created_at"],
        play_count=item_row["play_count"],
    )
    sides: dict[str, Side] = {}
    for label in item_type.sides:
        sides[label] = Side(label=label)
    for r in sorted(track_rows, key=lambda r: r["position"]):
        side = sides.setdefault(r["side_label"], Side(label=r["side_label"]))
        side.tracks.append(
            Track(
                path=r["path"],
                title=r["title"],
                artist=r["artist"],
                album=r["album"],
                duration_seconds=r["duration"],
                format=r["format"],
            )
        )
    item.sides = sides
    return item


def save_item(item: Item) -> None:
    # 完整持久化：items 行 upsert + tracks 整体重建（事务；新建/整体变更用）
    conn = _connect()
    try:
        item_row, track_rows = _item_to_rows(item)
        conn.execute(
            """INSERT INTO items (id, name, type, cover_source, cover_path, tag, created_at, play_count)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)
               ON CONFLICT(id) DO UPDATE SET name=excluded.name, type=excluded.type,
                   cover_source=excluded.cover_source, cover_path=excluded.cover_path,
                   tag=excluded.tag, play_count=excluded.play_count""",
            item_row,
        )
        conn.execute("DELETE FROM tracks WHERE item_id=?", (item.id,))
        conn.executemany(
            """INSERT INTO tracks (item_id, side_label, position, path, title, artist, album, duration, format)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            track_rows,
        )
        conn.commit()
    finally:
        conn.close()


def load_all() -> list[Item]:
    # 全量加载：一次查 items + 一次查全部 tracks，内存组装
    conn = _connect()
    try:
        item_rows = conn.execute("SELECT * FROM items ORDER BY created_at").fetchall()
        track_rows = conn.execute(
            "SELECT * FROM tracks ORDER BY item_id, side_label, position"
        ).fetchall()
        by_item: dict[str, list] = {}
        for r in track_rows:
            by_item.setdefault(r["item_id"], []).append(r)
        return [_row_to_item(r, by_item.get(r["id"], [])) for r in item_rows]
    finally:
        conn.close()


def load_item(item_id: str) -> Item | None:
    # 单物品加载（含 tracks）；不存在返回 None
    conn = _connect()
    try:
        row = conn.execute("SELECT * FROM items WHERE id=?", (item_id,)).fetchone()
        if row is None:
            return None
        track_rows = conn.execute(
            "SELECT * FROM tracks WHERE item_id=? ORDER BY side_label, position",
            (item_id,),
        ).fetchall()
        return _row_to_item(row, track_rows)
    finally:
        conn.close()


def delete_item(item_id: str) -> None:
    # 删除物品：外键 ON DELETE CASCADE 级联删 tracks（事务）
    conn = _connect()
    try:
        conn.execute("DELETE FROM items WHERE id=?", (item_id,))
        conn.commit()
    finally:
        conn.close()


def update_item(item: Item) -> None:
    # 更新 items 行字段（name/tag/cover/play_count 等），不动 tracks（与 save_item 区分）
    conn = _connect()
    try:
        conn.execute(
            """UPDATE items SET name=?, type=?, cover_source=?, cover_path=?, tag=?, play_count=?
               WHERE id=?""",
            (
                item.name,
                item.type.key,
                item.cover_source,
                item.cover_path,
                item.tag,
                item.play_count,
                item.id,
            ),
        )
        conn.commit()
    finally:
        conn.close()


# ===== modules/library/repository.py 函数/常量说明 =====
# _ITEM_TYPES_CFG: 载体类型配置（加载时重建 ItemType，从 static_config 一次性解包）
# _connect() -> Connection: 连接（外键 ON + Row 工厂 + migrate 确保 schema）
# _item_to_rows(item) -> (items 行, tracks 行): 物品 → 数据行（position = 面内序号）
# _row_to_item(item_row, track_rows) -> Item: 行 → 物品（ItemType 重建 + 面分组 + position 排序）
# save_item(item): 完整持久化（upsert + tracks 重建；事务，失败回滚不写半截）
# load_all() -> list[Item]: 全量（两查询内存组装，无 N+1）
# load_item(id) -> Item | None: 单查（无 → None）
# delete_item(id): 删除（外键级联 tracks）
# update_item(item): 只更新 items 行（改元数据/播放次数不重建 tracks）
#   设计理由：save 与 update 职责分离（整体重建 vs 行更新）；全量事务保证一致性
#   关联配置：DB_PATH（schema.py）、载体类型（item_types.json）
