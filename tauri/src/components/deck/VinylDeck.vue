<script setup lang="ts">
// 黑胶形态（PL009.2/9.3）：贴图转盘旋转 + 唱针 SVG（几何常量自 deck_widget 逐条移植，同源 deckMath）
// 拖针三事件（PL009.3）：27px 命中 → atan2 解卷 → 钳制 → Shift 精调 → 有效窗落针 seekSide / 窗外回臂
import { computed, ref } from "vue"
import {
  ANGLE_RANGE,
  ANGLE_REST,
  ANGLE_START,
  DRAG_MAX,
  DRAG_MIN,
  DROP_MAX,
  DROP_MIN,
  NEEDLE_FINE_STEP,
  PIVOT_X,
  PIVOT_Y,
  pointerAngle,
  unwrapDelta,
} from "../../lib/deckMath"

const props = defineProps<{
  angle: number
  sideProgress: number
  tonearmPos: number
  dragAngle: number | null
  textures: boolean
  realismLevel: string
  textureUrl: string | null
}>()

const emit = defineEmits<{
  (e: "dragStarted"): void
  (e: "dragMove", angleDeg: number): void
  (e: "dragEnd"): void
  (e: "dropped", fraction: number): void
}>()

const root = ref<HTMLElement | null>(null)
const dragging = ref(false)
const dragAngle = ref(ANGLE_REST)
const lastPointerAngle = ref(0)

// 渲染角（deck_widget._visual_angle 同语义）：拖拽角优先，否则静息↔落针按 tonearmPos 插值
const visualAngle = computed(() => {
  if (dragging.value) return dragAngle.value
  const engaged = ANGLE_START + ANGLE_RANGE * props.sideProgress
  return ANGLE_REST + (engaged - ANGLE_REST) * props.tonearmPos
})

// 唱臂端点（deckMath.tipPoint 同式，基于容器实际尺寸）
function endpoints() {
  const el = root.value
  const w = el?.clientWidth ?? 240
  const h = el?.clientHeight ?? 240
  const angleDeg = visualAngle.value
  const pivotX = w * PIVOT_X
  const pivotY = h * PIVOT_Y
  const rad = (angleDeg * Math.PI) / 180
  const length = w * 0.78
  return {
    w,
    h,
    pivot: { x: pivotX, y: pivotY },
    tip: {
      x: pivotX - length * Math.sin(rad),
      y: pivotY + length * Math.cos(rad),
    },
  }
}

function onPointerDown(event: PointerEvent) {
  // 27px 命中判定（deck_widget.mousePressEvent 同法）；未命中静默
  const { tip } = endpoints()
  const dx = event.offsetX - tip.x
  const dy = event.offsetY - tip.y
  if (dx * dx + dy * dy > 27 * 27) return
  dragging.value = true
  dragAngle.value = visualAngle.value
  const { w, h } = endpoints()
  lastPointerAngle.value = pointerAngle(w, h, event.offsetX, event.offsetY)
  emit("dragStarted") // 路由方接 transport_pause（提针停转拟物语义）
  ;(event.target as HTMLElement).setPointerCapture(event.pointerId)
}

function onPointerMove(event: PointerEvent) {
  if (!dragging.value) return
  const { w, h } = endpoints()
  const pointer = pointerAngle(w, h, event.offsetX, event.offsetY)
  const delta = unwrapDelta(lastPointerAngle.value, pointer)
  lastPointerAngle.value = pointer
  const fine = event.shiftKey ? NEEDLE_FINE_STEP : 1
  // 钳制 [_DRAG_MIN, _DRAG_MAX]（deck_widget.mouseMoveEvent 同法）
  dragAngle.value = Math.min(DRAG_MAX, Math.max(DRAG_MIN, dragAngle.value + delta * fine))
  emit("dragMove", dragAngle.value)
}

function onPointerUp() {
  if (!dragging.value) return
  dragging.value = false
  const angle = dragAngle.value
  // 有效窗判定（deck_widget.mouseReleaseEvent 同法）：窗内落针发面内比例，窗外回臂
  const fraction = Math.min(1, Math.max(0, (angle - ANGLE_START) / ANGLE_RANGE))
  if (angle >= DROP_MIN && angle <= DROP_MAX) {
    emit("dropped", fraction)
  }
  emit("dragEnd")
}
</script>

<template>
  <div
    ref="root"
    class="vinyl-stage"
    @pointerdown="onPointerDown"
    @pointermove="onPointerMove"
    @pointerup="onPointerUp"
    @pointercancel="onPointerUp"
  >
    <!-- 转盘：贴图打底（PL009.2）随角旋转；refined 档不叠手绘槽纹防打架 -->
    <div class="disc-rotor" :style="{ transform: `rotate(${angle}deg)` }">
      <img
        v-if="textures && textureUrl"
        class="disc-texture"
        :src="textureUrl"
        alt=""
        draggable="false"
      />
      <div v-else class="disc-fallback"></div>
      <div
        v-if="textures && realismLevel === 'realistic'"
        class="disc-grooves"
      ></div>
    </div>
    <!-- 唱臂：SVG 几何（枢轴/臂杆/唱头/配重，deck_widget._paint_tonearm 同构） -->
    <svg class="tonearm-svg" viewBox="0 0 240 240" preserveAspectRatio="none">
      <line
        class="arm-shadow"
        :x1="240 * PIVOT_X + 2"
        :y1="240 * PIVOT_Y + 2"
        :x2="endpoints().tip.x + 2"
        :y2="endpoints().tip.y + 2"
      />
      <line
        class="arm-body"
        :x1="240 * PIVOT_X"
        :y1="240 * PIVOT_Y"
        :x2="endpoints().tip.x"
        :y2="endpoints().tip.y"
      />
      <circle class="arm-pivot" :cx="240 * PIVOT_X" :cy="240 * PIVOT_Y" r="6" />
      <rect
        class="arm-head"
        :x="endpoints().tip.x - 3"
        :y="endpoints().tip.y - 6"
        width="6"
        height="12"
        :transform="`rotate(${-visualAngle} ${endpoints().tip.x} ${endpoints().tip.y})`"
      />
    </svg>
  </div>
</template>

<style scoped>
.vinyl-stage {
  position: absolute;
  inset: 0;
  touch-action: none;
}

.disc-rotor {
  position: absolute;
  left: 50%;
  top: 50%;
  width: 78%;
  height: 78%;
  margin-left: -39%;
  margin-top: -39%;
  border-radius: 50%;
  overflow: hidden;
  border: 1px solid #555;
}

.disc-texture {
  width: 100%;
  height: 100%;
  object-fit: cover;
  user-select: none;
  -webkit-user-drag: none;
}

.disc-fallback {
  width: 100%;
  height: 100%;
  background: radial-gradient(circle, #3a3a3a 0%, #0d0d0d 100%);
}

.disc-grooves {
  position: absolute;
  inset: 0;
  border-radius: 50%;
  background: repeating-radial-gradient(
    circle at center,
    transparent 0 6px,
    rgba(0, 0, 0, 0.25) 6px 7px
  );
}

.tonearm-svg {
  position: absolute;
  inset: 0;
  width: 100%;
  height: 100%;
  pointer-events: none;
}

.arm-shadow {
  stroke: rgba(0, 0, 0, 0.35);
  stroke-width: 5;
}

.arm-body {
  stroke: #c8c8c8;
  stroke-width: 4;
}

.arm-pivot {
  fill: #9a9a9a;
  stroke: #666;
}

.arm-head {
  fill: #b0b0b0;
  stroke: #555;
}
</style>
