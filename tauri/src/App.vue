<script setup lang="ts">
// App 壳（PL007.4/5）：启动取 bootstrap → 主题 + 库渲染；订阅协议事件驱动传输条；dead → 错误横幅
import { onMounted, ref } from "vue"
import { onSidecarDead, onSidecarEvent, sidecarCmd } from "./lib/ipc"
import { applyTheme } from "./lib/theme"
import type {
  Bootstrap,
  ItemDict,
  ProgressData,
  TrackChangedData,
} from "./lib/types"
import DeckBar from "./components/DeckBar.vue"
import ShelfView from "./views/ShelfView.vue"

const items = ref<ItemDict[]>([])
const loading = ref(true)
const dead = ref(false)
const playing = ref(false)
const currentTrack = ref<{ title: string; artist: string } | null>(null)
const progress = ref<ProgressData>({ position_ms: 0, duration_ms: 0 })

onMounted(async () => {
  // 事件先订阅（防 bootstrap 前丢事件），再取快照
  await onSidecarEvent((evt) => {
    if (evt.event === "playback_state") {
      const data = evt.data as { state: string }
      playing.value = data.state === "playing"
    } else if (evt.event === "track_changed") {
      const data = evt.data as TrackChangedData
      currentTrack.value = data.track
        ? { title: data.track.title, artist: data.track.artist }
        : null
    } else if (evt.event === "progress") {
      progress.value = evt.data as ProgressData
    }
  })
  await onSidecarDead(() => {
    dead.value = true
  })
  try {
    const boot = await sidecarCmd<Bootstrap>("get_bootstrap")
    applyTheme(boot)
    items.value = boot.items
  } catch (reason) {
    dead.value = true
    console.warn("bootstrap 失败:", reason)
  }
  loading.value = false
})

async function playItem(item: ItemDict) {
  // 点卡片 → 载入 + 播放（PL007.5 端到端闭环核心交互）
  try {
    await sidecarCmd("load_item", { item_id: item.id })
    await sidecarCmd("transport_play")
  } catch (reason) {
    console.warn("播放失败:", reason)
  }
}
</script>

<template>
  <div v-if="dead" class="dead-banner">
    侧车后端未连接——播放与库功能暂不可用（已尝试重启，请重启应用排查环境）
  </div>
  <main>
    <ShelfView :items="items" :loading="loading" @play="playItem" />
  </main>
  <DeckBar
    :playing="playing"
    :track="currentTrack"
    :position-ms="progress.position_ms"
    :duration-ms="progress.duration_ms"
    @toggle="playing ? sidecarCmd('transport_pause') : sidecarCmd('transport_play')"
  />
</template>
