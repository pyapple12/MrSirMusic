# 编辑模块（A8.3）：加曲（实时容量校验）/移除/改名/改 Tag，均持久化

from modules.items.factory import remove_track as _remove_track
from modules.items.model import Item, Track
from modules.library.repository import save_item, update_item
from modules.rules.capacity import fits


def add_track(item: Item, side_label: str, track: Track) -> tuple[bool, str]:
    # 加曲：实时容量校验（A5.1 fits）→ 追加 → 完整持久化；失败返回 (False, 中文原因)
    side = item.side_for(side_label)
    if side is None:
        return False, f"物品不存在面 {side_label}"
    ok, reason = fits(side, track, item.type)
    if not ok:
        return False, reason
    side.add_track(track)
    save_item(item)
    return True, ""


def remove_track(item: Item, side_label: str, index: int) -> bool:
    # 按序号移除曲目（内存移除 + 完整持久化）；越界/面缺失返回 False
    if not _remove_track(item, side_label, index):
        return False
    save_item(item)
    return True


def rename_item(item: Item, new_name: str) -> None:
    # 改名（更新 items 行，不动 tracks）
    item.name = new_name
    update_item(item)


def change_tag(item: Item, new_tag: str) -> None:
    # 改 Tag（更新 items 行，不动 tracks）
    item.tag = new_tag
    update_item(item)


# ===== modules/generator/edit.py 函数说明 =====
# add_track(item, side_label, track) -> (bool, str): 加曲
#   逻辑：面存在 → fits 校验（拒绝返回中文原因）→ 追加 → save_item（tracks 重建）
# remove_track(item, side_label, index) -> bool: 移除（委托 items.factory + save_item）
# rename_item(item, new_name): 改名（update_item 只动行）
# change_tag(item, new_tag): 改 Tag（update_item 只动行）
#   设计理由：曲目结构变更走 save_item（整体重建），元数据变更走 update_item（行更新）
#   关联配置：容量规则（rules/capacity）、仓储（library/repository）
