# 物品库建表模块（A6.1）：SQLite items/tracks/schema_version 建表，外键 + 索引

import sqlite3
from pathlib import Path

from config.static.static_config import get_static_config

# 库文件路径（music/items.db；music_dir 来自 base.json，项目根相对）
DB_PATH = (
    Path(__file__).resolve().parent.parent.parent
    / get_static_config().base.get("music_dir", "music")
    / "items.db"
)

# 当前 schema 版本（v1 首版建库）
SCHEMA_VERSION = 1

_SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS items (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    type TEXT NOT NULL,
    cover_source TEXT NOT NULL DEFAULT 'placeholder',
    cover_path TEXT NOT NULL DEFAULT '',
    tag TEXT NOT NULL DEFAULT '',
    created_at TEXT NOT NULL DEFAULT '',
    play_count INTEGER NOT NULL DEFAULT 0
);
CREATE TABLE IF NOT EXISTS tracks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    item_id TEXT NOT NULL REFERENCES items(id) ON DELETE CASCADE,
    side_label TEXT NOT NULL,
    position INTEGER NOT NULL,
    path TEXT NOT NULL,
    title TEXT NOT NULL DEFAULT '',
    artist TEXT NOT NULL DEFAULT '',
    album TEXT NOT NULL DEFAULT '',
    duration REAL NOT NULL DEFAULT 0,
    format TEXT NOT NULL DEFAULT ''
);
CREATE INDEX IF NOT EXISTS idx_tracks_item ON tracks(item_id);
CREATE INDEX IF NOT EXISTS idx_tracks_side ON tracks(item_id, side_label);
CREATE TABLE IF NOT EXISTS schema_version (
    version INTEGER NOT NULL
);
"""


def create_schema(conn: sqlite3.Connection) -> None:
    # 建表（幂等）：items/tracks（外键级联 + 双索引）+ schema_version；并写入当前版本号
    conn.executescript(_SCHEMA_SQL)
    conn.execute("DELETE FROM schema_version")
    conn.execute("INSERT INTO schema_version (version) VALUES (?)", (SCHEMA_VERSION,))
    conn.commit()


# ===== modules/library/schema.py 函数/常量说明 =====
# DB_PATH: 物品库文件路径（music/items.db，music_dir 来自 base.json；项目根相对）
# SCHEMA_VERSION: 当前 schema 版本（v1 首版；迁移注册表键）
# _SCHEMA_SQL: 建表脚本（幂等 CREATE IF NOT EXISTS；items 主键 id；tracks 外键
#   级联删除 + item_id / (item_id, side_label) 双索引；schema_version 单行版本号）
# create_schema(conn) -> None: 幂等建表 + 写版本（事务提交）
#   设计理由：外键级联让 delete_item 自动清 tracks（A6.2）；双索引覆盖"按物品查"
#     与"按物品+面查"两类访问路径
#   关联配置：DB_PATH 由 base.json music_dir 装配
