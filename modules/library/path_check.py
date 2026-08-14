# 路径失效检测模块（A6.4）：加载后批量检测缺失文件，写入 Item.missing_tracks 内存标记

from modules.items.model import Item


def mark_missing(item: Item) -> set[str]:
    # 批量检测物品全部曲目文件：缺失路径写入 item.missing_tracks（内存标记，不落库），返回缺失集合
    missing = {t.path for t in item.all_tracks() if t.is_missing()}
    item.missing_tracks = missing
    return missing


# ===== modules/library/path_check.py 函数说明 =====
# mark_missing(item) -> set[str]: 缺失检测
#   逻辑：all_tracks 遍历 → is_missing() 收集缺失 path → 写 item.missing_tracks → 返回
#   设计理由：加载流程（repository.load_all 后由调用方统一标记）不阻塞不抛出；
#     missing_tracks 为内存标记（A6.4 定案，不持久化）
#   关联配置：无（文件存在性本地判定）
