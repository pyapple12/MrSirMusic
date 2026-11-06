# 拟物音效套件（H3）：QSoundEffect 封装，fail-soft（无声卡/offscreen 环境自动降级禁用）
# 循环底噪（黑胶爆裂/嘶声，随播放态启停）+ 一次性音效（落针刮擦/磁带换曲机械声）
# 响度随拟真度档位（effects.json levels.*.ambience_intensity；concise 档静音）
# 依赖纪律：QtMultimedia 只在本模块使用（ui 层，QMediaPlayer 特许同源的音效例外）

from pathlib import Path

from PySide6.QtCore import QObject

from config.static.static_config import get_static_config
from utils.logger import get_logger
from utils.paths import project_root

# 模块日志（初始化失败/降级记录一次，不刷屏）
_logger = get_logger("ui.sounds")

# 静态配置一次解包
_SC = get_static_config()

# 音效资源目录（data/sounds/，产物由 .temp/make_sounds.py 一次性生成入库）
_SOUNDS_DIR = project_root() / _SC.base.get("data_dir", "data") / "sounds"

# 一次性音效固定响度（底噪响度走档位 ambience_intensity，一次性音效走固定值）
_NEEDLE_DROP_VOLUME = 0.8
_TAPE_MECH_VOLUME = 0.9


class SoundKit(QObject):
    # 拟物音效套件：黑胶循环底噪 + 落针/磁带一次性音效；初始化失败整体禁用（不崩溃不阻塞）

    def __init__(self, parent: QObject | None = None) -> None:
        # 初始化：逐一装配 QSoundEffect（资源缺失/后端不可用 → 整体禁用 + 告警一次）
        super().__init__(parent)
        self._enabled = False  # fail-soft 总闸：装配环节任何失败即禁用
        self._intensity = 0.0  # 底噪响度（档位 ambience_intensity）
        self._media_kind = "vinyl"  # 当前载体类型（vinyl 才有循环底噪）
        self._active = False  # 播放中标记（循环底噪开关源）
        self._crackle = None
        self._needle_drop = None
        self._tape_mech = None
        try:
            self._crackle = self._build_effect("vinyl_crackle")
            if self._crackle is not None:
                # 底噪无限循环（播放态启停）；-2 = QSoundEffect.Infinite 整数值
                # （PySide6 枚举对象与 setLoopCount(int) 签名不兼容，直接传整数值）
                self._crackle.setLoopCount(-2)
            self._needle_drop = self._build_effect("needle_drop")
            self._tape_mech = self._build_effect("tape_mech")
            self._enabled = (
                self._crackle is not None
                and self._needle_drop is not None
                and self._tape_mech is not None
            )
            if not self._enabled:
                _logger.warning("音效资源缺失（禁用音效，不影响播放）: %s", _SOUNDS_DIR)
        except Exception as exc:  # 无声卡/QtMultimedia 后端不可用等，一律降级
            self._enabled = False
            _logger.warning("音效初始化失败（禁用音效，不影响播放）: %s", exc)

    @staticmethod
    def _build_effect(name: str):
        # 装配单个 QSoundEffect（资源文件缺失返回 None；加载走异步 status，播放时未就绪静默忽略）
        path = _SOUNDS_DIR / f"{name}.wav"
        if not path.is_file():
            return None
        from PySide6.QtCore import QUrl
        from PySide6.QtMultimedia import QSoundEffect

        effect = QSoundEffect()
        effect.setSource(QUrl.fromLocalFile(str(path)))
        return effect

    def set_level(self, level: str) -> None:
        # 档位切换（main_window._apply_realism 联动）：读 levels[level].ambience_intensity
        # 宽容解析（缺失/非法 → 0）；0 值同时停底噪（concise 档静音语义）
        rec = _SC.effects.get("levels", {}).get(level, {})
        raw = rec.get("ambience_intensity", 0.0) if isinstance(rec, dict) else 0.0
        try:
            intensity = max(0.0, min(1.0, float(raw)))
        except (TypeError, ValueError):
            intensity = 0.0
        self._intensity = intensity
        if self._crackle is not None:
            self._crackle.setVolume(intensity)
        if intensity <= 0.0:
            self._stop_ambience()
        elif self._active:
            # FIX006.4（A006-P2-4）：播放中切档位（如 concise→refined）恢复底噪——
            # _start_ambience 内部 enabled/kind/intensity 三重门控，幂等安全
            self._start_ambience()

    def set_media_kind(self, kind: str) -> None:
        # 载体类型切换（载入物品联动）：黑胶才有循环底噪，切类型即停
        if kind != self._media_kind:
            self._media_kind = str(kind)
            self._stop_ambience()

    def set_active(self, active: bool) -> None:
        # 播放态联动（playing=True / 其余 False）：黑胶 + 响度>0 → 循环底噪启停
        self._active = bool(active)
        if self._active:
            self._start_ambience()
        else:
            self._stop_ambience()

    def play_needle_drop(self) -> None:
        # 落针刮擦（进入播放态且载体是黑胶时触发；disabled/未就绪静默忽略）
        if self._enabled and self._needle_drop is not None:
            try:
                self._needle_drop.setVolume(_NEEDLE_DROP_VOLUME)
                self._needle_drop.play()
            except Exception as exc:
                _logger.warning("落针音效播放失败（忽略）: %s", exc)

    def play_tape_mech(self) -> None:
        # 磁带换曲机械声（播放中 TRACK_CHANGED 且载体是磁带时触发）
        if self._enabled and self._tape_mech is not None:
            try:
                self._tape_mech.setVolume(_TAPE_MECH_VOLUME)
                self._tape_mech.play()
            except Exception as exc:
                _logger.warning("磁带机械声播放失败（忽略）: %s", exc)

    def _start_ambience(self) -> None:
        # 启动循环底噪（黑胶 + 响度>0 + 已启用才真正播放）
        if not self._enabled or self._media_kind != "vinyl" or self._intensity <= 0.0:
            return
        if self._crackle is not None and not self._crackle.isPlaying():
            try:
                self._crackle.play()
            except Exception as exc:
                _logger.warning("底噪播放失败（忽略）: %s", exc)

    def _stop_ambience(self) -> None:
        # 停循环底噪（暂停/停止/切载体/档位静音共用出口）
        if self._crackle is not None and self._crackle.isPlaying():
            try:
                self._crackle.stop()
            except Exception as exc:
                _logger.warning("底噪停止失败（忽略）: %s", exc)

    def is_enabled(self) -> bool:
        # 音效是否可用（验证断言用；offscreen/无声卡环境为 False）
        return self._enabled

    def ambience_playing(self) -> bool:
        # 循环底噪是否在播（验证断言用）
        try:
            return self._crackle is not None and self._crackle.isPlaying()
        except Exception:
            return False


# ===== ui/sounds.py 类/函数说明 =====
# SoundKit(QObject): 拟物音效套件（H3；QSoundEffect 封装，fail-soft 整体降级）
#   set_level(level): 档位 → 底噪响度（effects.levels[level].ambience_intensity，宽容解析）
#   set_media_kind(kind): 载体类型切换（黑胶才有底噪；切换即停防串型）
#   set_active(active): 播放态联动（底噪启停；黑胶 + 响度>0 + 启用才播）
#   play_needle_drop()/play_tape_mech(): 一次性音效（载体类型门控；异常吞掉不崩）
#   _build_effect(name): 单效果装配（资源缺失 None；QSoundEffect 异步加载）
#   _start_ambience()/_stop_ambience(): 循环底噪出口（isPlaying 防重复启停）
#   is_enabled()/ambience_playing(): 状态只读（探针断言）
#   设计理由：QtMultimedia 依赖收敛在 ui/sounds.py（engine 的 QMediaPlayer 特许同源例外）；
#     fail-soft 总闸 + 每次播放 try/except 双保险——音效任何失败不影响播放主链路
#   关联配置：effects.json（ambience_intensity 三档）、data/sounds/*.wav（.temp/make_sounds.py 产物）；
#     触发时序（main_window）：state playing→set_active(True)+黑胶→play_needle_drop；
#     TRACK_CHANGED 且播放中且磁带→play_tape_mech
