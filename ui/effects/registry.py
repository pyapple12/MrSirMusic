# 拟真度效果装配（A13.1）：按 effects.json 档位生成效果器实例列表，apply 接口

from typing import Any

from config.static.static_config import DEFAULT_REALISM_LEVEL, get_static_config
from ui.effects.wear import Effect, WearEffect, WeatheringEffect

# 静态配置一次解包
_SC = get_static_config()


def available_levels() -> list[str]:
    # 全部档位（effects.json levels 键，按声明顺序）
    levels = _SC.effects.get("levels", {}) if isinstance(_SC.effects, dict) else {}
    return list(levels.keys())


def default_level() -> str:
    # 默认档位（effects.json default_level；缺失回退单源常量，C2.4）
    return str(_SC.effects.get("default_level", DEFAULT_REALISM_LEVEL))


def animations_enabled(level: str) -> bool:
    # 档位动画开关（concise 关；缺失档位回退 False）
    rec = _level_config(level)
    if rec is None:
        return False
    return bool(rec.get("animations", False))


def _to_float(value: Any, default: float = 0.0) -> float:
    # 宽容数值转换（B3.16）：非数值/None 回退默认，不抛 TypeError
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def build_effects(level: str) -> list[Effect]:
    # 按档位装配效果器列表：wear → WearEffect(intensity)；weathering → WeatheringEffect(intensity)
    rec = _level_config(level)
    if rec is None:
        return []
    effects: list[Effect] = []
    if rec.get("wear"):
        effects.append(WearEffect(_to_float(rec.get("wear_intensity"))))
    if rec.get("weathering"):
        effects.append(WeatheringEffect(_to_float(rec.get("weathering_intensity"))))
    return effects


def apply(item_widget: Any, level: str) -> None:
    # 对物品控件应用档位：装配效果器并交给控件（set_effects 后控件绘制时叠加）
    item_widget.set_effects(build_effects(level))


def _level_config(level: str) -> dict | None:
    # 档位配置记录（levels[level]；缺失返回 None）
    levels = _SC.effects.get("levels", {}) if isinstance(_SC.effects, dict) else {}
    rec = levels.get(level)
    return rec if isinstance(rec, dict) else None


# ===== ui/effects/registry.py 函数/常量说明 =====
# _SC: 静态配置单例（effects.json）
# available_levels() -> list[str]: 档位列表（声明顺序）
# default_level() -> str: 默认档位（default_level 字段）
# animations_enabled(level) -> bool: 动画开关（concise 关）
# build_effects(level) -> list[Effect]: 装配效果器（wear/weathering 按强度；concise 空）
# apply(item_widget, level) -> None: 应用接口（set_effects）
# _level_config(level) -> dict | None: 档位配置记录（缺失 None）
#   设计理由：档位配置完全来自 effects.json（AGENTS.md 参数外置）；新效果项 = 配置 + 效果器类
#   关联配置：config/static/effects.json（levels/default_level/intensity）
