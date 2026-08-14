# 事件总线（A9.2/B3.8）：极简订阅/发布，回调异常隔离（记日志），订阅去重，支持退订

from typing import Any, Callable

from utils.logger import get_logger

# 模块日志
_logger = get_logger("playback.event_bus")

# 订阅表：事件名 → 回调列表
_subscribers: dict[str, list[Callable[[Any], None]]] = {}


def subscribe(event: str, callback: Callable[[Any], None]) -> Callable[[], None]:
    # 订阅事件（同一回调去重，B3.8）：返回退订函数（调用后不再收到该事件）
    callbacks = _subscribers.setdefault(event, [])
    if callback not in callbacks:
        callbacks.append(callback)
    return lambda: _unsubscribe(event, callback)


def _unsubscribe(event: str, callback: Callable[[Any], None]) -> None:
    # 内部退订：从回调列表移除（不存在则忽略）
    callbacks = _subscribers.get(event)
    if callbacks and callback in callbacks:
        callbacks.remove(callback)


def emit(event: str, payload: Any = None) -> None:
    # 发布事件：遍历回调逐个调用；单回调异常记日志并隔离（不影响其他回调，不向上抛）
    for callback in list(_subscribers.get(event, [])):
        try:
            callback(payload)
        except Exception as exc:
            _logger.warning("事件回调异常（已隔离）: %s: %s", event, exc)


# ===== modules/playback/event_bus.py 函数/常量说明 =====
# _subscribers: 订阅表（事件名 → 回调列表；list 快照防迭代中修改）
# subscribe(event, callback) -> Callable: 订阅并返回退订闭包（幂等安全）
# _unsubscribe(event, callback): 内部移除（不存在静默）
# emit(event, payload): 发布
#   逻辑：复制回调列表遍历（快照防回调内退订报错）→ 逐个调用
#   异常：回调异常捕获忽略（事件总线不因监听器错误崩溃，fail-soft）
#   设计理由：模块间解耦（engine/progress/UI 桥各自订阅），极简无依赖
#   关联配置：无（事件名见 events.py）
