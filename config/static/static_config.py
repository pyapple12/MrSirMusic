# 应用静态配置加载模块（A1.1）：config/static/ 只读 json 驱动，模块级缓存单例，坏 JSON 容错降级

import json
import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Any

# 静态配置目录（__file__ 自定位）
STATIC_DIR = Path(__file__).resolve().parent

# 模块级日志（utils.logger 建成前用标准库，A2.1 后可统一）；告警不打断加载
_logger = logging.getLogger(__name__)


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


def _load_static_config() -> StaticConfig:
    # 私有加载：读引导映射表 → 按四分类逐个加载 → 聚合；映射缺失键对应分类置空 dict 并告警
    mapping = _read_json("config.json")
    result = StaticConfig(base={}, item_types={}, effects={}, ui={})
    for key in ("base", "item_types", "effects", "ui"):
        rel_path = mapping.get(key)
        if isinstance(rel_path, str):
            setattr(result, key, _read_json(rel_path))
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
# STATIC_DIR: 静态配置目录（__file__ 自定位，唯一路径来源）
# StaticConfig(dataclass): 静态配置聚合（base/item_types/effects/ui 四个 dict 字段，只读）
# _read_json(rel_path) -> dict: 读单文件
#   逻辑：json 加载 → 非 dict 或解析失败返回空 dict
#   异常：一切异常捕获后告警返回空（不崩溃；与 AGENTS.md 宽容解析策略一致）
# _load_static_config() -> StaticConfig: 私有加载
#   逻辑：读 config.json 映射表 → 按四分类键遍历加载（映射缺失键 → 空 dict + 告警）
#   设计理由：映射表驱动（config.json 是唯一引导），键集合为契约层显式声明
# get_static_config() -> StaticConfig: 公开单例访问（缓存懒加载，进程内只读一次）
#   关联配置：config/static/config.json 映射表 + base/item_types/effects/ui 四 json
