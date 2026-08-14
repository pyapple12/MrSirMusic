# 物品工厂函数（A3.5）：创建物品 / 向面加曲目（含容量校验）/ 按序号移除曲目

from modules.items.model import Item, ItemType, Side, Track


def create_item(name: str, type: ItemType, tag: str) -> Item:
    # 创建空物品：按载体类型的面集合初始化各面（每个面一个空 Side）
    item = Item(name=name, type=type, tag=tag)
    for label in type.sides:
        item.sides[label] = Side(label=label)
    return item


def add_track_to_side(item: Item, side_label: str, track: Track) -> tuple[bool, str]:
    # 向指定面加曲目：单面容量校验（超出拒绝并返回中文原因）；成功追加返回 (True, "")
    side = item.side_for(side_label)
    if side is None:
        return False, f"物品不存在面 {side_label}"
    max_seconds = item.type.minutes_per_side * 60
    if side.total_seconds() + track.duration_seconds > max_seconds:
        return False, f"超出单面容量（{item.type.minutes_per_side} 分钟）"
    side.add_track(track)
    return True, ""


def remove_track(item: Item, side_label: str, index: int) -> bool:
    # 按序号从指定面移除曲目：序号越界返回 False，成功移除返回 True
    side = item.side_for(side_label)
    if side is None or not (0 <= index < len(side.tracks)):
        return False
    del side.tracks[index]
    return True


# ===== modules/items/factory.py 函数说明 =====
# create_item(name, type, tag) -> Item: 创建空物品（面初始化：按 type.sides 建空 Side）
# add_track_to_side(item, side_label, track) -> (bool, str): 加曲目
#   逻辑：面存在性 → 容量计算（minutes_per_side*60）→ 超出拒绝/成功追加
#   设计理由：容量校验内联（A5.1 capacity.py 建成后由生成流程统一走规则引擎，此入口保留）
#   返回：成功 (True, "")；失败 (False, 中文原因)
# remove_track(item, side_label, index) -> bool: 按序号移除（越界/面缺失返回 False）
#   关联配置：容量上限来自 ItemType.minutes_per_side（item_types.json 装配）
