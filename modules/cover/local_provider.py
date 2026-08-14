# 本地封面提供器（A7.2/B1.3/G0.3）：用户选封面复制到 music/covers/（UUID 命名）并写回 item.cover_path

import os
import shutil
import uuid
from pathlib import Path

from modules.cover.providers import COVERS_DIR, CoverProvider
from modules.items.model import Item


def import_cover_file(source: str, item: Item) -> str | None:
    # 复制用户封面文件到 covers/{uuid4().hex}{原扩展名}（G0.3 原子写：临时文件 + os.replace）→ 写回 cover_path
    try:
        src = Path(source)
        if not src.is_file():
            return None
        COVERS_DIR.mkdir(parents=True, exist_ok=True)
        dst = COVERS_DIR / f"{uuid.uuid4().hex}{src.suffix.lower()}"
        tmp = dst.with_suffix(dst.suffix + ".tmp")
        try:
            with src.open("rb") as fin, tmp.open("wb") as fout:
                shutil.copyfileobj(fin, fout)
            os.replace(tmp, dst)  # 原子改名：中途失败不留半截目标文件
        except Exception:
            tmp.unlink(missing_ok=True)
            raise
        item.cover_path = str(dst)
        return str(dst)
    except Exception:
        return None


class LocalProvider(CoverProvider):
    # 本地封面提供器：cover_path 存在则返回，否则 None（未导入过/文件被删）

    def get_cover(self, item: Item) -> str | None:
        # 返回已写回的封面路径（文件存在才返回；缺失返回 None 交占位图兜底）
        if item.cover_path and Path(item.cover_path).is_file():
            return item.cover_path
        return None


# ===== modules/cover/local_provider.py 函数/类说明 =====
# import_cover_file(source, item) -> str | None: 导入封面
#   逻辑：源存在 → covers 目录确保 → UUID 命名复制（保留扩展名）→ 写回 item.cover_path
#   异常：任何失败返回 None（不崩溃，调用方降级占位图）
# LocalProvider(CoverProvider): 本地提供器
#   get_cover(item): cover_path 有效（文件存在）则返回；否则 None
#   设计理由：UUID 命名避免文件名冲突；写回路径供持久化（A6 items.cover_path 列）
#   关联配置：COVERS_DIR（providers.py，base.json music_dir 装配）
