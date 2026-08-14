# 用户配置模块（A1.7）：AppConfig dataclass + config/user_config.json 读写，缺省回退，坏 JSON 不崩溃，变更回调

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable

# 用户配置文件路径（项目内，随项目模式；已 gitignore）
USER_CONFIG_PATH = (
    Path(__file__).resolve().parent.parent / "config" / "user_config.json"
)


@dataclass
class AppConfig:
    # 用户可调配置聚合：拟真度档位 + 自动翻面（缺省即默认值）
    realism_level: str = "refined"
    auto_flip: bool = False


# 变更通知回调注册表（保存后逐个调用，参数为新配置）
_changed_listeners: list[Callable[[AppConfig], None]] = []


def load_config() -> AppConfig:
    # 读取用户配置：字段逐项宽容解析（类型不符/缺失回退默认），坏 JSON/缺文件返回默认配置，不崩溃
    cfg = AppConfig()
    try:
        data: Any = json.loads(USER_CONFIG_PATH.read_text(encoding="utf-8"))
    except Exception:
        return cfg
    if not isinstance(data, dict):
        return cfg
    if isinstance(data.get("realism_level"), str):
        cfg.realism_level = data["realism_level"]
    if isinstance(data.get("auto_flip"), bool):
        cfg.auto_flip = data["auto_flip"]
    return cfg


def save_config(cfg: AppConfig) -> None:
    # 保存用户配置（覆盖写）并触发变更回调；写失败不抛出（下次启动回退默认，不崩溃）
    try:
        USER_CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
        USER_CONFIG_PATH.write_text(
            json.dumps(
                {"realism_level": cfg.realism_level, "auto_flip": cfg.auto_flip},
                ensure_ascii=False,
                indent=2,
            ),
            encoding="utf-8",
        )
    except Exception:
        return
    for cb in _changed_listeners:
        try:
            cb(cfg)
        except Exception:
            pass


def add_change_listener(callback: Callable[[AppConfig], None]) -> None:
    # 注册变更回调（保存配置后触发，参数为新 AppConfig）
    _changed_listeners.append(callback)


# ===== config/settings.py 函数/常量说明 =====
# USER_CONFIG_PATH: 用户配置文件路径（config/user_config.json，gitignore；随项目模式）
# AppConfig(dataclass): 用户可调配置（realism_level 拟真度档位 / auto_flip 自动翻面）
# _changed_listeners: 变更回调注册表（模块级列表，保存后逐个调用）
# load_config() -> AppConfig: 读取配置
#   逻辑：json 读取 → 逐字段类型校验（宽容解析：字符串/bool 不符回退默认）→ 返回
#   异常：坏 JSON/缺文件/非对象 → 返回默认配置（不崩溃，AGENTS.md 宽容解析）
# save_config(cfg) -> None: 保存配置
#   逻辑：目录确保 → json 覆盖写（UTF-8）→ 触发全部变更回调
#   异常：写失败静默返回（下次启动回退默认）；回调异常单独捕获不影响其他回调
# add_change_listener(callback) -> None: 注册变更回调（保存成功后触发）
#   关联配置：config/user_config.json（运行时生成，已 gitignore）
