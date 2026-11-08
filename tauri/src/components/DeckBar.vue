<script setup lang="ts">
// 最小传输条（PL007.5）：播放/暂停切换 + 只读进度条 + 曲目两行文本——事件驱动零轮询
import { computed } from "vue"
import type { ProgressData } from "../lib/types"

const props = defineProps<{
  playing: boolean
  track: { title: string; artist: string } | null
  positionMs: number
  durationMs: number
}>()

const emit = defineEmits<{
  (e: "toggle"): void
}>()

// 进度百分比（时长未知 → 0；PROGRESS 事件驱动，scrub 寻曲 PL009）
const percent = computed(() => {
  if (props.durationMs > 0) {
    return Math.min(100, (props.positionMs / props.durationMs) * 100)
  }
  return 0
})

function fmtTime(ms: number): string {
  // mm:ss（对齐 utils.convert.format_duration 语义）
  const total = Math.floor(ms / 1000)
  const minutes = Math.floor(total / 60)
  const seconds = total % 60
  return `${minutes}:${String(seconds).padStart(2, "0")}`
}
</script>

<template>
  <aside class="deck-bar">
    <div>
      <div class="track-title">{{ track?.title ?? "未载入物品" }}</div>
      <div class="track-artist">{{ track?.artist || "" }}</div>
    </div>
    <div class="progress-track">
      <div class="progress-fill" :style="{ width: `${percent}%` }"></div>
    </div>
    <div class="time-row">
      {{ fmtTime(positionMs) }} / {{ fmtTime(durationMs) }}
    </div>
    <button @click="emit('toggle')">
      {{ playing ? "暂停" : "播放" }}
    </button>
  </aside>
</template>
