# MP3 解码器声明（A9.5）：EXTENSIONS + probe（ID3 头或 MPEG 帧同步）；第一版解码走 QtMultimedia

from pathlib import Path
from typing import Any

EXTENSIONS = (".mp3",)


def probe(path: Path) -> bool:
    # 文件头验证：ID3 标签头或 MPEG 音频帧同步（0xFFEx）
    try:
        head = path.read_bytes()[:3]
        return head.startswith(b"ID3") or (
            len(head) >= 2 and head[0] == 0xFF and (head[1] & 0xE0) == 0xE0
        )
    except Exception:
        return False


def decoder(path: Path) -> Any:
    # 占位：第一版解码实际走 QtMultimedia（QMediaPlayer），本函数为注册表契约占位
    raise NotImplementedError("第一版解码由 QtMultimedia 承担，占位接口")


# ===== modules/playback/decoders/mp3.py 函数/常量说明 =====
# EXTENSIONS: 支持扩展名（.mp3）
# probe(path) -> bool: ID3 头（"ID3"）或 MPEG 帧同步（0xFF + 0xE0 掩码）验证
# decoder(path): 占位（QtMultimedia 承担实际解码；注册表契约为未来独立解码进程预留）
