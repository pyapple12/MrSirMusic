# 生成编排主流程（A8.1）：选歌 → 标签解析 → 校验 → 顺序分配 → 封面 → 建物品 → 入库

from pathlib import Path

from modules.cover.local_provider import import_cover_file
from modules.items.factory import create_item
from modules.items.model import Item, ItemType, Track
from modules.library.repository import save_item
from modules.rules.side_allocator import allocate
from modules.rules.validate import SelectionIssue, validate_selection
from modules.tagging.reader import read_tags_batch
from utils.logger import get_logger

# 模块日志（生成全链路记录，A14.4）
_logger = get_logger("generator")


class GenerateError(Exception):
    # 生成失败业务异常（携带中文消息；UI 只认分类不认细节）
    pass


def generate(
    files: list[str | Path],
    item_type: ItemType,
    name: str,
    tag: str,
    cover_source: str = "placeholder",
    cover_file: str | None = None,
) -> Item:
    # 主流程：标签解析 → 选歌校验（失败抛 GenerateError）→ 顺序分配 → 封面解析 → 建物品 → 入库
    paths = [str(p) for p in files]
    tags = read_tags_batch(paths)
    tracks = [Track.from_tagging(tag, path) for path, tag in zip(paths, tags)]
    issues: list[SelectionIssue] = validate_selection(tracks, item_type)
    if issues:
        detail = "；".join(f"{i.reason}（{Path(i.path).name}）" for i in issues)
        _logger.warning("生成失败（选歌校验未通过）: %s", detail)
        raise GenerateError(f"选歌校验未通过：{detail}")
    sides_data = allocate(tracks, item_type)
    item = create_item(name, item_type, tag)
    for label, side_tracks in sides_data.items():
        side = item.side_for(label)
        if side is not None:
            side.tracks = list(side_tracks)
    item.cover_source = cover_source
    if cover_source == "local" and cover_file:
        import_cover_file(cover_file, item)
    save_item(item)
    _logger.info(
        "生成物品成功: %s（%s，%d 首）",
        item.name,
        item_type.key,
        len(item.all_tracks()),
    )
    return item


# ===== modules/generator/generator.py 函数/常量说明 =====
# GenerateError(Exception): 生成失败业务异常（中文消息，UI 分类提示）
# generate(files, item_type, name, tag, cover_source, cover_file) -> Item: 主流程
#   逻辑：read_tags_batch → Track.from_tagging 组装 → validate_selection（失败抛异常）
#     → allocate 分配 → create_item 填面 → 封面处理（local 时 import_cover_file）→ save_item
#   异常：校验未通过抛 GenerateError（单曲标签失败已降级为 empty_record，不抛）
#   设计理由：编排层串起 A3-A7（items/rules/tagging/cover/library），未来 LLM 选歌只动本模块
#   关联配置：ItemType 来自 item_types.json；封面目录来自 base.json music_dir
