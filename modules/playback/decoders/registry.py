# 解码器注册表（A9.4）：扩展名 → 探测链 → 解码器（audacious InputPlugin 模式）

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable


@dataclass
class DecoderEntry:
    # 解码器条目：扩展名集合 + 探测函数（文件头验证）+ 解码函数（第一版占位）
    extensions: tuple[str, ...]
    probe_fn: Callable[[Path], bool]
    decoder: Callable[[Path], Any]


# 注册表（扩展名小写 → 条目）
_registry: dict[str, DecoderEntry] = {}

# 装配标记（懒装配：首次 resolve 前注册全部内置格式模块）
_loaded = False


def _ensure_loaded() -> None:
    # 懒装配：注册内置四格式（mp3/flac/wav/m4a）；新格式 = 模块 + 在此注册
    global _loaded
    if _loaded:
        return
    from modules.playback.decoders import flac, m4a, mp3, wav

    for mod in (mp3, flac, wav, m4a):
        register(mod.EXTENSIONS, mod.probe, mod.decoder)
    _loaded = True


def register(
    extensions: tuple[str, ...],
    probe_fn: Callable[[Path], bool],
    decoder: Callable[[Path], Any],
) -> None:
    # 注册解码器：为每个扩展名建立索引（重复注册后覆盖）
    entry = DecoderEntry(extensions=extensions, probe_fn=probe_fn, decoder=decoder)
    for ext in extensions:
        _registry[ext.lower()] = entry


def resolve(path: str | Path) -> DecoderEntry | None:
    # 解析解码器：懒装配 → 扩展名索引 → 探测链（probe 验证真实格式）→ 返回条目；未注册/探测失败 None
    _ensure_loaded()
    ext = Path(path).suffix.lower()
    entry = _registry.get(ext)
    if entry is None:
        return None
    try:
        if entry.probe_fn(Path(path)):
            return entry
    except Exception:
        return None
    return None


# ===== modules/playback/decoders/registry.py 函数/常量说明 =====
# DecoderEntry(dataclass): 条目（扩展名/probe/decoder；decoder 第一版占位，实际走 QtMultimedia）
# _registry: 扩展名 → 条目索引
# register(extensions, probe_fn, decoder): 注册（多扩展名一次注册）
# resolve(path) -> DecoderEntry | None: 解析
#   逻辑：扩展名小写查索引 → probe 验证（文件头魔数）→ 命中返回条目
#   异常：probe 异常返回 None（降级，不崩溃）
#   设计理由：新格式 = 加一个模块（EXTENSIONS/probe/decoder）+ 注册（audacious 模式）
#   关联配置：格式模块 mp3/flac/wav/m4a（本包内，由装配处注册）
