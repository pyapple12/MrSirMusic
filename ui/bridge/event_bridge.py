# 事件桥（A10.1-A10.2）：core 事件 → Qt 信号（ui/bridge 唯一翻译层），销毁自动退订防悬挂

from PySide6.QtCore import QObject, Signal

from modules.playback.event_bus import subscribe
from modules.playback.events import (
    ERROR,
    PLAYBACK_STATE,
    PROGRESS,
    SIDE_FLIPPED,
    TRACK_CHANGED,
)


class _SignalCarrier(QObject):
    # 桥内信号载体：QObject 持有 Qt 信号（对外暴露的 Qt 侧接口）
    state_changed = Signal(str)
    track_changed = Signal(object)
    progress = Signal(int, int)
    side_flipped = Signal(str)
    error = Signal(str, str)


class EventBridge:
    # 事件桥：订阅 core 事件 → 转发为 Qt 信号；shutdown 退订全部（幂等，防悬挂回调）

    def __init__(self) -> None:
        # 初始化：创建信号载体并订阅五类 core 事件（保存退订函数列表）
        self._carrier = _SignalCarrier()
        self._unsubs = [
            subscribe(PLAYBACK_STATE, self._on_state),
            subscribe(TRACK_CHANGED, self._on_track),
            subscribe(PROGRESS, self._on_progress),
            subscribe(SIDE_FLIPPED, self._on_side),
            subscribe(ERROR, self._on_error),
        ]

    @property
    def signals(self) -> _SignalCarrier:
        # Qt 侧信号载体（视图层 connect 用）
        return self._carrier

    def _on_state(self, payload) -> None:
        # core PLAYBACK_STATE → state_changed（state 字符串）
        self._carrier.state_changed.emit(getattr(payload, "state", ""))

    def _on_track(self, payload) -> None:
        # core TRACK_CHANGED → track_changed（TrackChangedPayload 原样透传）
        self._carrier.track_changed.emit(payload)

    def _on_progress(self, payload) -> None:
        # core PROGRESS → progress（position_ms, duration_ms）
        self._carrier.progress.emit(
            getattr(payload, "position_ms", 0), getattr(payload, "duration_ms", 0)
        )

    def _on_side(self, payload) -> None:
        # core SIDE_FLIPPED → side_flipped（side 字符串）
        self._carrier.side_flipped.emit(getattr(payload, "side", ""))

    def _on_error(self, payload) -> None:
        # core ERROR → error（category, message）
        self._carrier.error.emit(
            getattr(payload, "category", ""), getattr(payload, "message", "")
        )

    def shutdown(self) -> None:
        # 退订全部 core 事件（幂等：重复调用安全；桥销毁前必须调用，防悬挂回调）
        for unsub in self._unsubs:
            unsub()
        self._unsubs.clear()

    def __del__(self) -> None:
        # 析构兜底（B3.17）：未显式 shutdown 时退订，防悬挂回调（GC 时机不定，正常路径仍走 shutdown）
        try:
            self.shutdown()
        except Exception:
            pass


# ===== ui/bridge/event_bridge.py 类/函数说明 =====
# _SignalCarrier(QObject): 信号载体（state_changed/track_changed/progress/side_flipped/error）
# EventBridge: core 事件 → Qt 信号翻译层（唯一允许 import PySide6 的翻译层）
#   __init__: 订阅五类 core 事件，退订函数入 _unsubs
#   signals: 载体属性（视图 connect）
#   _on_state/_on_track/_on_progress/_on_side/_on_error: 各事件转发（payload 字段安全读取）
#   shutdown(): 全部退订（幂等；A10.2 生命周期管理，防销毁后悬挂回调）
#   设计理由：AGENTS.md 架构约束——modules 事件契约零 Qt，ui/bridge 是唯一翻译层
#   关联配置：事件名/payload 见 modules/playback/events.py
