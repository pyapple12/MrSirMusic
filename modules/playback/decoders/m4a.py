# M4A 解码器声明（A9.5）：EXTENSIONS + probe（ftyp box 魔数）；第一版解码走 QtMultimedia

from pathlib import Path
from typing import Any

EXTENSIONS = (".m4a",)


def probe(path: Path) -> bool:
    # 文件头验证：MP4 容器以 ftyp box 开头（偏移 4 处 "ftyp"）；流式读取前 12 字节（C2.1 不整文件读盘）
    try:
        with open(path, "rb") as f:
            head = f.read(12)
        return head[4:8] == b"ftyp"
    except Exception:
        return False


def decoder(path: Path) -> Any:
    # 占位：第一版解码实际走 QtMultimedia（QMediaPlayer），本函数为注册表契约占位
    raise NotImplementedError("第一版解码由 QtMultimedia 承担，占位接口")


# ===== modules/playback/decoders/m4a.py 函数/常量说明 =====
# EXTENSIONS: 支持扩展名（.m4a）
# probe(path) -> bool: MP4 ftyp box 魔数验证（偏移 4）
# decoder(path): 占位（QtMultimedia 承担实际解码）
