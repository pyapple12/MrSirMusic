# 文件工具模块（A2.2）：pathlib 封装，零业务依赖（音频判定/目录确保/安全复制/存在检查）

import shutil
from pathlib import Path

# 音频扩展名集合（与播放解码器注册表对齐：mp3/flac/wav/m4a；判定时统一小写）
AUDIO_EXTENSIONS = frozenset({".mp3", ".flac", ".wav", ".m4a"})


def is_audio_file(path: str | Path) -> bool:
    # 按扩展名判断是否音频文件（大小写不敏感）
    return Path(path).suffix.lower() in AUDIO_EXTENSIONS


def ensure_dir(path: str | Path) -> Path:
    # 确保目录存在（含多级），返回目录 Path
    p = Path(path)
    p.mkdir(parents=True, exist_ok=True)
    return p


def safe_copy(src: str | Path, dst: str | Path) -> bool:
    # 安全复制：源存在则复制（自动建目标目录），成功返回 True；源缺失/失败返回 False，不抛出
    try:
        src_p = Path(src)
        if not src_p.is_file():
            return False
        dst_p = Path(dst)
        dst_p.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src_p, dst_p)
        return True
    except Exception:
        return False


def file_exists(path: str | Path) -> bool:
    # 文件存在性检查（目录不算）
    return Path(path).is_file()


# ===== utils/file_utils.py 函数/常量说明 =====
# AUDIO_EXTENSIONS: 音频扩展名白名单（frozenset，小写；与 decoders 注册表同步维护）
# is_audio_file(path) -> bool: 扩展名判定（大小写不敏感，非文件路径字符串也可判定）
# ensure_dir(path) -> Path: 目录确保（mkdir parents + exist_ok），返回目录 Path
# safe_copy(src, dst) -> bool: 安全复制
#   逻辑：源存在检查 → 目标目录确保 → copy2 → True；任何失败返回 False
#   异常：全部捕获返回 False（不崩溃；调用方按返回值降级）
# file_exists(path) -> bool: 文件存在检查（Path.is_file，目录返回 False）
#   关联配置：无（零业务依赖，utils 层最底层）
