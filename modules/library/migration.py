# 迁移模块（A6.3）：schema_version 读取 + 迁移函数注册表，逐级升级到最新版本

import sqlite3
from typing import Callable

from modules.library.schema import DB_PATH, SCHEMA_VERSION, create_schema


def _migrate_v1(conn: sqlite3.Connection) -> None:
    # v1 迁移：首版建库（幂等建表 + 写版本）
    create_schema(conn)


# 迁移函数注册表：version → 函数（新增 schema 变更时加一项，永不修改已发布的迁移）
MIGRATIONS: dict[int, Callable[[sqlite3.Connection], None]] = {1: _migrate_v1}


def _connect() -> sqlite3.Connection:
    # 建迁移专用连接（库不存在时先确保父目录）
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    return sqlite3.connect(DB_PATH)


def get_schema_version(conn: sqlite3.Connection) -> int:
    # 读取当前 schema 版本：无版本表视为 0（未初始化）；读取失败容错为 0
    try:
        row = conn.execute("SELECT version FROM schema_version").fetchone()
        return int(row[0]) if row else 0
    except Exception:
        return 0


def migrate(conn: sqlite3.Connection | None = None) -> None:
    # 执行迁移：从当前版本逐级应用注册表到最新；自己打开的连接用完即关；幂等
    own_conn = conn is None
    if own_conn:
        conn = _connect()
    try:
        current = get_schema_version(conn)
        for version in sorted(MIGRATIONS):
            if version > current:
                MIGRATIONS[version](conn)
        conn.commit()
    finally:
        if own_conn:
            conn.close()


# ===== modules/library/migration.py 函数/常量说明 =====
# _migrate_v1(conn): v1 建库（委托 create_schema；幂等）
# MIGRATIONS: 迁移注册表（version → 函数；只增不改，新增 schema 变更 = 加一项）
# _connect() -> Connection: 迁移专用连接（父目录确保）
# get_schema_version(conn) -> int: 版本读取（无表/坏表 → 0，宽容降级）
# migrate(conn|None) -> None: 逐级迁移到最新
#   逻辑：取当前版本 → 对注册表中高于当前版本的项依次执行 → 提交
#   异常：迁移函数失败上抛（schema 错误属开发期缺陷，快速暴露而非静默）
#   关联配置：DB_PATH（schema.py 同源）
