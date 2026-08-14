# FLAC 解码器声明（A9.5）：EXTENSIONS + probe（fLaC 魔数）；第一版解码走 QtMultimedia

from pathlib import Path
from typing import Any

EXTENSIONS = (".flac",)


def probe(path: Path) -> bool:
    # 文件头验证：FLAC 魔数 "fLaC"；流式读取前 4 字节（C2.1 不整文件读盘）
    try:
        with open(path, "rb") as f:
            head = f.read(4)
        return head == b"fLaC"
    except Exception:
        return False


def decoder(path: Path) -> Any:
    # 占位：第一版解码实际走 QtMultimedia（QMediaPlayer），本函数为注册表契约占位
    raise NotImplementedError("第一版解码由 QtMultimedia 承担，占位接口")


# ===== modules/playback/decoders/flac.py 函数/常量说明 =====
# EXTENSIONS: 支持扩展名（.flac）
# probe(path) -> bool: fLaC 魔数验证
# decoder(path): 占位（QtMultimedia 承担实际解码）
