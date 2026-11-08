<script setup lang="ts">
// 磨损/风化效果叠加（PL009.7）：A13 效果器语义平移——wear/weathering 贴图 overlay
// 档位 opacity = wear_intensity/weathering_intensity；concise 不渲染
import { computed } from "vue"
import { convertFileSrc } from "@tauri-apps/api/core"

const props = defineProps<{
  level: string
  levels: Record<string, { wear?: boolean; weathering?: boolean; wear_intensity?: number; weathering_intensity?: number }>
  assetRoot: string
}>()

const wearUrl = computed(() =>
  props.levels[props.level]?.wear ? convertFileSrc(`${props.assetRoot}/data/textures/wear.png`) : null,
)
const weatheringUrl = computed(() =>
  props.levels[props.level]?.weathering
    ? convertFileSrc(`${props.assetRoot}/data/textures/weathering.png`)
    : null,
)
const wearOpacity = computed(
  () => props.levels[props.level]?.wear_intensity ?? 0.3,
)
const weatheringOpacity = computed(
  () => props.levels[props.level]?.weathering_intensity ?? 0.5,
)
</script>

<template>
  <div class="effect-overlay">
    <img
      v-if="wearUrl"
      class="effect-img"
      :src="wearUrl"
      :style="{ opacity: wearOpacity }"
      alt=""
      draggable="false"
    />
    <img
      v-if="weatheringUrl"
      class="effect-img"
      :src="weatheringUrl"
      :style="{ opacity: weatheringOpacity }"
      alt=""
      draggable="false"
    />
  </div>
</template>

<style scoped>
.effect-overlay {
  position: absolute;
  inset: 0;
  pointer-events: none;
}

.effect-img {
  position: absolute;
  inset: 0;
  width: 100%;
  height: 100%;
  object-fit: cover;
  mix-blend-mode: overlay;
  user-select: none;
  -webkit-user-drag: none;
}
</style>
