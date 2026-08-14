# 播放队列（A9.6）：由 Item 生成面内曲目序列 + 当前索引 + 翻面标记

from dataclasses import dataclass, field

from modules.items.model import Item, Track


@dataclass
class PlaybackQueue:
    # 播放序列：tracks 为面内展平列表；boundary 为 A 面曲目数（B 面起点索引）
    tracks: list[Track]
    boundary: int
    auto_flip: bool = False
    index: int = 0
    flipped: bool = False

    def current_track(self) -> Track | None:
        # 当前曲目（索引越界返回 None）
        if 0 <= self.index < len(self.tracks):
            return self.tracks[self.index]
        return None

    def next(self) -> bool:
        # 推进：A 面末（还有 B 面）→ auto_flip 翻面跳 B 面首（标记 flipped），否则停止；
        # 其余 +1；序列末 False
        if self.boundary < len(self.tracks) and self.index == self.boundary - 1:
            if self.auto_flip:
                self.index = self.boundary
                self.flipped = True
                return True
            return False
        if self.index + 1 < len(self.tracks):
            self.index += 1
            return True
        return False

    def prev(self) -> bool:
        # 回退：非首曲 -1；首曲返回 False（停留原位）
        if self.index > 0:
            self.index -= 1
            return True
        return False


def build_queue(item: Item, auto_flip: bool = False) -> PlaybackQueue:
    # 由物品构建播放队列：[SideA.tracks..., SideB.tracks...]，boundary=A 面曲目数
    tracks: list[Track] = []
    boundary = 0
    for label in item.type.sides:
        side = item.side_for(label)
        if side is None:
            continue
        if boundary == 0:
            boundary = len(tracks) + len(side.tracks)
        tracks.extend(side.tracks)
    return PlaybackQueue(tracks=tracks, boundary=boundary, auto_flip=auto_flip)


# ===== modules/playback/queue.py 类/函数说明 =====
# PlaybackQueue(dataclass): 播放序列状态机
#   current_track(): 当前曲目（越界 None）
#   next(): 推进（普通 +1；A 面末 auto_flip 翻面；序列末 False）
#   prev(): 回退（首曲失败停留）
#   flipped: 翻面标记（进入 B 面后 True，UI 翻面动画/指示用）
# build_queue(item, auto_flip) -> PlaybackQueue: 物品 → 队列（面内展平 + boundary）
#   设计理由：边界用 boundary（A 面曲目数）表达翻面点；auto_flip 由调用方
#     （engine 读 settings.auto_flip）传入
#   关联配置：面集合来自 ItemType.sides（item_types.json）；auto_flip 来自用户配置
