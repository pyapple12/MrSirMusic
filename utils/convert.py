# 格式转换工具模块（A2.4/B3.1 预留）：时长显示/毫秒换算/float32 占位（为后续音频处理预留）

from typing import Any


def format_duration(seconds: int | float) -> str:
    # 秒数 → "mm:ss" 显示格式（分钟自然位数，秒两位补零；负值按 0 处理，防御非法输入）
    total = max(0, int(seconds))
    m, s = divmod(total, 60)
    return f"{m}:{s:02d}"


def seconds_from_ms(ms: int | float) -> float:
    # 毫秒 → 秒（float，保留小数精度）
    return float(ms) / 1000.0


def progress_percent(position_ms: int, duration_ms: int) -> int:
    # 进度百分比换算（钳制 0-100，C2.3；总时长 0/非正返回 0）：进度显示唯一实现（B1.4 去重）
    if duration_ms <= 0:
        return 0
    return min(100, int(position_ms * 100 / duration_ms))


def to_float32(audio: Any) -> Any:
    # 占位：后续音频处理时实现统一 (N, 2) float32 [-1, 1] @ 44100Hz 转换；当前原样返回
    return audio


# ===== utils/convert.py 函数/常量说明 =====
# format_duration(seconds) -> str: 秒数格式化
#   逻辑：负数钳制 0 → divmod(60) → "mm:ss"（分钟自然位数，秒两位补零）
# seconds_from_ms(ms) -> float: 毫秒 → 秒（1000 除法，保留小数）
# progress_percent(position_ms, duration_ms) -> int: 进度百分比（0-100）
#   逻辑：duration <= 0 返回 0；否则 int(position*100/duration)
#   设计理由：进度换算单点实现（B1.4 去重），ProgressWidget 等统一引用
# to_float32(audio) -> Any: float32 转换占位（A9 预留）
#   关联配置：无（44100Hz 约定见 base.json sample_rate）
