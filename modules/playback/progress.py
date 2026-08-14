# 进度上报（A9.7）：1s 定时器读引擎位置发 PROGRESS；播放结束自动 next/stop

from typing import Any, Callable

from modules.playback.engine import PlaybackEngine
from modules.playback.event_bus import emit, subscribe
from modules.playback.events import PLAYBACK_STATE, PROGRESS, ProgressPayload


class ProgressReporter:
    # 进度上报器：QTimer(1s) → 引擎位置 → PROGRESS；监听 ended → 自动 next/stop

    def __init__(self, engine: PlaybackEngine, timer_interval_ms: int = 1000) -> None:
        # 初始化：创建 1s 定时器（offscreen 可无头创建）+ 订阅播放结束事件
        from PySide6.QtCore import QTimer

        self.engine = engine
        self.timer_interval_ms = timer_interval_ms
        self._timer = QTimer()
        self._timer.setInterval(timer_interval_ms)
        self._timer.timeout.connect(self._report)
        self._unsubscribe_state = subscribe(PLAYBACK_STATE, self._on_state)

    def start(self) -> None:
        # 启动定时器（进度上报开始）
        self._timer.start()

    def stop(self) -> None:
        # 停止定时器（进度上报暂停）
        self._timer.stop()

    def shutdown(self) -> None:
        # 销毁：停定时器 + 退订事件（防悬挂回调）
        self.stop()
        self._unsubscribe_state()

    def _report(self) -> None:
        # 读引擎位置与当前曲目时长 → 发 PROGRESS（无曲目/无时长时按 0）
        duration_ms = 0
        track = self.engine.current_track()
        if track is not None:
            duration_ms = int(track.duration_seconds * 1000)
        emit(
            PROGRESS,
            ProgressPayload(
                position_ms=self.engine.position_ms(), duration_ms=duration_ms
            ),
        )

    def _on_state(self, payload: Any) -> None:
        # 播放结束（ended）：自动 next（含翻面）；无下一首 → stop
        if getattr(payload, "state", None) != "ended":
            return
        if not self.engine.play_next():
            self.engine.stop()


# ===== modules/playback/progress.py 类/函数说明 =====
# ProgressReporter: 进度上报（1s 定时器 + 结束协调）
#   __init__(engine, timer_interval_ms): QTimer 创建 + PLAYBACK_STATE 订阅
#   start()/stop(): 定时器启停（播放/暂停联动由调用方控制）
#   shutdown(): 停定时器 + 退订（生命周期管理，防悬挂回调）
#   _report(): PROGRESS 事件（position_ms + duration_ms；duration 来自 Track.duration_seconds）
#   _on_state(payload): ended → engine.play_next()（失败 → engine.stop()）
#   设计理由：定时器事件循环驱动（1s 节流，非必要不频繁刷新——AGENTS.md 节流约定）
#   关联配置：定时器间隔可调（第一版固定 1000ms，后续可外置 ui.json/base.json）
