# 封面提供器注册表（A7.1/B3.9）：名称→实例注册表，按 item.cover_source 解析
# （FIX006.14：基类与 COVERS_DIR 下沉 cover/base.py 断环；此处 re-export 保持既有导入路径兼容）

from threading import Lock

from modules.cover.base import COVERS_DIR, CoverProvider  # noqa: F401 (re-export)
from modules.items.model import Item


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
# COVERS_DIR / CoverProvider: 自 cover/base.py re-export（FIX006.14 断环；既有 from providers import 兼容）
# _registry: 注册表缓存（None=未装配，懒构建）
# _build_registry() -> dict: 装配 local/placeholder；network 预留位注释（z.plan 留接口未实现）
# get_provider(name) -> CoverProvider | None: 按名取实例（懒装配）
# resolve_cover(item) -> str | None: 按 cover_source 解析封面（provider 缺失 → None）
#   设计理由：注册表模式让新封面源 = 加一个 provider 类 + 注册一行（对齐解码器注册表思路）；
#     基座（基类/目录常量）在 cover/base.py，本模块只管注册表装配（FIX006.14）
#   关联配置：COVERS_DIR 由 base.json music_dir 装配（装配逻辑在 cover/base.py）
