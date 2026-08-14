# 占位封面提供器（A7.3/B2.1）：无封面时返回 data/placeholder.png（缓存兜底，不显示空白）

from config.static.static_config import get_static_config
from modules.cover.providers import CoverProvider
from modules.items.model import Item
from utils.paths import project_root

# 占位图路径（data/ 静态资源，随包发布；目录走 base.json data_dir）
PLACEHOLDER_PATH = (
    project_root()
    / get_static_config().base.get("data_dir", "data")
    / "placeholder.png"
)


class PlaceholderProvider(CoverProvider):
    # 占位封面提供器：返回 data/placeholder.png 路径（文件缺失返回 None，调用方按无封面处理）

    def get_cover(self, item: Item) -> str | None:
        # 返回占位图路径（文件存在才返回）
        if PLACEHOLDER_PATH.is_file():
            return str(PLACEHOLDER_PATH)
        return None


# ===== modules/cover/placeholder_provider.py 函数/类说明 =====
# PLACEHOLDER_PATH: 占位图路径（data/placeholder.png，静态资源入库）
# PlaceholderProvider(CoverProvider): 占位提供器
#   get_cover(item): 文件存在返回路径；缺失返回 None（不崩溃，UI 按无封面显示）
#   设计理由：封面获取失败回退占位图不显示空白（AGENTS.md 缓存兜底策略）
#   关联配置：无（路径固定 data/ 下，随项目发布）
