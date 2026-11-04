# 应用静态配置加载模块（A1.1/B2.2/B2.4/D0.1）：config/static/ 只读 json 驱动，模块级缓存单例，坏 JSON 容错降级

import json
import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Any

# 静态配置目录（__file__ 自定位；本层不依赖 utils，避免 utils/logger → config 循环）
STATIC_DIR = Path(__file__).resolve().parent

# 模块级日志（utils.logger 依赖本模块，故此处用标准库；告警不打断加载）
_logger = logging.getLogger(__name__)

# 合法日志级别值域（D0.2：log_level 值域校验，小写/非法级别名导入即崩）
_VALID_LOG_LEVELS = frozenset(logging._nameToLevel.keys())

# 数值键白名单（B2.4/C0.5/E0.1：加载后逐键校验类型，非法 → 移除键 + 告警，消费点回退默认）
_NUMERIC_BASE_KEYS = ("sample_rate", "channels")
_NUMERIC_UI_KEYS = (
    "window_width",
    "window_height",
    "thumbnail_size",
    "record_widget_size",
    "deck_widget_size",
    "spin_tick_ms",
    "progress_interval_ms",
    "drag_threshold",
)

# 字符串键白名单（C0.5：log_level/music_dir 等非字符串会导致导入即崩）
_STRING_BASE_KEYS = (
    "version",
    "app_name",
    "music_dir",
    "data_dir",
    "logs_dir",
    "log_level",
)
_STRING_UI_KEYS = ("font_family", "cover_image_filter")

# 拟真度默认档位回退字面量（C2.4 单源：effects.json 缺 default_level 时的统一回退值）
DEFAULT_REALISM_LEVEL = "refined"


def _fallback_level() -> str:
    # 默认档位回退（F0.6）：字面量不在 levels 时取 levels 首键，避免回退链自引用写无效档位
    levels = get_static_config().effects.get("levels", {})
    if isinstance(levels, dict) and DEFAULT_REALISM_LEVEL in levels:
        return DEFAULT_REALISM_LEVEL
    if isinstance(levels, dict) and levels:
        return next(iter(levels))
    return DEFAULT_REALISM_LEVEL


# 容器内部数值键白名单（D0.1：animation.record_spin_ms 等嵌套数值键递归校验；
# card_size=None 表示 list 容器元素全数值校验）
_NESTED_NUMERIC = {
    "animation": ("record_spin_ms", "tonearm_drop_ms"),
    "card_size": None,
}


@dataclass
class StaticConfig:
    # 应用静态配置聚合（各分类 dict 只读；坏文件对应分类为空 dict，调用方自行降级）
    base: dict[str, Any]
    item_types: dict[str, Any]
    effects: dict[str, Any]
    ui: dict[str, Any]


def _read_json(rel_path: str) -> dict[str, Any]:
    # 读单个静态配置文件：缺失/坏 JSON/非对象结构均返回空 dict 并告警（不崩溃，宽容降级）
    try:
        data = json.loads((STATIC_DIR / rel_path).read_text(encoding="utf-8"))
        if isinstance(data, dict):
            return data
        _logger.warning("静态配置结构非法（应为对象）: %s", rel_path)
    except Exception:
        _logger.warning("静态配置读取失败（缺失或损坏）: %s", rel_path)
    return {}


def _sanitize_types(
    data: dict[str, Any],
    numeric_keys: tuple[str, ...] = (),
    string_keys: tuple[str, ...] = (),
    dict_keys: tuple[str, ...] = (),
    list_keys: tuple[str, ...] = (),
    nested_numeric: dict[str, tuple[str, ...] | None] | None = None,
    valid_values: dict[str, frozenset] | None = None,
    values_must_be_dict: bool = False,
) -> dict[str, Any]:
    # B2.4/C0.5/D0.1 类型校验：白名单数值/字符串/字典/列表键、嵌套数值、值域、值全 dict 校验
    # 非法（含 null）→ 移除键 + 告警（消费点回退默认，不崩溃）
    result = dict(data)

    def _drop(key, value):
        _logger.warning("静态配置键类型非法（已移除，回退默认）: %s = %r", key, value)
        result.pop(key, None)

    for key in numeric_keys:
        value = result.get(key)
        # F3.2：数值键统一 >0 下界（0/负值无业务意义：尺寸/阈值/间隔/时长）
        if (
            value is None
            or (type(value) is not int and not isinstance(value, float))
            or value <= 0
        ):
            _drop(key, value)
    for key in string_keys:
        value = result.get(key)
        if value is None or not isinstance(value, str):
            _drop(key, value)
    for key in dict_keys:
        value = result.get(key)
        if value is None or not isinstance(value, dict):
            _drop(key, value)
    for key in list_keys:
        value = result.get(key)
        if value is None or not isinstance(value, list):
            _drop(key, value)
    for key, valid in (valid_values or {}).items():
        value = result.get(key)
        if value is not None and value not in valid:
            _drop(key, value)
    for container, inner in (nested_numeric or {}).items():
        cv = result.get(container)
        if inner is None:
            # list 容器：元素数值过滤后须保持长度契约（E0.2：card_size 恒 2 元素，否则整键移除）
            if isinstance(cv, list):
                filtered = [
                    v
                    for v in cv
                    if v is not None
                    and (type(v) is int or isinstance(v, float))
                    and v > 0  # F1.1：元素 >0
                ]
                if len(filtered) == 2:
                    result[container] = filtered
                else:
                    _logger.warning(
                        "静态配置列表键元素非法或长度不符（已移除，回退默认）: %s = %r",
                        container,
                        cv,
                    )
                    result.pop(container, None)
            continue
        if isinstance(cv, dict):
            for key in inner:
                value = cv.get(key)
                if (
                    value is None
                    or (type(value) is not int and not isinstance(value, float))
                    or value <= 0  # E0.3：时长类数值 >0 下界（防除零）
                ):
                    if key in cv:
                        _logger.warning(
                            "静态配置嵌套数值键类型非法或非正（已移除，回退默认）: %s.%s = %r",
                            container,
                            key,
                            value,
                        )
                        cv.pop(key, None)
    if values_must_be_dict:
        for key in list(result.keys()):
            if not isinstance(result[key], dict):
                _drop(key, result[key])
    return result


def _load_static_config() -> StaticConfig:
    # 私有加载：读引导映射表 → 按四分类逐个加载 → 类型校验 → 聚合；映射缺失键对应分类置空 dict 并告警
    mapping = _read_json("config.json")
    result = StaticConfig(base={}, item_types={}, effects={}, ui={})
    for key in ("base", "item_types", "effects", "ui"):
        rel_path = mapping.get(key)
        if isinstance(rel_path, str):
            data = _read_json(rel_path)
            if key == "base":
                data = _sanitize_types(
                    data,
                    numeric_keys=_NUMERIC_BASE_KEYS,
                    string_keys=_STRING_BASE_KEYS,
                    valid_values={"log_level": _VALID_LOG_LEVELS},
                )
            elif key == "ui":
                data = _sanitize_types(
                    data,
                    numeric_keys=_NUMERIC_UI_KEYS,
                    string_keys=_STRING_UI_KEYS,
                    dict_keys=("animation", "colors"),
                    list_keys=("card_size",),
                    nested_numeric=_NESTED_NUMERIC,
                )
            elif key == "effects":
                data = _sanitize_types(
                    data, string_keys=("default_level",), dict_keys=("levels",)
                )
                # E0.7：default_level 必须 ∈ levels 键（否则移除回退默认）
                levels = data.get("levels")
                dl = data.get("default_level")
                if (
                    isinstance(levels, dict)
                    and isinstance(dl, str)
                    and dl not in levels
                ):
                    _logger.warning(
                        "default_level 不在 levels 键中（已移除，回退默认）: %s", dl
                    )
                    data.pop("default_level", None)
                if not isinstance(levels, dict) and "default_level" in data:
                    # F0.6：levels 缺失/非 dict 时 default_level 一并移除（防回退链自引用写无效档位）
                    _logger.warning(
                        "levels 缺失时 default_level 一并移除（防无效档位）"
                    )
                    data.pop("default_level", None)
            elif key == "item_types":
                data = _sanitize_types(data, values_must_be_dict=True)
                # E0.6/F0.5：记录内字段校验（minutes_per_side 数值、side list 且元素 ∈ A/B），非法移除记录
                for type_key, rec in list(data.items()):
                    if not isinstance(rec, dict):
                        continue
                    mp = rec.get("minutes_per_side")
                    if (
                        mp is None
                        or (type(mp) is not int and not isinstance(mp, float))
                        or mp <= 0
                    ):
                        # F1.1：minutes_per_side >0 下界（0 容量 → 生成静默失效）
                        _logger.warning(
                            "载体类型记录数值非法（已移除）: %s.minutes_per_side = %r",
                            type_key,
                            mp,
                        )
                        data.pop(type_key, None)
                        continue
                    sides = rec.get("side")
                    if (
                        not isinstance(sides, list)
                        or not sides
                        or not all(s in ("A", "B") for s in sides)
                    ):
                        _logger.warning(
                            "载体类型记录 side 非法（已移除）: %s.side = %r",
                            type_key,
                            sides,
                        )
                        data.pop(type_key, None)
                        continue
                    # H2：spin_ms_per_rev 可选数值键（>0 下界），非法移除键保留记录（from_config 回退默认）
                    spin = rec.get("spin_ms_per_rev")
                    if spin is not None and (
                        (type(spin) is not int and not isinstance(spin, float))
                        or spin <= 0
                    ):
                        _logger.warning(
                            "载体类型记录 spin_ms_per_rev 非法（已移除键，回退默认）: %s = %r",
                            type_key,
                            spin,
                        )
                        rec.pop("spin_ms_per_rev", None)
            setattr(result, key, data)
        else:
            _logger.warning("静态配置映射缺少分类: %s", key)
    return result


_static_config_cache: StaticConfig | None = None


def get_static_config() -> StaticConfig:
    # 公开单例访问：缓存懒加载，首次调用后不再读文件；模块顶层 _SC = get_static_config() 解包
    global _static_config_cache
    if _static_config_cache is None:
        _static_config_cache = _load_static_config()
    return _static_config_cache


# ===== config/static/static_config.py 函数/常量说明 =====
# STATIC_DIR: 静态配置目录（__file__ 自定位；本层不依赖 utils，避免 utils/logger → config 循环，B2.2）
# _NUMERIC_BASE_KEYS / _NUMERIC_UI_KEYS: 数值键白名单（B2.4 类型校验；E0.1 补 drag_threshold）
# _STRING_BASE_KEYS / _STRING_UI_KEYS: 字符串键白名单（C0.5：log_level/music_dir 等非字符串导入即崩）
# _VALID_LOG_LEVELS: 合法日志级别值域（D0.2：log_level 值域校验）
# _NESTED_NUMERIC: 容器内部数值键白名单（D0.1/E0.2/E0.3：animation 嵌套数值 >0 下界、card_size 长度契约）
# DEFAULT_REALISM_LEVEL: 拟真度默认档位回退字面量（C2.4 单源）
# StaticConfig(dataclass): 静态配置聚合（base/item_types/effects/ui 四个 dict 字段，只读）
# _read_json(rel_path) -> dict: 读单文件
#   逻辑：json 加载 → 非 dict 或解析失败返回空 dict
#   异常：一切异常捕获后告警返回空（不崩溃；与 AGENTS.md 宽容解析策略一致）
# _sanitize_types(data, numeric_keys, string_keys, dict_keys, list_keys, nested_numeric,
#                 valid_values, values_must_be_dict) -> dict: B2.4-C0.5-D0.1-E0.x 类型校验
#   逻辑：数值/字符串/字典/列表白名单 + 嵌套数值（>0 下界与长度契约）+ 值域 + 值全 dict 校验，
#     非法（含 null）→ 移除键 + 告警（消费点回退默认，不崩溃）
# _load_static_config() -> StaticConfig: 私有加载
#   逻辑：读 config.json 映射表 → 四分类加载 → 各自类型校验（base 值域、ui 嵌套、
#     effects default_level 值域 E0.7、item_types 记录内数值 E0.6 + spin_ms_per_rev H2）→ 聚合
#   设计理由：映射表驱动（config.json 是唯一引导），键集合为契约层显式声明
# get_static_config() -> StaticConfig: 公开单例访问（缓存懒加载，进程内只读一次）
#   关联配置：config/static/config.json 映射表 + base/item_types/effects/ui 四 json
