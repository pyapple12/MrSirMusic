# sidecar 进程核心（PL006.1）：QCoreApplication 无头事件循环 + stdio JSON Lines 收发 + 域事件泵 + 生命周期
# 线程模型：stdin 读取在守护线程（行 → Qt 信号跨线程排队），解析/分发/响应/事件写全部在主线程；
# stdout 单写者（锁兜底）；日志走 stderr（logging StreamHandler 默认）+ 文件——stdout 协议流零污染

import json
import sys
import threading
from typing import Any

from PySide6.QtCore import QCoreApplication, QObject, Signal

from config.static.static_config import get_static_config
from modules.library.path_check import mark_missing
from modules.library.repository import increment_play_count, load_all
from modules.playback.engine import PlaybackEngine
from modules.playback.event_bus import subscribe
from modules.playback.events import (
    ERROR,
    PLAYBACK_STATE,
    PROGRESS,
    SIDE_FLIPPED,
    TRACK_CHANGED,
)
from modules.playback.progress import ProgressReporter
from utils.logger import get_logger

from sidecar import protocol as _proto
from sidecar.commands import (
    CommandError,
    _item_to_dict,
    _payload_to_dict,
    execute,
)

# 模块日志（stderr + 文件；不进 stdout 协议流）
_logger = get_logger("sidecar.app")

# 版本快照（ready 握手用；模块加载时取——base.json 单源）
_SC_VERSION = str(get_static_config().base.get("version", "unknown"))


class Session(QObject):
    # 侧车会话：命令分发 + 事件泵 + 优雅退出；信封编解码走 sidecar/protocol 单源

    line_received = Signal(str)  # stdin 行（守护线程 → 主线程排队）
    eof_received = Signal()  # stdin EOF（父进程关闭 = 退出信号）

    def __init__(self) -> None:
        # 会话初始化：引擎/上报器/事件订阅/库缓存空；配置路径与库路径钩子已由 __main__ 先行应用
        super().__init__()
        self.engine = PlaybackEngine()
        self.reporter = ProgressReporter(self.engine)
        self.items: list = []
        self.current_item_id = ""  # 当前载入物品 id（播放计数回写锚点；load_item 命令设置）
        self._stdout_lock = threading.Lock()
        self._line_received_connected = False

    # ── 库与快照 ────────────────────────────────────────────────────────────────
    def refresh_items(self) -> None:
        # 重读库 + 逐件缺失标记（与 Qt 壳 refresh_library 同语义：默认重载不阻塞）
        items = load_all()
        for item in items:
            mark_missing(item)
        self.items = items

    def bootstrap_snapshot(self) -> dict[str, Any]:
        # 前端唯一配置源（PL006 get_bootstrap）：静态四分类 + 用户配置 + 库全量
        # PL009 增 app_root：前端拼贴图/音效绝对路径（convertFileSrc 需绝对路径）
        from config.settings import load_config
        from config.static.static_config import get_static_config
        from utils.paths import project_root

        sc = get_static_config()
        cfg = load_config()
        self.refresh_items()
        return {
            "base": sc.base,
            "ui": sc.ui,
            "effects": sc.effects,
            "item_types": sc.item_types,
            "app_root": str(project_root()),
            "user_config": {
                "realism_level": cfg.realism_level,
                "auto_flip": cfg.auto_flip,
            },
            "items": [
                _item_to_dict(item) for item in self.items
            ],
        }

    # ── 生命周期 ────────────────────────────────────────────────────────────────
    def run(self) -> None:
        # 进程主流程：QCoreApplication → bootstrap → 接线（信号/事件泵）→ ready 握手 → 事件循环
        app = QCoreApplication.instance() or QCoreApplication([])
        self.refresh_items()
        self.line_received.connect(self._handle_line)
        self.eof_received.connect(self._shutdown)
        self._wire_event_pump()
        reader = threading.Thread(target=self._read_stdin_loop, daemon=True)
        reader.start()
        self.emit_event(
            _proto.EV_READY,
            {
                "version": str(_SC_VERSION),
                "items_count": len(self.items),
            },
        )
        app.exec()

    def _shutdown(self) -> None:
        # 优雅退出：停引擎（即时静音，H0.3 同语义）→ 停上报器 → 退出事件循环
        _logger.info("sidecar 收到退出信号，停引擎并退出")
        self.engine.stop()
        self.reporter.shutdown()
        QCoreApplication.instance().quit()

    # ── stdin 接收（守护线程侧） ────────────────────────────────────────────────
    def _read_stdin_loop(self) -> None:
        # 守护线程：按行读 stdin → utf-8 解码 → 信号排队到主线程；EOF → eof_received
        assert sys.stdin is not None and sys.stdin.buffer is not None
        while True:
            raw = sys.stdin.buffer.readline()
            if not raw:
                self.eof_received.emit()
                return
            line = raw.decode("utf-8", errors="replace").strip()
            if line:
                self.line_received.emit(line)

    # ── 命令分发（主线程槽） ────────────────────────────────────────────────────
    def _handle_line(self, line: str) -> None:
        # 单行请求 → 解析 → 分发 → 响应信封；一切异常收敛为错误信封（进程永不因单命令崩溃）
        try:
            request = _proto.parse_line(line)
            if request is None:
                self._write_message(
                    _proto.make_error(0, _proto.CAT_BAD_REQUEST, "请求不是合法 JSON 对象")
                )
                return
            req_id = request.get("id")
            if not isinstance(req_id, int):
                self._write_message(
                    _proto.make_error(0, _proto.CAT_BAD_REQUEST, "请求缺少整数 id")
                )
                return
            cmd = request.get("cmd")
            params = request.get("params")
            if not isinstance(cmd, str):
                self._write_message(
                    _proto.make_error(req_id, _proto.CAT_BAD_REQUEST, "请求缺少 cmd 字符串")
                )
                return
            result = execute(self, cmd, params if isinstance(params, dict) else {})
            self._write_message(_proto.make_result(req_id, result))
        except CommandError as exc:
            req_id = self._last_req_id(line)
            self._write_message(_proto.make_error(req_id, exc.category, str(exc)))
        except Exception as exc:
            _logger.exception("命令执行未分类异常")
            req_id = self._last_req_id(line)
            self._write_message(
                _proto.make_error(req_id, _proto.CAT_INTERNAL, f"内部错误: {type(exc).__name__}")
            )

    @staticmethod
    def _last_req_id(line: str) -> int:
        # 异常路径回捞请求 id（取不到回 0——前端按 id 关联，0 视为可丢弃）
        request = _proto.parse_line(line)
        if request is not None and isinstance(request.get("id"), int):
            return int(request["id"])
        return 0

    # ── 事件泵（event_bus 域事件 → 协议事件） ───────────────────────────────────
    def _wire_event_pump(self) -> None:
        # 订阅五个域事件（映射表单源）；payload 经 commands._payload_to_dict 协议化
        mapping = {
            PROGRESS: _proto.EV_PROGRESS,
            PLAYBACK_STATE: _proto.EV_PLAYBACK_STATE,
            TRACK_CHANGED: _proto.EV_TRACK_CHANGED,
            SIDE_FLIPPED: _proto.EV_SIDE_FLIPPED,
            ERROR: _proto.EV_ERROR,
        }
        for domain_name, wire_name in mapping.items():
            subscribe(domain_name, self._make_pump_callback(wire_name))
        # 播放计数回写（PATCH003）：独立订阅 TRACK_CHANGED（与前端泵并行，互不影响）
        subscribe(TRACK_CHANGED, self._on_track_changed)

    def _make_pump_callback(self, wire_name: str):
        # 生成闭包（默认参数绑定 wire_name——防循环变量迟到绑定）

        def _pump(payload: Any) -> None:
            self.emit_event(wire_name, _payload_to_dict(payload))

        return _pump

    def _on_track_changed(self, _payload: Any) -> None:
        # 播放计数回写（PATCH003 接线）：TRACK_CHANGED 即计一次——载入首曲/自动切曲/手动
        # 切曲/翻面各计（暂停恢复与 seek 不发该事件故不计）；SQL 原子自增 + 会话缓存对象
        # 同步（防陈旧值经 save_item/update_item 写回覆盖）；失败降级日志一次不阻断播放
        if not self.current_item_id:
            return
        try:
            if increment_play_count(self.current_item_id):
                for item in self.items:
                    if item.id == self.current_item_id:
                        item.play_count += 1
                        break
        except Exception:
            _logger.exception("播放计数写库失败（降级忽略，播放不受影响）")

    def emit_event(self, name: str, data: Any = None) -> None:
        # 协议事件写出（ready/library_changed/config_changed + 域事件泵共用出口）
        self._write_message(_proto.make_event(name, data))

    # ── stdout 单写者 ───────────────────────────────────────────────────────────
    def _write_message(self, message: dict[str, Any]) -> None:
        # 信封 → 单行 JSON → stdout（锁兜底 + 逐行 flush；行内禁止换行——json.dumps 天然转义）
        line = _proto.encode_message(message) + "\n"
        with self._stdout_lock:
            sys.stdout.write(line)
            sys.stdout.flush()


# ===== sidecar/app.py 类/函数说明 =====
# Session(QObject): 侧车会话（命令分发/事件泵/生命周期）
#   line_received(str)/eof_received(): 跨线程信号（守护线程 → 主线程排队；Qt 对象只主线程触碰）
#   refresh_items(): 重读库 + mark_missing（与 Qt 壳 refresh_library 同语义）
#   bootstrap_snapshot() -> dict: get_bootstrap 六合快照（base/ui/effects/item_types/user_config/items）
#   run(): QCoreApplication → bootstrap → 接线 → ready → exec（进程入口由 __main__ 调）
#   _shutdown(): engine.stop（H0.3 即时静音同语义）+ reporter.shutdown + quit
#   _read_stdin_loop(): 守护线程按行读 → 解码 → 信号；EOF → eof_received
#   _handle_line(line): 主线程槽——解析/分发/响应；单命令异常收敛为错误信封（进程不因命令崩溃）
#   _last_req_id(line): 异常路径回捞请求 id（回 0 可丢弃）
#   _wire_event_pump(): event_bus 五事件 → 协议事件（映射表单源；闭包默认参防迟到绑定）+ 计数订阅
#   _on_track_changed(payload): 播放计数回写（PATCH003）——TRACK_CHANGED 即计一次（载入/切曲/
#     翻面；暂停恢复与 seek 不计）；increment_play_count SQL 原子自增 + 缓存对象同步；异常降级
#   emit_event(name, data): 事件统一出口（ready/library_changed/config_changed/域事件）
#   _write_message(message): stdout 单写者（锁 + 逐行 flush；JSON Lines 帧纪律）
#   设计理由：Qt 对象主线程纪律（QMediaPlayer/ProgressReporter 均主线程）；stdout 协议流零污染
#     （日志走 stderr + 文件——logging StreamHandler 默认 stderr，FFmpeg 诊断同）；优雅退出 = stdin EOF
#   异常：_handle_line 全捕获（CommandError 分类信封 / Exception internal 信封）；读行解码 errors=replace
#   关联配置：--db/--config 钩子由 __main__ 先行应用；base.json version（ready 握手）
