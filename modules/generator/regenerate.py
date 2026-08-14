# 重新刻录模块（A8.2）：复用原歌池按策略重新分配，生成新 id 物品并入库

from modules.generator.generator import GenerateError
from modules.items.factory import create_item
from modules.items.model import Item
from modules.library.repository import save_item
from modules.rules.side_allocator import ALLOC_STRATEGY, allocate


def regenerate(item: Item, strategy: str | None = None) -> Item:
    # 重新刻录：复用原曲目 path 列表重新分配（策略预留，None → 默认策略），生成新 id 物品并入库
    use_strategy = strategy or ALLOC_STRATEGY
    if use_strategy != "sequential":
        raise GenerateError(f"不支持的分配策略：{use_strategy}")
    tracks = list(item.all_tracks())
    new_item = create_item(item.name, item.type, item.tag)
    new_item.cover_source = item.cover_source
    new_item.cover_path = item.cover_path
    sides_data = allocate(tracks, item.type)
    for label, side_tracks in sides_data.items():
        side = new_item.side_for(label)
        if side is not None:
            side.tracks = list(side_tracks)
    save_item(new_item)
    return new_item


# ===== modules/generator/regenerate.py 函数说明 =====
# regenerate(item, strategy) -> Item: 重新刻录
#   逻辑：原 all_tracks 作为歌池 → 按策略（仅 sequential，其他抛 GenerateError）重新分配
#     → 新 id 物品（继承 name/type/tag/封面）→ 入库 → 返回
#   异常：未知策略抛 GenerateError（业务分类异常）
#   设计理由：旧物品保留（重新刻录产生新物品，不覆盖原物品——A8.2 定案）
#   关联配置：分配策略常量 ALLOC_STRATEGY（rules/side_allocator.py）
