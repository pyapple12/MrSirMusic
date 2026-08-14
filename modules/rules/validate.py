# 选歌校验模块（A5.3）：重复曲目 / 超容量 / 路径失效三类校验，返回逐条问题清单

from dataclasses import dataclass

from modules.items.model import ItemType, Track


@dataclass
class SelectionIssue:
    # 选歌校验单条问题：曲目路径 + 中文原因
    path: str
    reason: str


def validate_selection(
    tracks: list[Track], item_type: ItemType
) -> list[SelectionIssue]:
    # 校验选歌列表：重复 path / 路径失效 / 单曲超单面容量 分别记问题；返回问题清单（空 = 全部通过）
    issues: list[SelectionIssue] = []
    seen: set[str] = set()
    max_seconds = item_type.minutes_per_side * 60
    for track in tracks:
        if track.path in seen:
            issues.append(SelectionIssue(track.path, "重复曲目（同一路径）"))
            continue
        if track.is_missing():
            issues.append(SelectionIssue(track.path, "文件缺失"))
            continue
        if track.duration_seconds > max_seconds:
            issues.append(SelectionIssue(track.path, "单曲超过单面容量"))
            continue
        seen.add(track.path)
    return issues


# ===== modules/rules/validate.py 函数/常量说明 =====
# SelectionIssue(dataclass): 校验问题条目（path + reason，UI 可直接展示）
# validate_selection(tracks, item_type) -> list[SelectionIssue]: 选歌校验
#   逻辑：逐曲三类判定（重复 path → 问题；is_missing → 问题；时长 > 单面容量 → 问题）；
#     通过项记入 seen 防后续重复；已记问题的曲目不入 seen（同 path 多次出现每条都记）
#   设计理由：校验结果列表化（不抛异常），调用方（生成流程/UI 对话框）逐条提示
#   关联配置：单面容量来自 ItemType.minutes_per_side（item_types.json 装配）
