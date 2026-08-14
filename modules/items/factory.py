# 物品工厂函数（A3.5）：创建物品 / 向面加曲目（含容量校验）/ 按序号移除曲目

from modules.items.model import Item, ItemType, Side, Track


def create_item(name: str, type: ItemType, tag: str) -> Item:
    # 创建空物品：按载体类型的面集合初始化各面（每个面一个空 Side）
    item = Item(name=name, type=type, tag=tag)
    for label in type.sides:
        item.sides[label] = Side(label=label)
    return item


def remove_track(item: Item, side_label: str, index: int) -> bool:
    # 按序号从指定面移除曲目：序号越界返回 False，成功移除返回 True
    side = item.side_for(side_label)
    if side is None or not (0 <= index < len(side.tracks)):
        return False
    del side.tracks[index]
    return True


# ===== modules/items/factory.py 函数说明 =====
# create_item(name, type, tag) -> Item: 创建空物品（面初始化：按 type.sides 建空 Side）
# remove_track(item, side_label, index) -> bool: 按序号移除（越界/面缺失返回 False）
#   注：加曲容量校验统一走 modules/rules/capacity（B3.1 已删除重复的内联实现）
#   关联配置：容量上限来自 ItemType.minutes_per_side（item_types.json 装配）
