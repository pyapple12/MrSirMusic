// 拟物绘制数学（PL009.1）：常量与公式逐条自 ui/widgets/parts.py 与 ui/widgets/deck_widget.py 移植
// 同源约定：本文件与 Qt 侧参数一一对应（改一处必须同步另一处）；几何坐标均为容器矩形比例

// 带卷半径物理因子上下界（parts.py REEL_RADIUS_MIN/MAX）
export const REEL_RADIUS_MIN = 44.0
export const REEL_RADIUS_MAX = 77.0
// 播放基准角速度（度/秒，parts.py REEL_BASE_SPEED）
export const REEL_BASE_SPEED = 240.0
// scrub 快进/倒带角速度基准（record_widget.py _REEL_WIND_SPEED）
export const REEL_WIND_SPEED = 900.0
// 转盘惯性趋近系数（deck_widget.py _SPIN_EASE）
export const SPIN_EASE = 2.2
// 唱臂几何（deck_widget.py _PIVOT_X/_PIVOT_Y/_ARM_LENGTH）
export const PIVOT_X = 0.88
export const PIVOT_Y = 0.1
export const ARM_LENGTH = 0.78
// 落针角/扫过角/静息角（deck_widget.py _ANGLE_START/_ANGLE_RANGE/_ANGLE_REST）
export const ANGLE_START = 8.0
export const ANGLE_RANGE = 24.0
export const ANGLE_REST = -4.0
// 拖拽角度钳制（deck_widget.py _DRAG_MIN/_DRAG_MAX）
export const DRAG_MIN = -8.0
export const DRAG_MAX = ANGLE_START + ANGLE_RANGE + 12.0
// 有效落针窗（deck_widget.py _DROP_MIN/_DROP_MAX）
export const DROP_MIN = ANGLE_START - 2.0
export const DROP_MAX = ANGLE_START + ANGLE_RANGE + 2.0
// 唱针命中半径（deck_widget.py _HIT_RADIUS，像素）
export const HIT_RADIUS = 27.0
// Shift 精调系数（deck_widget.py _NEEDLE_FINE_STEP）
export const NEEDLE_FINE_STEP = 0.1
// 落针动画时长（与 Qt 版 deck_widget 常量同源；ui.json animation 死键已清理，此处为唯一事实源）
export const TONEARM_DROP_MS = 500

// 带卷半径因子：sqrt(44² + (77²-44²)×fill)——卷多因子大（parts.py reel_factor 同式）
export function reelFactor(fill: number): number {
  const f = Math.min(1, Math.max(0, fill))
  return Math.sqrt(
    REEL_RADIUS_MIN ** 2 + (REEL_RADIUS_MAX ** 2 - REEL_RADIUS_MIN ** 2) * f,
  )
}

// 转盘目标角速度（度/秒）＝每转毫秒换算（deck_widget._tick 同式）
export function spinTargetDegPerSec(spinMs: number): number {
  return 3600000 / Math.max(1, spinMs)
}

// 惯性缓动一步：current += (target-current)×min(1, dt×k)（deck_widget._tick 同式）
export function easeStep(
  current: number,
  target: number,
  dt: number,
  k = SPIN_EASE,
): number {
  return current + (target - current) * Math.min(1, dt * k)
}

// 唱针尖端坐标：枢轴 + 臂长×(-sin 角, +cos 角)（deck_widget._tip_point 同式，角 0 = 正下方）
export function tipPoint(
  width: number,
  height: number,
  angleDeg: number,
): { x: number; y: number } {
  const pivotX = width * PIVOT_X
  const pivotY = height * PIVOT_Y
  const rad = (angleDeg * Math.PI) / 180
  const length = width * ARM_LENGTH
  return {
    x: pivotX - length * Math.sin(rad),
    y: pivotY + length * Math.cos(rad),
  }
}

// 指针绕枢轴角（度）：atan2(枢轴x-指针x, 指针y-枢轴y)——与唱针角坐标系同源
export function pointerAngle(
  width: number,
  height: number,
  px: number,
  py: number,
): number {
  const pivotX = width * PIVOT_X
  const pivotY = height * PIVOT_Y
  return (Math.atan2(pivotX - px, py - pivotY) * 180) / Math.PI
}

// 角度解卷：±180° 内取增量（deck_widget.mouseMoveEvent 同法）
export function unwrapDelta(prev: number, next: number): number {
  let delta = next - prev
  if (delta > 180) delta -= 360
  else if (delta < -180) delta += 360
  return delta
}
