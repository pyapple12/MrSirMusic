# 封面模块基座（FIX006.14 断环下沉）：COVERS_DIR 常量 + CoverProvider 抽象基类
# 叶模块（零反向依赖）——providers 注册表与 local/placeholder 提供器共同自此处引用，
# 消除 providers ↔ local_provider 的循环依赖（A006-P3-⑩）

from abc import ABC, abstractmethod
from pathlib import Path

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


# ===== modules/cover/base.py 常量/类说明 =====
# COVERS_DIR: 封面实体目录（music/covers/，music_dir 来自 base.json；gitignore 内容保留目录）
# CoverProvider(ABC): 提供器基类（get_cover 抽象方法，返回本地路径或 None）
#   设计理由：常量与基类是无依赖的"叶"，原居 providers.py 致 local_provider（顶层引 COVERS_DIR）
#     与 providers（函数内延迟引 LocalProvider）成环——下沉后各引各的，环消（FIX006.14）
#   关联配置：base.json music_dir
