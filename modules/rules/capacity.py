# 容量规则模块（A5.1）：单曲适配校验（先加后比口径唯一实现）

from modules.items.model import ItemType, Side, Track
from utils.convert import format_duration


def fits(side: Side, track: Track, item_type: ItemType) -> tuple[bool, str]:
    # 单曲适配校验：先加后比（与 allocate/add_track_to_side 同口径，防浮点边界判定不一致）
    max_seconds = item_type.minutes_per_side * 60
    if side.total_seconds() + track.duration_seconds > max_seconds:
        return False, (
            f"曲目《{track.title}》时长 {format_duration(track.duration_seconds)}"
            f"超出剩余容量 {format_duration(max_seconds - side.total_seconds())}"
        )
    return True, ""


# ===== modules/rules/capacity.py 函数说明 =====
# fits(side, track, item_type) -> (bool, str): 适配校验
#   逻辑：track.duration_seconds > remaining → 拒绝（原因含曲名/时长/剩余容量）
#   边界：恰好相等通过（== 不拒绝）；超出 1 秒拒绝；长曲（超单面总量）拒绝
#   设计理由：规则引擎单一入口，A8 生成流程/A3.5 工厂均可引用，原因带中文提示；
#     remaining_seconds 已移除（FIX006.13：零调用方死代码，调用方均自算 total > max 同口径）
#   关联配置：容量来自 ItemType.minutes_per_side（item_types.json 装配）
