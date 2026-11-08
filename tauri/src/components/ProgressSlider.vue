<script setup lang="ts">
// 进度滑条（PL009.5）：scrub 三态——拖动挂起外部回写 + 时间预览、松手发曲内秒数（H5 语义平移）
// 0-1000 千分位值域对齐 Qt ProgressWidget；wind 方向由父级按 scrubMoved 差值判定
import { computed, ref } from "vue"

const props = defineProps<{
  positionMs: number
  durationMs: number
}>()

const emit = defineEmits<{
  (e: "scrubStarted"): void
  (e: "scrubMoved", value: number): void
  (e: "scrubReleased", seconds: number): void
}>()

const MAX = 1000
const scrubbing = ref(false)
const scrubValue = ref(0)

// 非拖动时跟随外部进度（百分比 0-100 缩放 0-1000 值域）
const barValue = computed(() => {
  if (scrubbing.value) return scrubValue.value
  if (props.durationMs > 0) {
    return Math.min(MAX, Math.max(0, (props.positionMs / props.durationMs) * MAX))
  }
  return 0
})

function onDown() {
  scrubbing.value = true
  scrubValue.value = barValue.value
  emit("scrubStarted")
}

function onMove() {
  emit("scrubMoved", scrubValue.value)
}

function onUp() {
  // 松手：值换算曲内秒数（deck_view._on_scrub_released 同式）→ seek
  scrubbing.value = false
  const seconds = Math.max(
    0,
    Math.round((props.durationMs / 1000) * (scrubValue.value / MAX)),
  )
  emit("scrubReleased", seconds)
}

function fmtTime(ms: number): string {
  const total = Math.floor(ms / 1000)
  const minutes = Math.floor(total / 60)
  const seconds = total % 60
  return `${minutes}:${String(seconds).padStart(2, "0")}`
}

// 时间文本：scrub 中按滑条比例预览（ProgressWidget._on_moved 同语义）
const timeText = computed(() => {
  const posMs = scrubbing.value
    ? (props.durationMs > 0 ? props.durationMs * (scrubValue.value / MAX) : 0)
    : props.positionMs
  return `${fmtTime(posMs)} / ${fmtTime(props.durationMs)}`
})
</script>

<template>
  <div class="slider-row">
    <input
      class="progress-slider"
      type="range"
      min="0"
      :max="MAX"
      :value="barValue"
      @pointerdown="onDown"
      @input="onMove"
      @change="onUp"
      @pointerup="onUp"
    />
    <span class="slider-time">{{ timeText }}</span>
  </div>
</template>

<style scoped>
.slider-row {
  display: flex;
  align-items: center;
  gap: 10px;
  width: 100%;
}

.progress-slider {
  flex: 1;
  accent-color: var(--mm-primary);
  cursor: pointer;
}

.slider-time {
  font-size: 11px;
  color: var(--mm-muted);
  white-space: nowrap;
}
</style>
