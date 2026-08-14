# AB 面分配模块（A5.2）：第一版顺序填充（按添加顺序填 A 面，满后填 B 面），策略参数预留

from modules.items.model import ItemType, Track

# 分配策略（第一版仅 sequential；后续可加 balanced 平分 / manual 手动）
ALLOC_STRATEGY = "sequential"


def allocate(tracks: list[Track], item_type: ItemType) -> dict[str, list[Track]]:
    # 按顺序填充各面：每首曲目从 A 面开始尝试，放不下换下一面；单曲超单面总量跳过（不入任何面）
    max_seconds = item_type.minutes_per_side * 60
    labels = list(item_type.sides)
    result: dict[str, list[Track]] = {label: [] for label in labels}
    for track in tracks:
        for label in labels:
            side_total = sum(t.duration_seconds for t in result[label])
            if side_total + track.duration_seconds <= max_seconds:
                result[label].append(track)
                break
    return result


# ===== modules/rules/side_allocator.py 函数/常量说明 =====
# ALLOC_STRATEGY: 分配策略常量（sequential 顺序填充；未来扩展 balanced/manual 时切换分支）
# allocate(tracks, item_type) -> dict[str, list[Track]]: 顺序填充
#   逻辑：逐曲找当前面（容量够则入面，不够换下一面）；所有面放不下（长曲）跳过
#   设计理由：第一版固定顺序填充（任务定案）；策略常量作为扩展点避免重构
#   关联配置：面容量来自 ItemType.minutes_per_side；面集合来自 ItemType.sides
