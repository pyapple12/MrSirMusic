# 播放引擎（A9.3）：封装 QMediaPlayer（内部延迟导入），对外零 Qt 类型，状态经 event_bus 发事件

from typing import Any

from config.settings import load_config
from modules.items.model import Item, Track
from modules.playback.event_bus import emit
from modules.playback.events import (
    ERROR,
    PLAYBACK_STATE,
    SIDE_FLIPPED,
    TRACK_CHANGED,
    ErrorPayload,
    PlaybackStatePayload,
    SideFlippedPayload,
    TrackChangedPayload,
)
from modules.playback.queue import PlaybackQueue, build_queue
from utils.logger import get_logger

# 模块日志（生成/播放/错误全链路记录，A14.4）
_logger = get_logger("playback.engine")


class PlaybackEngine:
    # 播放引擎：内部 QMediaPlayer（方法内延迟导入，模块导入零 Qt 开销）；对外仅项目模型

    def __init__(self) -> None:
        # 初始化：播放器延迟创建；队列/当前曲目/状态初始为空
        self._player: Any | None = None
        self._queue: PlaybackQueue | None = None
        self._track: Track | None = None
        self.state: str = "stopped"

    def _ensure_player(self) -> Any:
        # 延迟创建 QMediaPlayer（offscreen 可无头初始化）；媒体自然结束 → ended；播放错误 → ERROR
        if self._player is None:
            from PySide6.QtMultimedia import QMediaPlayer

            self._player = QMediaPlayer()
            self._player.mediaStatusChanged.connect(self._on_media_status)
            self._player.errorOccurred.connect(self._on_player_error)
        return self._player

    def _on_player_error(self, error: Any, error_string: str) -> None:
        # 播放器错误回调（C0.2）：解码失败/格式不支持/IO 错误 → ERROR(playback_error) + 日志
        from PySide6.QtMultimedia import QMediaPlayer

        if error == QMediaPlayer.Error.NoError:
            return
        _logger.warning("播放器错误: %s", error_string)
        emit(
            ERROR,
            ErrorPayload(
                category="playback_error", message=f"播放错误：{error_string}"
            ),
        )

    def _on_media_status(self, status: Any) -> None:
        # 媒体状态回调：自然结束（EndOfMedia）→ 发 PLAYBACK_STATE(ended)（由 progress 决定 next/stop）
        from PySide6.QtMultimedia import QMediaPlayer

        if status == QMediaPlayer.MediaStatus.EndOfMedia:
            self.state = "ended"
            emit(PLAYBACK_STATE, PlaybackStatePayload(state="ended"))

    def _emit_state(self, state: str) -> None:
        # 发播放状态事件（playing/paused/stopped）
        self.state = state
        emit(PLAYBACK_STATE, PlaybackStatePayload(state=state))

    def _emit_track(self) -> None:
        # 发曲目切换事件（当前曲目 + 所在面；翻面时附带 SIDE_FLIPPED）
        side = None
        if self._queue is not None:
            side = "B" if self._queue.index >= self._queue.boundary else "A"
        emit(TRACK_CHANGED, TrackChangedPayload(track=self._track, side=side))
        if self._queue is not None and self._queue.flipped and side == "B":
            emit(SIDE_FLIPPED, SideFlippedPayload(side="B"))

    def load_item(self, item: Item) -> None:
        # 载入物品：建面内播放序列（auto_flip 读用户配置）→ 载第一首（不自动播放）
        from PySide6.QtCore import QUrl

        self._queue = build_queue(item, auto_flip=load_config().auto_flip)
        player = self._ensure_player()
        first = self._queue.current_track()
        self._track = first
        if first is not None:
            player.setSource(QUrl.fromLocalFile(first.path))
        self._emit_track()

    def play(self) -> None:
        # 播放（无当前曲目静默忽略；曲目文件缺失 → ERROR 事件 + 日志，不播放不崩溃）
        if self._track is None:
            return
        if self._track.is_missing():
            message = f"文件缺失：{self._track.title or self._track.path}"
            _logger.warning("播放失败（文件缺失）: %s", self._track.path)
            emit(ERROR, ErrorPayload(category="file_missing", message=message))
            return
        self._ensure_player().play()
        self._emit_state("playing")
        _logger.info("开始播放: %s", self._track.title or self._track.path)

    def pause(self) -> None:
        # 暂停
        if self._player is not None:
            self._player.pause()
            self._emit_state("paused")

    def stop(self) -> None:
        # 停止（停留当前曲目，不发 TRACK_CHANGED）
        if self._player is not None:
            self._player.stop()
        self._emit_state("stopped")

    def seek(self, seconds: float) -> None:
        # 跳转（毫秒换算；未初始化播放器忽略）
        if self._player is not None:
            self._player.setPosition(int(seconds * 1000))

    def position_ms(self) -> int:
        # 当前播放位置（毫秒；未初始化返回 0）
        if self._player is None:
            return 0
        return int(self._player.position())

    def duration_ms(self) -> int:
        # 媒体总时长（毫秒；B3.13 进度上报优先用播放器时长，未初始化返回 0）
        if self._player is None:
            return 0
        return int(self._player.duration())

    def current_track(self) -> Track | None:
        # 当前曲目（项目模型，对外零 Qt 类型）
        return self._track

    def _play_current(self, log_msg: str) -> bool:
        # 载入并播放当前队列曲目：缺失 → ERROR(file_missing) + 日志 + 返回 False（不崩溃）
        from PySide6.QtCore import QUrl

        track = self._queue.current_track() if self._queue is not None else None
        if track is None:
            return False
        if track.is_missing():
            _logger.warning("播放失败（文件缺失）: %s", track.path)
            emit(
                ERROR,
                ErrorPayload(
                    category="file_missing",
                    message=f"文件缺失：{track.title or track.path}",
                ),
            )
            return False
        self._track = track
        self._ensure_player().setSource(QUrl.fromLocalFile(track.path))
        self._ensure_player().play()
        self._emit_track()
        self._emit_state("playing")
        _logger.info("%s: %s", log_msg, track.title or track.path)
        return True

    def play_next(self) -> bool:
        # 播放下一首（含翻面）：队列推进成功 → 载入播放；失败/缺失返回 False
        if self._queue is None or not self._queue.next():
            return False
        return self._play_current("切至下一首")

    def play_prev(self) -> bool:
        # 播放上一首：队列回退成功 → 载入播放；失败/缺失返回 False
        if self._queue is None or not self._queue.prev():
            return False
        return self._play_current("切回上一首")

    def flip(self) -> bool:
        # 手动翻面：A 面 → 跳 B 面首播放（发 SIDE_FLIPPED）；已在 B 面/无 B 面返回 False
        if self._queue is None or not (self._queue.boundary < len(self._queue.tracks)):
            return False
        if self._queue.index >= self._queue.boundary:
            return False
        self._queue.index = self._queue.boundary
        self._queue.flipped = True
        if not self._play_current("手动翻面 → B 面"):
            return False
        _logger.info("手动翻面 → B 面")
        return True


# ===== modules/playback/engine.py 类/函数说明 =====
# PlaybackEngine: 播放引擎（内部 QMediaPlayer 延迟导入，对外仅项目模型/事件）
#   load_item(item): 建队列（auto_flip 读 settings）→ 载第一首 → 发 TRACK_CHANGED
#   play/pause/stop/seek/position_ms: 播放控制（state 变化发 PLAYBACK_STATE）
#   current_track(): 当前曲目（Track | None）
#   play_next(): 队列推进（含翻面 SIDE_FLIPPED）→ 载入播放 → 发事件；无下一首 False
#   _on_media_status: 自然结束 → PLAYBACK_STATE(ended)（progress 监听后决定 next/stop）
#   _emit_track: TRACK_CHANGED + 翻面时 SIDE_FLIPPED（side 由队列 flipped/boundary 推导）
#   设计理由：modules 层特许例外——内部可用 QtMultimedia，对外零 Qt 类型（A9.3 定案）
#   关联配置：auto_flip 来自 config/settings.py 用户配置；队列逻辑见 queue.py
