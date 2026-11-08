<script setup lang="ts">
// 唱机列容器（PL009）：DeckStage 拟物 + EffectOverlay 磨损 + 曲目信息 + ProgressSlider + 播放按钮
// wind：scrub 差值方向驱动卷轴快转（±1），松手归零；sideFraction 面内比例换算（deck_view 同式）
import { computed, ref, watch } from "vue"
import { convertFileSrc } from "@tauri-apps/api/core"
import EffectOverlay from "./EffectOverlay.vue"
import ProgressSlider from "./ProgressSlider.vue"
import DeckStage from "./deck/DeckStage.vue"
import type {
  EffectLevel,
  ItemDict,
  ProgressData,
  TrackDict,
} from "../lib/types"

const props = defineProps<{
  item: ItemDict | null
  playing: boolean
  track: TrackDict | null
  progress: ProgressData
  sideFraction: number
  realismLevel: string
  effectLevels: Record<string, EffectLevel>
  assetRoot: string
  itemTypes: Record<string, { name: string; spin_ms_per_rev?: number }>
}>()

const emit = defineEmits<{
  (e: "toggle"): void
  (e: "flip"): void
  (e: "dropItem", itemId: string): void
  (e: "seek", seconds: number): void
  (e: "seekSide", fraction: number): void
  (e: "needleDragStarted"): void
}>()

const DND_MIME = "application/x-mrsir-item-id"

const wind = ref(0)
let scrubLast = 0
let scrubbing = false

function onScrubStarted() {
  scrubbing = true
  scrubLast = scrubValueOf()
}

function scrubValueOf(): number {
  // 最近滑条值（父级 progress 换算回 0-1000——预览值仅方向判定用）
  const dur = props.progress.duration_ms
  if (dur > 0) return Math.round((props.progress.position_ms / dur) * 1000)
  return 0
}

function onScrubMoved(value: number) {
  // wind 方向判定（deck_view._on_scrub_moved 同语义）
  const delta = value - scrubLast
  if (delta !== 0) {
    wind.value = delta > 0 ? 1 : -1
    scrubLast = value
  }
}

function onScrubReleased(seconds: number) {
  scrubbing = false
  wind.value = 0
  emit("seek", seconds)
}

// 载体类型级转速（缺省 2000 对齐 ItemType.spin_ms_per_rev 缺省）
const spinMs = computed(() => {
  if (!props.item) return 2000
  return props.itemTypes[props.item.type.key]?.spin_ms_per_rev ?? 2000
})

// 档位贴图开关（effects.texture）
const textures = computed(() => {
  const level = props.effectLevels[props.realismLevel]
  return level?.texture === true
})

const textureUrls = computed(() => {
  if (!props.assetRoot) return {}
  return {
    vinyl_disc: convertFileSrc(`${props.assetRoot}/data/textures/vinyl_disc.png`),
    cd_disc: convertFileSrc(`${props.assetRoot}/data/textures/cd_disc.png`),
    cassette_shell: convertFileSrc(
      `${props.assetRoot}/data/textures/cassette_shell.png`,
    ),
  }
})

const coverUrl = computed(() =>
  props.item?.cover_path ? convertFileSrc(props.item.cover_path) : null,
)

function onDrop(event: DragEvent) {
  const itemId = event.dataTransfer?.getData(DND_MIME)
  if (itemId) emit("dropItem", itemId)
}
</script>

<template>
  <aside class="deck-bar" @dragover.prevent @drop="onDrop">
    <DeckStage
      :item-type="item?.type.key ?? 'vinyl'"
      :playing="playing"
      :side-progress="sideFraction"
      :spin-ms="spinMs"
      :wind="wind"
      :textures="textures"
      :realism-level="realismLevel"
      :cover-url="coverUrl"
      :texture-urls="textureUrls"
      @needle-drag-started="emit('needleDragStarted')"
      @needle-dropped="(f) => emit('seekSide', f)"
    />
    <EffectOverlay
      :level="realismLevel"
      :levels="effectLevels"
      :asset-root="assetRoot"
    />
    <div class="deck-info">
      <div class="track-title">
        {{ track?.title ?? item?.name ?? "未载入物品" }}
      </div>
      <div class="track-artist">{{ track?.artist || "" }}</div>
    </div>
    <ProgressSlider
      :position-ms="progress.position_ms"
      :duration-ms="progress.duration_ms"
      @scrub-started="onScrubStarted"
      @scrub-moved="onScrubMoved"
      @scrub-released="onScrubReleased"
    />
    <div class="deck-btn-row">
      <button @click="emit('toggle')">
        {{ playing ? "暂停" : "播放" }}
      </button>
      <button @click="emit('flip')">翻面</button>
    </div>
  </aside>
</template>

<style scoped>
.deck-bar {
  /* Grid 内联子项：结构性占右列（不依赖定位/层序/合成层） */
  height: 100%;
  background: var(--mm-surface);
  border-left: 1px solid var(--mm-border);
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 12px;
  padding: 14px;
  position: relative;
}

.deck-info {
  text-align: center;
}

.deck-btn-row {
  display: flex;
  gap: 8px;
}

.deck-bar button {
  width: 96px;
  padding: 8px 0;
  background: var(--mm-primary);
  color: var(--mm-text_on_primary);
  border: 1px solid var(--mm-pressed);
  border-radius: 4px;
  cursor: pointer;
}
</style>
