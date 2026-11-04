# 播放事件契约（A9.1）：事件名常量 + payload dataclass，零 Qt 依赖（ui/bridge 唯一翻译层）

from dataclasses import dataclass

from modules.items.model import Track

# 事件名常量（ui/bridge 与 progress 等模块按名订阅）
PLAYBACK_STATE = "playback_state"
TRACK_CHANGED = "track_changed"
PROGRESS = "progress"
SIDE_FLIPPED = "side_flipped"
ERROR = "error"


@dataclass
class PlaybackStatePayload:
    # 播放状态切换载荷（playing/paused/stopped/ended）
    state: str


@dataclass
class TrackChangedPayload:
    # 曲目切换载荷（track 为当前曲目，side 为所在面 label）
    # H1 扩展：side_offset_seconds=当前曲目在面内的起始秒偏移、side_total_seconds=面总时长秒；
    # 时长缺失/无队列时为 None（唱针映射消费端需宽容降级到单曲内映射）
    track: Track | None
    side: str | None = None
    side_offset_seconds: float | None = None
    side_total_seconds: float | None = None


@dataclass
class ProgressPayload:
    # 进度载荷（毫秒位置/总时长）
    position_ms: int
    duration_ms: int


@dataclass
class SideFlippedPayload:
    # 翻面载荷（新面 label）
    side: str


@dataclass
class ErrorPayload:
    # 播放错误载荷（分类 + 中文消息；UI 按分类提示）
    category: str
    message: str


# ===== modules/playback/events.py 常量/类说明 =====
# 事件名常量: PLAYBACK_STATE/TRACK_CHANGED/PROGRESS/SIDE_FLIPPED/ERROR（z.plan 第六节契约）
# PlaybackStatePayload: state 取值 playing/paused/stopped/ended
# TrackChangedPayload: track + side（面 label）+ side_offset_seconds/side_total_seconds
#   （H1 面内寻曲扩展：可选，None=时长缺失降级；消费端 bridge 用 getattr 兼容）
# ProgressPayload: position_ms/duration_ms（毫秒，1s 定时器上报）
# SideFlippedPayload: side（翻面后所在面）
# ErrorPayload: category（分类，如 file_missing）+ message（中文）
#   设计理由：纯数据结构零 Qt 依赖（AGENTS.md 架构约束），ui/bridge 是唯一翻译层
#   关联配置：无
