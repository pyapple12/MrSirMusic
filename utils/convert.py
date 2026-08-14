# 格式转换工具模块（A2.4）：时长显示/毫秒换算/float32 占位（为后续音频处理预留）

from typing import Any


def format_duration(seconds: int | float) -> str:
    # 秒数 → "mm:ss" 显示格式（分钟自然位数，秒两位补零；负值按 0 处理，防御非法输入）
    total = max(0, int(seconds))
    m, s = divmod(total, 60)
    return f"{m}:{s:02d}"


def seconds_from_ms(ms: int | float) -> float:
    # 毫秒 → 秒（float，保留小数精度）
    return float(ms) / 1000.0


def to_float32(audio: Any) -> Any:
    # 占位：后续音频处理时实现统一 (N, 2) float32 [-1, 1] @ 44100Hz 转换；当前原样返回
    return audio


# ===== utils/convert.py 函数/常量说明 =====
# format_duration(seconds) -> str: 秒数格式化
#   逻辑：负数钳制 0 → divmod(60) → "mm:ss"（分钟/秒各两位）
#   异常：非数值输入由 int() 抛出（调用方保证数值类型；字符串数字可弹性转换）
# seconds_from_ms(ms) -> float: 毫秒 → 秒（1000 除法，保留小数，进度条显示用）
# to_float32(audio) -> Any: float32 转换占位
#   设计理由：音频数组约定 (N, 2) float32 [-1, 1] @ 44100Hz（AGENTS.md），
#     第一版无 numpy 依赖，函数先占位供 A9 播放核心接入时实现
#   关联配置：无（44100Hz 约定见 base.json sample_rate）
