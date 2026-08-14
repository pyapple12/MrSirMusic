# 用户配置模块（A1.7/B2.6/C1.3）：AppConfig dataclass + config/user_config.json 读写，缺省回退，坏 JSON 不崩溃，变更回调

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable

from config.static.static_config import (
    DEFAULT_REALISM_LEVEL,
    _fallback_level,
    get_static_config,
)
from utils.logger import get_logger
from utils.paths import project_root

# 模块日志（保存失败/回调异常告警用，C1.3 顶部导入）
_logger = get_logger("settings")

# 用户配置文件路径（项目内，随项目模式；已 gitignore；C1.3 收敛 project_root 单点）
USER_CONFIG_PATH = project_root() / "config" / "user_config.json"


@dataclass
class AppConfig:
    # 用户可调配置聚合：拟真度档位（默认读 effects.json 单源，回退常量 C2.4）+ 自动翻面
    realism_level: str = field(
        default_factory=lambda: str(
            get_static_config().effects.get("default_level", _fallback_level())
        )
    )
    auto_flip: bool = False


# 变更通知回调注册表（保存后逐个调用，参数为新配置）
_changed_listeners: list[Callable[[AppConfig], None]] = []

# 档位白名单（effects.json levels 键；B3.4 非法档位回退默认）
_VALID_LEVELS = frozenset(get_static_config().effects.get("levels", {}).keys())

# 配置缓存（B3.12：load 懒加载，save 后失效；避免每次读文件）
_config_cache: AppConfig | None = None


def load_config() -> AppConfig:
    # 读取用户配置：缓存懒加载（B3.12）；字段宽容解析，坏 JSON/缺文件回退默认，不崩溃
    global _config_cache
    if _config_cache is None:
        _config_cache = _load_from_disk()
    return _config_cache


def _load_from_disk() -> AppConfig:
    # 磁盘读取（缓存未命中时调用）：字段逐项宽容解析 + 档位白名单校验（非法回退默认）
    cfg = AppConfig()
    try:
        data: Any = json.loads(USER_CONFIG_PATH.read_text(encoding="utf-8"))
    except Exception:
        return cfg
    if not isinstance(data, dict):
        return cfg
    if (
        isinstance(data.get("realism_level"), str)
        and data["realism_level"] in _VALID_LEVELS
    ):
        cfg.realism_level = data["realism_level"]
    if isinstance(data.get("auto_flip"), bool):
        cfg.auto_flip = data["auto_flip"]
    return cfg


def save_config(cfg: AppConfig) -> None:
    # 保存用户配置（覆盖写，档位非法回退默认）→ 失效缓存 → 触发变更回调；写失败不抛出
    global _config_cache
    level = (
        cfg.realism_level
        if cfg.realism_level in _VALID_LEVELS
        else str(get_static_config().effects.get("default_level", _fallback_level()))
    )
    try:
        USER_CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
        USER_CONFIG_PATH.write_text(
            json.dumps(
                {"realism_level": level, "auto_flip": cfg.auto_flip},
                ensure_ascii=False,
                indent=2,
            ),
            encoding="utf-8",
        )
    except Exception:
        _logger.warning("用户配置保存失败: %s", USER_CONFIG_PATH)
        return
    _config_cache = None
    for cb in _changed_listeners:
        try:
            cb(cfg)
        except Exception as exc:
            _logger.warning("配置变更回调异常（已隔离）: %s", exc)


def add_change_listener(callback: Callable[[AppConfig], None]) -> None:
    # 注册变更回调（保存配置后触发；C1.3 同一回调去重）
    if callback not in _changed_listeners:
        _changed_listeners.append(callback)


# ===== config/settings.py 函数/常量说明 =====
# USER_CONFIG_PATH: 用户配置文件路径（config/user_config.json，gitignore；project_root 收敛 C1.3）
# AppConfig(dataclass): 用户可调配置（realism_level 拟真度档位，默认读 effects.json 单源回退 _fallback_level / auto_flip 自动翻面）
# _changed_listeners: 变更回调注册表（模块级列表，保存后逐个调用；C1.3 去重）
# _VALID_LEVELS: 档位白名单（effects.json levels 键；B3.4 非法档位回退默认）
# _config_cache: 配置缓存（B3.12 懒加载，save 后失效）
# load_config() -> AppConfig: 读取配置
#   逻辑：缓存懒加载（B3.12）→ _load_from_disk 磁盘读取（宽容解析 + 档位白名单校验）
#   异常：坏 JSON/缺文件/非对象 → 返回默认配置（不崩溃，AGENTS.md 宽容解析）
# _load_from_disk() -> AppConfig: 磁盘读取（缓存未命中时调用）
#   逻辑：json 读取 → realism_level 白名单校验（非法回退默认）+ auto_flip bool 校验
# save_config(cfg) -> None: 保存配置
#   逻辑：目录确保 → 档位白名单校验（非法回退默认）→ json 覆盖写（UTF-8）→ 失效缓存 → 触发回调
#   异常：写失败日志告警（不抛出）；回调异常单独捕获不影响其他回调
# add_change_listener(callback) -> None: 注册变更回调（保存成功后触发；同一回调去重）
#   关联配置：config/user_config.json（运行时生成，已 gitignore）；effects.json（档位白名单）
