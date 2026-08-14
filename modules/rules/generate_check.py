# 生成前完整性校验模块（A5.4）：物品非空 / 各面不超载 / 封面可解析

from modules.items.model import Item


def _cover_resolvable(item: Item) -> bool:
    # 封面可解析判定：placeholder 模式无需实体路径（A7 兜底占位图）；local 模式要求 cover_path 非空
    if item.cover_source == "placeholder":
        return True
    return bool(item.cover_path)


def check_item(item: Item) -> list[str]:
    # 生成前完整性检查：返回问题列表（空 = 通过）；问题：空物品 / 面超载 / 封面不可解析
    problems: list[str] = []
    if not item.all_tracks():
        problems.append("物品为空（无任何曲目）")
    for label, side in item.sides.items():
        max_seconds = item.type.minutes_per_side * 60
        if side.total_seconds() > max_seconds:
            problems.append(
                f"{label} 面超载（超出 {item.type.minutes_per_side} 分钟容量）"
            )
    if not _cover_resolvable(item):
        problems.append("封面不可解析（local 模式缺少封面路径）")
    return problems


# ===== modules/rules/generate_check.py 函数说明 =====
# _cover_resolvable(item) -> bool: 封面可解析判定（placeholder 免路径；local 要求路径）
# check_item(item) -> list[str]: 生成前完整性校验
#   逻辑：三项检查（空物品 / 各面 total > 容量 / 封面），逐项收集问题，空列表 = 通过
#   异常：无（纯计算，不抛）
#   设计理由：生成（A8）/编辑（A8.3）入库前统一把关，UI 提示友好
#   关联配置：面容量来自 ItemType.minutes_per_side；封面语义见 modules/cover（A7）
