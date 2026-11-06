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
from utils.convert import ms_from_seconds
from utils.logger import get_logger

# 模块日志（生成/播放/错误全链路记录，A14.4）
_logger = get_logger("playback.engine")


class PlaybackEngine:
    # 播放引擎：内部 QMediaPlayer（方法内延迟导入，模块导入零 Qt 开销）；对外仅项目模型

    def __init__(self) -> None:
        # 初始化：播放器延迟创建；队列/当前曲目/状态初始为空
        self._player: Any | None = None
        self._audio_output: Any | None = None
        self._queue: PlaybackQueue | None = None
        self._track: Track | None = None
        self.state: str = "stopped"
        # 刚翻面标记（D0.4：SIDE_FLIPPED 仅在翻面瞬间发射一次，B 面内切换不发）
        self._just_flipped = False
        # 挂起跳转秒数（H1：setSource 后媒体未就绪时 setPosition 会被忽略，待 LoadedMedia 补应用）
        self._pending_seek: float | None = None

    def _ensure_player(self) -> Any:
        # 延迟创建 QMediaPlayer（offscreen 可无头初始化）；媒体自然结束 → ended；播放错误 → ERROR
        if self._player is None:
            from PySide6.QtMultimedia import QAudioOutput, QMediaPlayer

            self._player = QMediaPlayer()
            # H0.1 体检修复（P0）：Qt6 必须显式挂载 QAudioOutput，否则解码推进但全程静音；
            # 输出对象持引用防 GC 回收
            self._audio_output = QAudioOutput()
            self._player.setAudioOutput(self._audio_output)
            self._player.mediaStatusChanged.connect(self._on_media_status)
            self._player.errorOccurred.connect(self._on_player_error)
        return self._player

    def _on_player_error(self, error: Any, error_string: str) -> None:
        # 播放器错误回调（C0.2/D0.5）：解码失败/格式不支持/IO 错误 → ERROR(playback_error) + 状态同步 stopped；
        # FIX006.2（A006-P2-2）：清挂起跳转——否则旧偏移会经 LoadedMedia 应用到之后错误曲目上
        from PySide6.QtMultimedia import QMediaPlayer

        if error == QMediaPlayer.Error.NoError:
            return
        self._pending_seek = None
        _logger.warning("播放器错误: %s", error_string)
        emit(
            ERROR,
            ErrorPayload(
                category="playback_error", message=f"播放错误：{error_string}"
            ),
        )
        if self.state != "stopped":
            self._emit_state("stopped")

    def _on_media_status(self, status: Any) -> None:
        # 媒体状态回调：自然结束（EndOfMedia）→ 发 PLAYBACK_STATE(ended)（由 progress 决定 next/stop）；
        # LoadedMedia → 应用挂起跳转（H1：跨曲面内寻曲时源刚切换，此刻 setPosition 才生效）
        from PySide6.QtMultimedia import QMediaPlayer

        if status == QMediaPlayer.MediaStatus.EndOfMedia:
            self.state = "ended"
            emit(PLAYBACK_STATE, PlaybackStatePayload(state="ended"))
        elif status == QMediaPlayer.MediaStatus.LoadedMedia:
            if self._pending_seek is not None:
                seconds = self._pending_seek
                self._pending_seek = None
                self._player.setPosition(ms_from_seconds(seconds))

    def _emit_state(self, state: str) -> None:
        # 发播放状态事件（playing/paused/stopped）
        self.state = state
        emit(PLAYBACK_STATE, PlaybackStatePayload(state=state))

    def _side_range(self) -> tuple[int, int]:
        # 当前所在面的队列索引区间 [start, end)：boundary>0 按 A/B 分段；
        # boundary=0（空 A 面）整队列视作 A 面（与 _emit_track 的 F3.1 推导同源）
        if self._queue is None or not self._queue.tracks:
            return (0, 0)
        boundary = self._queue.boundary
        if boundary > 0:
            if self._queue.index >= boundary:
                return (boundary, len(self._queue.tracks))
            return (0, boundary)
        return (0, len(self._queue.tracks))

    def _side_durations(self, start: int, end: int) -> list[float] | None:
        # 面内曲目时长列表（秒）：全部有效（>0）才返回，任一缺失/非正返回 None（宽容降级）
        tracks = self._queue.tracks[start:end]
        durations: list[float] = []
        for track in tracks:
            raw = getattr(track, "duration_seconds", None)
            if not isinstance(raw, (int, float)) or isinstance(raw, bool) or raw <= 0:
                return None
            durations.append(float(raw))
        return durations if tracks else None

    def _emit_track(self) -> None:
        # 发曲目切换事件（当前曲目 + 所在面；翻面瞬间附带一次 SIDE_FLIPPED，D0.4）；
        # H1 附带面内偏移/面总时长（唱针面内映射；时长缺失时为 None 由 UI 降级）
        side = None
        offset = None
        total = None
        if self._queue is not None:
            # F3.1：boundary=0（空 A 面）时推导为 A（index>=0 恒真不误判 B）
            side = (
                "B"
                if self._queue.boundary > 0
                and self._queue.index >= self._queue.boundary
                else "A"
            )
            start, end = self._side_range()
            durations = self._side_durations(start, end)
            if durations is not None:
                total = sum(durations)
                offset = sum(durations[: self._queue.index - start])
        emit(
            TRACK_CHANGED,
            TrackChangedPayload(
                track=self._track,
                side=side,
                side_offset_seconds=offset,
                side_total_seconds=total,
            ),
        )
        if self._just_flipped and side == "B":
            emit(SIDE_FLIPPED, SideFlippedPayload(side="B"))
            self._just_flipped = False

    def load_item(self, item: Item) -> None:
        # 载入物品：建面内播放序列（auto_flip 读用户配置）→ 载第一首（不自动播放）；状态复位（E1.2）
        from PySide6.QtCore import QUrl

        self._queue = build_queue(item, auto_flip=load_config().auto_flip)
        self._just_flipped = False
        # H0.2 体检修复（P2）：复位改走事件——播放中载入首曲缺失的新物品时，
        # 裸赋值不发事件会导致 UI 停留在"播放中"（转盘照转/按钮显示暂停）而实际无声
        self._pending_seek = None
        self._emit_state("stopped")
        player = self._ensure_player()
        first = self._queue.current_track()
        self._track = first
        if first is not None and not first.is_missing():
            player.setSource(QUrl.fromLocalFile(first.path))
        elif first is not None:
            # FIX006.11（A006-P3-⑦）：首曲缺失与 play() 同口径——file_missing 中文分类预检，
            # 不 setSource（否则走 Qt 泛化英文错误，错误分类漂移）
            _logger.warning("载入物品首曲缺失: %s", first.path)
            emit(
                ERROR,
                ErrorPayload(
                    category="file_missing",
                    message=f"文件缺失：{first.title or first.path}",
                ),
            )
            # FIX007.1（A007-P2）：补停旧媒体——预检跳过 setSource 后丢失其停声副作用，
            # 播放中换载缺失首曲物品会"UI 冻结停止态而扬声器继续放旧曲"（A006-P2-3 同构）
            player.stop()
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
        # 跳转（毫秒换算；未初始化播放器忽略）；ended 后 seek 会把媒体拉回 LoadedMedia，
        # 补发 paused 刷新按钮态（H0.4：否则 UI 卡在"播放结束"态无法继续）
        if self._player is not None:
            self._player.setPosition(ms_from_seconds(seconds))
            if self.state == "ended":
                self._emit_state("paused")

    def seek_side(self, fraction: float) -> bool:
        # 面内寻曲（H1）：fraction ∈ [0,1] 为当前面内时间比例 → 定位目标曲目与曲内偏移；
        # 同曲直接 seek；跨曲更新队列索引 + 载入播放（挂起跳转待 LoadedMedia 应用）。
        # 仅在当前面内定位（拟物语义：唱针不跨面）；面时长缺失时降级为当前曲目内比例跳转
        if self._queue is None or not self._queue.tracks:
            return False
        clamped = min(1.0, max(0.0, float(fraction)))
        start, end = self._side_range()
        durations = self._side_durations(start, end)
        if durations is None:
            track = self._queue.current_track()
            if track is None:
                return False
            fallback = float(getattr(track, "duration_seconds", 0) or 0)
            self.seek(clamped * fallback)
            return True
        total = sum(durations)
        value = clamped * total
        # 累计时长定位目标曲目（末曲吸收浮点余量，防 fraction→1.0 越界）
        offset = 0.0
        target = start
        acc = 0.0
        for i, duration in enumerate(durations):
            target = start + i
            offset = value - acc
            if value < acc + duration:
                break
            acc += duration
        offset = min(max(0.0, offset), durations[target - start])
        if target == self._queue.index:
            self.seek(offset)
            return True
        self._queue.index = target
        self._pending_seek = offset
        ok = self._play_current("面内寻曲跳转")
        if not ok:
            self._pending_seek = None
        return ok

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
            # E2.1 跳过语义：更新 _track 保持一致 + 发 TRACK_CHANGED（F0.2 UI 展示同步）+ ERROR；
            # FIX006.3（A006-P2-3）：手动切曲路径停旧媒体 + 状态同步 stopped——
            # 否则 UI 展示已切到缺失曲而扬声器继续放上一曲（自动链经 stop 无此错位）
            self._track = track
            self._emit_track()
            _logger.warning("播放失败（文件缺失）: %s", track.path)
            emit(
                ERROR,
                ErrorPayload(
                    category="file_missing",
                    message=f"文件缺失：{track.title or track.path}",
                ),
            )
            if self._player is not None:
                self._player.stop()
            self._emit_state("stopped")
            return False
        self._track = track
        self._ensure_player().setSource(QUrl.fromLocalFile(track.path))
        self._ensure_player().play()
        self._emit_track()
        self._emit_state("playing")
        _logger.info("%s: %s", log_msg, track.title or track.path)
        return True

    def play_next(self) -> bool:
        # 播放下一首（含翻面）：队列推进成功 → 载入播放；失败/缺失返回 False（E2.1 跳过语义：index 保持推进）；
        # FIX007.2：换源入口清挂起跳转——旧 pending 对新源必然失效，防 LoadedMedia 错位应用
        self._pending_seek = None
        if self._queue is None or not self._queue.next():
            return False
        # D0.4：进入 B 面第一首（刚翻面）时置标记，SIDE_FLIPPED 仅发一次
        if self._queue.flipped and self._queue.index == self._queue.boundary:
            self._just_flipped = True
        ok = self._play_current("切至下一首")
        if not ok and self._just_flipped:
            # F1.2：自动翻面遇缺失 → 翻面事件不发（与 flip 失败复位对称）
            self._just_flipped = False
        return ok

    def play_prev(self) -> bool:
        # 播放上一首：队列回退成功 → 载入播放；失败/缺失返回 False（E2.1 跳过语义：index 保持）；
        # FIX007.2：换源入口清挂起跳转（同 play_next）
        self._pending_seek = None
        if self._queue is None or not self._queue.prev():
            return False
        return self._play_current("切回上一首")

    def flip(self) -> bool:
        # 手动翻面：A 面 → 跳 B 面首播放（发 SIDE_FLIPPED）；已在 B 面/无 B 面返回 False
        # 失败（B 面首缺失）→ 回滚 A 面末 + 复位翻面标记（E1.1/E2.1）；FIX007.2：换源入口清挂起
        self._pending_seek = None
        if self._queue is None or not (self._queue.boundary < len(self._queue.tracks)):
            return False
        if self._queue.index >= self._queue.boundary:
            return False
        self._queue.index = self._queue.boundary
        self._queue.flipped = True
        self._just_flipped = True
        if not self._play_current("手动翻面 → B 面"):
            self._queue.index = self._queue.boundary - 1
            self._queue.flipped = False
            self._just_flipped = False
            self._track = self._queue.current_track()  # F0.3：回滚 _track 到 A 面末
            self._emit_track()  # F0.2 配套：UI 展示同步回 A 面末
            return False
        _logger.info("手动翻面 → B 面")
        return True


# ===== modules/playback/engine.py 类/函数说明 =====
# PlaybackEngine: 播放引擎（内部 QMediaPlayer 延迟导入，对外仅项目模型/事件）
#   load_item(item): 建队列（auto_flip 读 settings）→ 载第一首 → 发 TRACK_CHANGED；
#     复位走 _emit_state("stopped")（H0.2）+ 清挂起跳转
#   play/pause/stop/seek/position_ms: 播放控制（state 变化发 PLAYBACK_STATE）；
#     seek 在 ended 后补发 paused（H0.4）
#   seek_side(fraction): 面内寻曲（H1）——面内时间比例 → 定位曲目/曲内偏移；
#     同曲 seek、跨曲换索引挂起跳转；面时长缺失降级单曲内比例；只在当前面内（唱针不跨面）
#   current_track(): 当前曲目（Track | None）
#   play_next(): 队列推进（含翻面 SIDE_FLIPPED）→ 载入播放 → 发事件；无下一首 False
#   _ensure_player: 延迟创建 QMediaPlayer + QAudioOutput（H0.1：不挂输出全程静音）
#   _on_media_status: 自然结束 → PLAYBACK_STATE(ended)（progress 监听后决定 next/stop）；
#     LoadedMedia → 应用挂起跳转 _pending_seek（H1 跨曲寻曲）
#   _side_range/_side_durations: 当前面索引区间 + 面内时长表（H1；缺失宽容降级 None）
#   _emit_track: TRACK_CHANGED + 翻面时 SIDE_FLIPPED（side 由队列 flipped/boundary 推导）；
#     附带 side_offset_seconds/side_total_seconds（H1 唱针面内映射数据）
#   设计理由：modules 层特许例外——内部可用 QtMultimedia，对外零 Qt 类型（A9.3 定案）
#   关联配置：auto_flip 来自 config/settings.py 用户配置；队列逻辑见 queue.py
