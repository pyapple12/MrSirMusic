<script setup lang="ts">
// App 壳（PL009）：双视图管理面 + 拟物唱机列（DeckStage/磨损/滑条）+ Web Audio 音效 + 库同步
// 音效语义（ui/sounds.py 平移）：底噪循环随播放态启停（vinyl 门控）、落针在播放迁移沿、磁带换曲机械声
import { computed, onBeforeUnmount, onMounted, ref, watch } from "vue"
import {
  onSidecarDead,
  onSidecarEvent,
  parseSidecarError,
  sidecarCmd,
} from "./lib/ipc"
import { applyTheme } from "./lib/theme"
import { soundKit } from "./lib/sounds"
import type {
  Bootstrap,
  EffectLevel,
  ItemDict,
  ItemTypeConfig,
  ProgressData,
  TrackChangedData,
  UserConfigData,
} from "./lib/types"
import ContextMenu, { type MenuItem } from "./components/ContextMenu.vue"
import ConfirmModal from "./components/ConfirmModal.vue"
import DeckBar from "./components/DeckBar.vue"
import ImportDialog from "./dialogs/ImportDialog.vue"
import PromptModal from "./components/PromptModal.vue"
import SettingsDialog from "./dialogs/SettingsDialog.vue"
import ShelfView from "./views/ShelfView.vue"
import LibraryView from "./views/LibraryView.vue"

const items = ref<ItemDict[]>([])
const loading = ref(true)
const dead = ref(false)
const playing = ref(false)
const currentTrack = ref<TrackDict | null>(null)
const currentItemId = ref<string | null>(null)
const sideOffset = ref<number | null>(null)
const sideTotal = ref<number | null>(null)
const progress = ref<ProgressData>({ position_ms: 0, duration_ms: 0 })
const userConfig = ref<UserConfigData>({ realism_level: "refined", auto_flip: false })
const effectLevels = ref<Record<string, EffectLevel>>({})
const itemTypes = ref<Record<string, ItemTypeConfig>>({})
const assetRoot = ref("")
const activeTab = ref<"library" | "shelf">("library")
const lastState = ref("stopped")

// 对话框/菜单/模态状态（PL008 语义保留）
const showImport = ref(false)
const showSettings = ref(false)
const contextState = ref<{ x: number; y: number; item: ItemDict } | null>(null)
const renameState = ref<{ item: ItemDict } | null>(null)
const deleteState = ref<{ item: ItemDict } | null>(null)

const currentItem = computed(
  () => items.value.find((item) => item.id === currentItemId.value) ?? null,
)

// 面内比例（deck_view._side_fraction 同语义）：面时长可用用面内，否则退单曲内
const sideFraction = computed(() => {
  const posSec = progress.value.position_ms / 1000
  if (sideOffset.value !== null && sideTotal.value && sideTotal.value > 0) {
    return Math.min(1, Math.max(0, (sideOffset.value + posSec) / sideTotal.value))
  }
  if (progress.value.duration_ms > 0) {
    return Math.min(
      1,
      Math.max(0, posSec / (progress.value.duration_ms / 1000)),
    )
  }
  return 0
})

// 消息条（瞬态提示：info/error，4s 自清）
const message = ref<{ text: string; kind: "info" | "error" } | null>(null)
let messageTimer: ReturnType<typeof setTimeout> | null = null

function showMessage(text: string, kind: "info" | "error" = "info") {
  message.value = { text, kind }
  if (messageTimer) clearTimeout(messageTimer)
  messageTimer = setTimeout(() => (message.value = null), 4000)
}

function itemTypeOf(itemId: string | null): string | null {
  const item = items.value.find((i) => i.id === itemId)
  return item?.type.key ?? null
}

onMounted(async () => {
  // 事件先订阅（防 bootstrap 前丢事件），再取快照
  await onSidecarEvent((evt) => {
    if (evt.event === "playback_state") {
      const data = evt.data as { state: string }
      playing.value = data.state === "playing"
      // H3 音效联动：底噪启停 + 播放迁移沿落针（vinyl 门控）
      soundKit.setActive(data.state === "playing")
      if (data.state === "playing" && lastState.value !== "playing" && isVinyl()) {
        soundKit.playNeedleDrop()
      }
      lastState.value = data.state
    } else if (evt.event === "track_changed") {
      const data = evt.data as TrackChangedData
      currentTrack.value = data.track
      sideOffset.value = data.side_offset_seconds
      sideTotal.value = data.side_total_seconds
      // H3：播放中磁带换曲机械声
      if (
        playing.value &&
        itemTypeOf(currentItemId.value) === "cassette"
      ) {
        soundKit.playTapeMech()
      }
    } else if (evt.event === "progress") {
      progress.value = evt.data as ProgressData
    } else if (evt.event === "error") {
      // parity ⑧：缺失文件等播放错误 → 消息条提示（不崩溃）
      const data = evt.data as { category?: string; message?: string }
      showMessage(`提示：${data?.message ?? "播放错误"}`, "error")
    } else if (evt.event === "side_flipped") {
      // H3：黑胶翻面落针音
      if (isVinyl()) soundKit.playNeedleDrop()
    } else if (evt.event === "library_changed") {
      // PL008.4：库同步——重取（保留旧视图直到成功，沿用既有刷新原则）
      refreshLibrary()
    } else if (evt.event === "config_changed") {
      userConfig.value = evt.data as UserConfigData
      soundKit.setLevel(
        (effectLevels.value[userConfig.value.realism_level] as EffectLevel)
          ?.ambience_intensity ?? 0.4,
      )
    }
  })
  await onSidecarDead(() => {
    dead.value = true
  })
  try {
    const boot = await sidecarCmd<Bootstrap>("get_bootstrap")
    applyTheme(boot)
    items.value = boot.items
    userConfig.value = boot.user_config
    effectLevels.value = boot.effects.levels as Record<
      string,
      EffectLevel
    >
    itemTypes.value = boot.item_types as Record<
      string,
      ItemTypeConfig
    >
    assetRoot.value = boot.app_root ?? ""
    soundKit.setAssetRoot(assetRoot.value)
    soundKit.setLevel(
      (effectLevels.value[userConfig.value.realism_level] as EffectLevel)
        ?.ambience_intensity ?? 0.4,
    )
  } catch (reason) {
    dead.value = true
    console.warn("bootstrap 失败:", reason)
  }
  loading.value = false
})

function isVinyl(): boolean {
  return itemTypeOf(currentItemId.value) === "vinyl"
}

async function refreshLibrary() {
  // 库重取：请求成功才替换 items（失败保留旧视图）
  try {
    const fresh = await sidecarCmd<{ items: ItemDict[] }>("list_items")
    items.value = fresh.items
  } catch (reason) {
    console.warn("库刷新失败（保留旧视图）:", reason)
  }
}

async function playItem(item: ItemDict) {
  // 点卡片/菜单播放 → 载入 + 播放 + 音效载体切换（H3）
  try {
    currentItemId.value = item.id
    soundKit.setMediaKind(item.type.key)
    await sidecarCmd("load_item", { item_id: item.id })
    await sidecarCmd("transport_play")
  } catch (reason) {
    const info = parseSidecarError(reason)
    showMessage(`播放失败（${info.category}）：${info.message}`, "error")
  }
}

async function dropPlay(itemId: string) {
  // 卡片拖入唱机放置区（PL008.4）
  const item = items.value.find((i) => i.id === itemId)
  if (item) {
    await playItem(item)
  }
}

// ── 右键菜单动作（PL008.1） ─────────────────────────────────────────────────────
function menuFor(item: ItemDict): MenuItem[] {
  return [
    { label: "播放", action: () => playItem(item) },
    { label: "编辑", action: () => (renameState.value = { item }) },
    { label: "重新刻录", action: () => regenerateItem(item) },
    { label: "删除", danger: true, action: () => (deleteState.value = { item }) },
  ]
}

async function regenerateItem(item: ItemDict) {
  try {
    const fresh = await sidecarCmd<{ id: string; name: string }>("regenerate", {
      item_id: item.id,
    })
    showMessage(`重新刻录成功：${fresh.name}`)
  } catch (reason) {
    const info = parseSidecarError(reason)
    showMessage(`重新刻录失败（${info.category}）：${info.message}`, "error")
  }
}

async function submitRename(item: ItemDict, name: string) {
  try {
    await sidecarCmd("rename_item", { item_id: item.id, name })
    showMessage(`已改名：${name}`)
  } catch (reason) {
    showMessage(`改名失败：${parseSidecarError(reason).message}`, "error")
  } finally {
    renameState.value = null
  }
}

async function submitDelete(item: ItemDict) {
  try {
    await sidecarCmd("delete_item", { item_id: item.id })
    showMessage(`已删除：${item.name}`)
  } catch (reason) {
    showMessage(`删除失败：${parseSidecarError(reason).message}`, "error")
  } finally {
    deleteState.value = null
  }
}

// ── 快捷键（PL008.4：Space/←/→/F，输入类焦点豁免） ─────────────────────────────
function isTypingTarget(target: EventTarget | null): boolean {
  const el = target as HTMLElement | null
  if (!el) return false
  const tag = el.tagName
  return (
    tag === "INPUT" ||
    tag === "TEXTAREA" ||
    tag === "SELECT" ||
    el.isContentEditable
  )
}

function onKeydown(e: KeyboardEvent) {
  if (isTypingTarget(e.target) || e.isComposing || dead.value) return
  if (e.code === "Space") {
    e.preventDefault()
    playing.value ? sidecarCmd("transport_pause") : sidecarCmd("transport_play")
  } else if (e.code === "ArrowLeft") {
    e.preventDefault()
    sidecarCmd("transport_prev")
  } else if (e.code === "ArrowRight") {
    e.preventDefault()
    sidecarCmd("transport_next")
  } else if (e.code === "KeyF") {
    e.preventDefault()
    sidecarCmd("transport_flip")
  }
}

onMounted(() => {
  window.addEventListener("keydown", onKeydown)
})

onBeforeUnmount(() => {
  window.removeEventListener("keydown", onKeydown)
  soundKit.setActive(false)
})
</script>

<template>
  <div v-if="dead" class="dead-banner">
    侧车后端未连接——播放与库功能暂不可用（已尝试重启，请重启应用排查环境）
  </div>
  <div v-if="message" class="message-bar" :class="message.kind">
    {{ message.text }}
  </div>
  <main>
    <div class="tab-bar">
      <button
        class="tab-btn"
        :class="{ active: activeTab === 'library' }"
        @click="activeTab = 'library'"
      >
        物品库
      </button>
      <button
        class="tab-btn"
        :class="{ active: activeTab === 'shelf' }"
        @click="activeTab = 'shelf'"
      >
        置物架
      </button>
      <div class="tab-spacer"></div>
      <button class="btn-ghost tab-action" @click="showImport = true">
        导入/生成…
      </button>
      <button class="btn-ghost tab-action" @click="showSettings = true">
        设置…
      </button>
    </div>
    <LibraryView
      v-if="activeTab === 'library'"
      :items="items"
      :loading="loading"
      @play="playItem"
      @context="contextState = $event"
    />
    <ShelfView
      v-else
      :items="items"
      :loading="loading"
      @play="playItem"
    />
  </main>
  <DeckBar
    :item="currentItem"
    :playing="playing"
    :track="currentTrack"
    :progress="progress"
    :side-fraction="sideFraction"
    :realism-level="userConfig.realism_level"
    :effect-levels="effectLevels"
    :asset-root="assetRoot"
    :item-types="itemTypes"
    @toggle="playing ? sidecarCmd('transport_pause') : sidecarCmd('transport_play')"
    @flip="sidecarCmd('transport_flip')"
    @drop-item="dropPlay"
    @seek="(s) => sidecarCmd('seek', { seconds: s })"
    @seek-side="(f) => sidecarCmd('seek_side', { fraction: f })"
    @needle-drag-started="sidecarCmd('transport_pause')"
  />
  <ContextMenu
    v-if="contextState"
    :x="contextState.x"
    :y="contextState.y"
    :items="menuFor(contextState.item)"
    @close="contextState = null"
  />
  <PromptModal
    v-if="renameState"
    title="编辑物品"
    label="新名称："
    :initial="renameState.item.name"
    @confirm="(name) => submitRename(renameState!.item, name)"
    @cancel="renameState = null"
  />
  <ConfirmModal
    v-if="deleteState"
    title="删除物品"
    :message="`确定删除「${deleteState.item.name}」？曲目将级联删除，操作不可撤销。`"
    danger
    @confirm="submitDelete(deleteState!.item)"
    @cancel="deleteState = null"
  />
  <ImportDialog
    v-if="showImport"
    :item-types="itemTypes"
    @done="
      (msg) => {
        showImport = false
        showMessage(msg)
      }
    "
    @close="showImport = false"
  />
  <SettingsDialog
    v-if="showSettings"
    :user-config="userConfig"
    :levels="effectLevels"
    @changed="(cfg) => (userConfig = cfg)"
    @close="showSettings = false"
  />
</template>
