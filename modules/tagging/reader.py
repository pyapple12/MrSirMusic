# 标签解析模块（A4.2-A4.4）：按扩展名分派 mutagen 读取，容错降级 empty_record，批量解析

from pathlib import Path
from typing import Any

from modules.tagging.tag_data import TagData


def empty_record(path: str | Path) -> TagData:
    # 降级记录：title=文件名（去扩展名），其余空，format=扩展名（不抛异常，单曲失败不影响整体）
    p = Path(path)
    return TagData(
        title=p.stem, duration_seconds=0.0, format=p.suffix.lstrip(".").lower()
    )


def _first_text(tags: Any, *keys: str) -> str:
    # 从标签对象按键序取首个文本值（EasyID3/Vorbis 为 str；MP4 为 list[str]；ID3 为 str），空则返回 ""
    for key in keys:
        value = tags.get(key)
        if value:
            if isinstance(value, list):
                return str(value[0])
            return str(value)
    return ""


def _read_id3_file(path: Path, fmt: str) -> TagData:
    # 读取带 ID3 标签的文件（mp3/wav）：mutagen.File 可解析时取 info 时长；无音频帧时 ID3 纯标签降级
    from mutagen import File as MFile
    from mutagen.id3 import ID3

    try:
        mfile = MFile(path)
    except Exception:
        mfile = None
    if mfile is not None:
        length = float(getattr(mfile.info, "length", 0.0) or 0.0)
        tags = mfile.tags or {}
    else:
        tags = ID3(path)
        length = 0.0
    return TagData(
        title=_first_text(tags, "TIT2") or Path(path).stem,
        artist=_first_text(tags, "TPE1"),
        album=_first_text(tags, "TALB"),
        duration_seconds=length,
        format=fmt,
    )


def _read_flac(path: Path, fmt: str) -> TagData:
    # 读取 FLAC 标签（Vorbis comment 统一键 title/artist/album）；时长取 info.length，无效给 0
    from mutagen.flac import FLAC

    audio = FLAC(path)
    length = float(getattr(audio.info, "length", 0.0) or 0.0)
    return TagData(
        title=_first_text(audio.tags or {}, "title") or Path(path).stem,
        artist=_first_text(audio.tags or {}, "artist"),
        album=_first_text(audio.tags or {}, "album"),
        duration_seconds=length,
        format=fmt,
    )


def _read_mp4(path: Path, fmt: str) -> TagData:
    # 读取 M4A 标签（MP4 键 \xa9nam/\xa9ART/\xa9alb）；时长取 info.length，无效给 0
    from mutagen.mp4 import MP4

    audio = MP4(path)
    length = float(getattr(audio.info, "length", 0.0) or 0.0)
    return TagData(
        title=_first_text(audio.tags or {}, "\xa9nam") or Path(path).stem,
        artist=_first_text(audio.tags or {}, "\xa9ART"),
        album=_first_text(audio.tags or {}, "\xa9alb"),
        duration_seconds=length,
        format=fmt,
    )


# 扩展名 → 读取函数分派表（新格式 = 加一个读取函数 + 一条映射，未知格式走降级）
_READERS: dict[str, Any] = {
    ".mp3": _read_id3_file,
    ".flac": _read_flac,
    ".wav": _read_id3_file,
    ".m4a": _read_mp4,
}


def read_tags(path: str | Path) -> TagData:
    # 单曲标签解析：按扩展名分派；未知格式/损坏/解析失败一律返回 empty_record，不抛异常
    p = Path(path)
    reader = _READERS.get(p.suffix.lower())
    if reader is None:
        return empty_record(p)
    try:
        return reader(p, p.suffix.lstrip(".").lower())
    except Exception:
        return empty_record(p)


def read_tags_batch(paths: list[str | Path]) -> list[TagData]:
    # 批量解析：逐曲降级（单曲失败不影响整体），返回与输入等长的 TagData 列表
    return [read_tags(p) for p in paths]


# ===== modules/tagging/reader.py 函数/常量说明 =====
# empty_record(path) -> TagData: 降级记录（title=stem，format=扩展名；A4.3 容错策略）
# _first_text(tags, *keys) -> str: 多键取首个文本（兼容 list[str] 与 str；MP4 键语义）
# _read_id3_file(path, fmt) -> TagData: mp3/wav（ID3 帧键 TIT2/TPE1/TALB）
#   逻辑：mutagen.File 可解析（含音频数据）→ 取 info 时长 + tags；纯标签文件（无帧）→ ID3 纯标签，时长 0
#   异常：损坏文件 ID3 解析抛错 → 外层 read_tags 捕获降级 empty_record
# _read_flac(path, fmt) -> TagData: FLAC（Vorbis comment 键 title/artist/album + info.length）
# _read_mp4(path, fmt) -> TagData: M4A（MP4 键 \xa9nam/\xa9ART/\xa9alb + info.length）
# _READERS: 扩展名分派表（对齐解码器注册表思路：新格式加函数 + 映射）
# read_tags(path) -> TagData: 分派解析（未知格式直接降级；任何异常捕获降级，不崩溃）
# read_tags_batch(paths) -> list[TagData]: 批量（逐曲降级，数量与输入一致）
#   关联配置：无（格式支持集合与播放解码器注册表对齐，见 utils/file_utils.AUDIO_EXTENSIONS）
