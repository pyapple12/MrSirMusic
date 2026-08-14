# 泛型重试装饰器（A2.3/B3.1 预留）：指数退避，捕获指定异常，最终失败重抛原异常
# 注：当前无联网/IO 重试场景（预留），供后续网络请求/IO 失败重试使用

import functools
import time
from typing import Callable, ParamSpec, TypeVar, cast

_P = ParamSpec("_P")
_T = TypeVar("_T")


def retry(
    times: int = 3,
    delay: float = 0.1,
    exceptions: tuple[type[Exception], ...] = (Exception,),
) -> Callable[[Callable[_P, _T]], Callable[_P, _T]]:
    # 重试装饰器工厂：指数退避（第 n 次重试前等待 delay * 2^n），捕获指定异常，耗尽后重抛
    # 参数校验（B3.3/C1.2）：times 为 >=1 的整数（排除 bool）、delay 为 >=0 的数字（排除 bool）、exceptions 非空
    if isinstance(times, bool) or not isinstance(times, int) or times < 1:
        raise ValueError("times 必须为 >= 1 的整数")
    if isinstance(delay, bool) or not isinstance(delay, (int, float)) or delay < 0:
        raise ValueError("delay 必须为 >= 0 的数字")
    if not exceptions:
        raise ValueError("exceptions 不能为空")

    def decorator(func: Callable[_P, _T]) -> Callable[_P, _T]:
        @functools.wraps(func)
        def wrapper(*args: _P.args, **kwargs: _P.kwargs) -> _T:
            last_exc: Exception | None = None
            for attempt in range(times):
                try:
                    return func(*args, **kwargs)
                except exceptions as exc:
                    last_exc = exc
                    if attempt < times - 1:
                        time.sleep(delay * (2**attempt))
            if last_exc is not None:
                raise last_exc
            raise RuntimeError("retry 未执行任何尝试")

        return wrapper

    return decorator


# ===== utils/retry.py 函数/常量说明 =====
# retry(times, delay, exceptions) -> 装饰器: 泛型重试工厂
#   逻辑：包装函数按 times 次尝试；捕获 exceptions 指定的异常类型；每次失败后按
#     指数退避等待 delay * 2^attempt；耗尽后重抛最后一次原异常
#   异常：指定异常外的类型不捕获直接上抛（不重试）；最终失败重抛原异常（保持调用方语义）
#   设计理由：指数退避避免瞬时故障风暴；exceptions 参数让调用方精确指定可重试错误
#   （网络/IO 类），逻辑错误（ValueError 等）默认也不重试需显式指定
#   关联配置：无（参数由调用方传入）
