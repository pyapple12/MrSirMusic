# 封面提供器注册表（A7.1/B3.9）：CoverProvider 基类 + 名称→实例注册表，按 item.cover_source 解析

from abc import ABC, abstractmethod
from pathlib import Path
from threading import Lock

from config.static.static_config import get_static_config
from modules.items.model import Item

# 封面实体目录（music/covers/，music_dir 来自 base.json）
COVERS_DIR = (
    Path(__file__).resolve().parent.parent.parent
    / get_static_config().base.get("music_dir", "music")
    / "covers"
)


class CoverProvider(ABC):
    # 封面提供器基类：get_cover(item) 返回本地封面路径或 None（无封面时由占位图兜底）

    @abstractmethod
    def get_cover(self, item: Item) -> str | None:
        # 抽象方法：按 item 返回封面本地路径（子类实现）
        raise NotImplementedError


# 注册表缓存（懒装配，B3.9 加锁防并发首调竞态）
_registry: dict[str, CoverProvider] | None = None
_registry_lock = Lock()


def _build_registry() -> dict[str, CoverProvider]:
    # 装配注册表：local/placeholder 已实现；network 预留位（网络封面未实现，后续 provider 加入）
    from modules.cover.local_provider import LocalProvider
    from modules.cover.placeholder_provider import PlaceholderProvider

    return {
        "local": LocalProvider(),
        "placeholder": PlaceholderProvider(),
        # "network": NetworkProvider(),  # 预留：网络封面（未实现）
    }


def get_provider(name: str) -> CoverProvider | None:
    # 按名称取提供器实例（懒装配 + 双重检查锁，B3.9；未注册返回 None）
    global _registry
    if _registry is None:
        with _registry_lock:
            if _registry is None:
                _registry = _build_registry()
    return _registry.get(name)


def resolve_cover(item: Item) -> str | None:
    # 按 item.cover_source 选择提供器取封面路径；provider 缺失或返回 None → 无封面
    provider = get_provider(item.cover_source)
    if provider is None:
        return None
    return provider.get_cover(item)


# ===== modules/cover/providers.py 函数/常量说明 =====
# COVERS_DIR: 封面实体目录（music/covers/，music_dir 来自 base.json；gitignore 内容保留目录）
# CoverProvider(ABC): 提供器基类（get_cover 抽象方法，返回本地路径或 None）
# _registry: 注册表缓存（None=未装配，懒构建）
# _build_registry() -> dict: 装配 local/placeholder；network 预留位注释（z.plan 留接口未实现）
# get_provider(name) -> CoverProvider | None: 按名取实例（懒装配）
# resolve_cover(item) -> str | None: 按 cover_source 解析封面（provider 缺失 → None）
#   设计理由：注册表模式让新封面源 = 加一个 provider 类 + 注册一行（对齐解码器注册表思路）
#   关联配置：COVERS_DIR 由 base.json music_dir 装配
