# 重新刻录模块（A8.2/G 系列）：复用原歌池按策略重新分配，生成新 id 物品并入库

from modules.generator.generator import GenerateError
from modules.items.factory import create_item
from modules.items.model import Item
from modules.library.repository import save_item
from modules.rules.generate_check import check_item
from modules.rules.side_allocator import ALLOC_STRATEGY, allocate
from utils.logger import get_logger

# 模块日志（重刻丢弃/校验失败记录，FIX006.1）
_logger = get_logger("generator.regenerate")


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
    placed = 0
    for label, side_tracks in sides_data.items():
        side = new_item.side_for(label)
        if side is not None:
            side.tracks = list(side_tracks)
            placed += len(side_tracks)
    # FIX006.1（A006-P2-1）：与 generate 主流程同口径（G0.2）——分配丢弃曲目即中止，
    # 防 0 容量类型物品静默造空物品、容量缩水后静默丢歌
    if placed < len(tracks):
        dropped = len(tracks) - placed
        _logger.warning("重新刻录丢弃曲目 %d/%d，中止", dropped, len(tracks))
        raise GenerateError(f"重新刻录丢弃了 {dropped} 首曲目（载体容量不足），已取消")
    # FIX006.1（A006-P2-1）：入库前完整性校验（与 generate 主流程同口径，防空物品入库）
    problems = check_item(new_item)
    if problems:
        _logger.warning("重新刻录校验未通过: %s", "；".join(problems))
        raise GenerateError(f"重新刻录完整性校验未通过：{'；'.join(problems)}")
    save_item(new_item)
    return new_item


# ===== modules/generator/regenerate.py 函数说明 =====
# regenerate(item, strategy) -> Item: 重新刻录
#   逻辑：原 all_tracks 作为歌池 → 按策略（仅 sequential，其他抛 GenerateError）重新分配
#     → 丢弃检查（FIX006.1：placed < 总数抛 GenerateError，同 G0.2 口径）
#     → 完整性校验（FIX006.1：check_item 拦空物品）→ 新 id 物品（继承 name/type/tag/封面）→ 入库 → 返回
#   异常：未知策略/丢弃曲目/校验未通过均抛 GenerateError（业务分类异常，UI 分类提示）
#   设计理由：旧物品保留（重新刻录产生新物品，不覆盖原物品——A8.2 定案）
#   关联配置：分配策略常量 ALLOC_STRATEGY（rules/side_allocator.py）
