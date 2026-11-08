<script setup lang="ts">
// 拟物唱机分派容器（PL009.1）：rAF 动画中枢——转盘惯性缓动/收敛自停 + 卷轴恒线速 + 落针插值
// 常量与公式走 lib/deckMath（同源 Qt deck_widget/parts）；按 itemType 分派三形态子组件
import { computed, onBeforeUnmount, ref, watch } from "vue"
import {
  REEL_BASE_SPEED,
  REEL_WIND_SPEED,
  TONEARM_DROP_MS,
  easeStep,
  reelFactor,
  spinTargetDegPerSec,
} from "../../lib/deckMath"
import CassetteDeck from "./CassetteDeck.vue"
import CdDeck from "./CdDeck.vue"
import VinylDeck from "./VinylDeck.vue"

const props = defineProps<{
  itemType: string
  playing: boolean
  sideProgress: number // 面内进度 0-1（唱针/卷轴共用）
  spinMs: number // 类型级转速（item_types.spin_ms_per_rev）
  wind: number // scrub 方向（±1，静止 0）
  textures: boolean // 档位贴图开关（effects.texture）
  realismLevel: string
  coverUrl: string | null
  textureUrls: Record<string, string> // 键→convertFileSrc 绝对 URL（vinyl_disc/cd_disc/cassette_shell）
}>()

const emit = defineEmits<{
  (e: "needleDragStarted"): void
  (e: "needleDropped", fraction: number): void
}>()

// 动画状态（rAF 单中枢驱动；数值经 props 下发子组件）
const angle = ref(0)
const spinSpeed = ref(0)
const reelL = ref(0)
const reelR = ref(0)
const tonearmPos = ref(0) // 0=抬起 1=落下
const dragAngle = ref<number | null>(null) // 拖拽中唱针角（null=非拖拽）

let rafId: number | null = null
let lastTs = 0

function frame(ts: number) {
  const dt = lastTs ? Math.min(0.1, (ts - lastTs) / 1000) : 0.03
  lastTs = ts
  // 转盘角速度惯性趋近（deckMath.easeStep，SPIN_EASE 同源）
  const target = props.playing ? spinTargetDegPerSec(props.spinMs) : 0
  spinSpeed.value = easeStep(spinSpeed.value, target, dt)
  if (Math.abs(spinSpeed.value) > 0.02) {
    angle.value = (angle.value + spinSpeed.value * dt) % 360
  }
  // 卷轴恒线速（scrub wind 覆盖基准；同源 deck_widget._tick/record_widget._tick）
  const base = Math.abs(props.wind) > 0.01 ? props.wind * REEL_WIND_SPEED : REEL_BASE_SPEED
  reelL.value =
    (reelL.value - (dt * base) / reelFactor(1 - props.sideProgress)) % 360
  reelR.value =
    (reelR.value - (dt * base) / reelFactor(props.sideProgress)) % 360
  // 落针插值（deck_widget 落针步进：dt/dropMs；拖拽中不抢控制权）
  if (dragAngle.value === null) {
    const target = props.playing ? 1 : 0
    const step = dt / (TONEARM_DROP_MS / 1000)
    tonearmPos.value =
      tonearmPos.value < target
        ? Math.min(target, tonearmPos.value + step)
        : Math.max(target, tonearmPos.value - step)
  }
  rafId = requestAnimationFrame(frame)
}

function ensureLoop() {
  if (rafId === null) {
    lastTs = 0
    rafId = requestAnimationFrame(frame)
  }
}

watch(
  () => props.playing,
  (playing) => {
    if (playing) ensureLoop()
    else if (!dragging()) {
      // 收敛自停交给 frame 末判定（deck_widget._tick 同语义：拖拽中不停）
    }
  },
  { immediate: true },
)

function dragging(): boolean {
  return dragAngle.value !== null
}

// 收敛自停（FIX006.5 同语义）：非播放+非拖拽+速度归零+落针到位 → 停 rAF
watch([spinSpeed, tonearmPos], () => {
  if (
    rafId !== null &&
    !props.playing &&
    !dragging() &&
    Math.abs(spinSpeed.value) <= 0.02 &&
    ((props.playing && tonearmPos.value === 1) || tonearmPos.value === 0)
  ) {
    if (rafId !== null) cancelAnimationFrame(rafId)
    rafId = null
  }
})

onBeforeUnmount(() => {
  if (rafId !== null) cancelAnimationFrame(rafId)
  rafId = null
})

function onDragStart() {
  dragAngle.value = visualAngle()
  emit("needleDragStarted")
  ensureLoop()
}

function onDragMove(angleDeg: number) {
  dragAngle.value = angleDeg
}

function onDragEnd() {
  dragAngle.value = null
  ensureLoop()
}

// 拖拽中的渲染角（deck_widget._visual_angle 同语义：拖拽角优先，否则插值）
const visualAngle = computed(() => angle.value)

// 进度变化重绘触发（sideProgress 经 props 已响应式下发）

const activeForm = computed(() =>
  props.itemType === "cassette"
    ? "cassette"
    : props.itemType === "cd"
      ? "cd"
      : "vinyl",
)
</script>

<template>
  <div class="deck-stage">
    <VinylDeck
      v-if="activeForm === 'vinyl'"
      :angle="angle"
      :side-progress="sideProgress"
      :tonearm-pos="tonearmPos"
      :drag-angle="dragAngle"
      :textures="textures"
      :realism-level="realismLevel"
      :texture-url="textureUrls.vinyl_disc ?? null"
      @drag-started="onDragStart"
      @drag-move="onDragMove"
      @drag-end="onDragEnd"
      @dropped="emit('needleDropped', $event)"
    />
    <CassetteDeck
      v-else-if="activeForm === 'cassette'"
      :angle="angle"
      :side-progress="sideProgress"
      :reel-l="reelL"
      :reel-r="reelR"
      :playing="playing"
      :textures="textures"
      :texture-url="textureUrls.cassette_shell ?? null"
    />
    <CdDeck
      v-else
      :angle="angle"
      :side-progress="sideProgress"
      :textures="textures"
      :realism-level="realismLevel"
      :texture-url="textureUrls.cd_disc ?? null"
      :cover-url="coverUrl"
    />
  </div>
</template>

<style scoped>
.deck-stage {
  width: 240px;
  height: 240px;
  position: relative;
}
</style>
