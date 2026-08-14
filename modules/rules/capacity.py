# 容量规则模块（A5.1）：单面剩余容量计算与单曲适配校验

from modules.items.model import ItemType, Side, Track
from utils.convert import format_duration


def remaining_seconds(side: Side, item_type: ItemType) -> float:
    # 计算单面剩余容量（秒）：面容量 - 已有曲目总时长
    return item_type.minutes_per_side * 60 - side.total_seconds()


def fits(side: Side, track: Track, item_type: ItemType) -> tuple[bool, str]:
    # 单曲适配校验：剩余容量够则 (True, "")；不够返回 (False, 中文原因)
    remaining = remaining_seconds(side, item_type)
    if track.duration_seconds > remaining:
        return False, (
            f"曲目《{track.title}》时长 {format_duration(track.duration_seconds)}"
            f"超出剩余容量 {format_duration(remaining)}"
        )
    return True, ""


# ===== modules/rules/capacity.py 函数说明 =====
# remaining_seconds(side, item_type) -> float: 剩余容量（面容量 - 已有时长；可负，超载态）
# fits(side, track, item_type) -> (bool, str): 适配校验
#   逻辑：track.duration_seconds > remaining → 拒绝（原因含曲名/时长/剩余容量）
#   边界：恰好相等通过（== 不拒绝）；超出 1 秒拒绝；长曲（超单面总量）拒绝
#   设计理由：规则引擎单一入口，A8 生成流程/A3.5 工厂均可引用，原因带中文提示
#   关联配置：容量来自 ItemType.minutes_per_side（item_types.json 装配）
