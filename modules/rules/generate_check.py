# 生成前完整性校验模块（A5.4）：物品非空 / 面序成立 / 各面不超载 / 封面可解析

from modules.items.model import Item


def _cover_resolvable(item: Item) -> bool:
    # 封面可解析判定：placeholder 模式无需实体路径（A7 兜底占位图）；local 模式要求 cover_path 非空
    if item.cover_source == "placeholder":
        return True
    return bool(item.cover_path)


def check_item(item: Item) -> list[str]:
    # 生成前完整性检查：返回问题列表（空 = 通过）；
    # 问题：空物品 / 面序不成立（PATCH004：A 空而其他面有曲）/ 面超载 / 封面不可解析
    problems: list[str] = []
    if not item.all_tracks():
        problems.append("物品为空（无任何曲目）")
    non_empty_sides = [label for label, side in item.sides.items() if side.tracks]
    if non_empty_sides and "A" not in non_empty_sides:
        # 拟物面序（PATCH004 用户拍板）：有曲面必须从 A 开始——A 空而 B 有曲物理上不成立
        # （生成端顺序分配器先填 A 造不出该态，此处拦编辑/未来写链路径；engine 侧 F3.1
        # 已容忍该态不崩，本规则是语义层把关而非崩溃防御）
        problems.append("A 面为空而其他面有曲（面序不成立）")
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
#   逻辑：四项检查（空物品 / 面序 / 各面 total > 容量 / 封面），逐项收集问题，空列表 = 通过
#   异常：无（纯计算，不抛）
#   设计理由：生成（A8）/编辑（A8.3）入库前统一把关，UI 提示友好；面序拦截为 PATCH004
#     用户拍板（A006 观察项转正）——保持拟物"先 A 后 B"语义，编辑删空 A 面被拒绝回滚
#   关联配置：面容量来自 ItemType.minutes_per_side；封面语义见 modules/cover（A7）
