<script setup lang="ts">
// 物品库视图（PL008.1）：两行列表（名称主行/形态·Tag·时长次行）+ 详情面板 + 右键菜单信号
// 对齐 Qt 版 LibraryView 信息架构（parity ⑦ 详情字段）；选中行高亮
import { computed, ref } from "vue"
import { convertFileSrc } from "@tauri-apps/api/core"
import type { ItemDict } from "../lib/types"

const props = defineProps<{
  items: ItemDict[]
  loading: boolean
}>()

const emit = defineEmits<{
  (e: "play", item: ItemDict): void
  (e: "context", payload: { item: ItemDict; x: number; y: number }): void
}>()

const selectedId = ref<string | null>(null)
const selected = computed(
  () => props.items.find((item) => item.id === selectedId.value) ?? null,
)

function select(item: ItemDict) {
  selectedId.value = item.id
}

function rowText(item: ItemDict): string {
  // 次行：形态·Tag·时长（对齐 Qt 版 set_items 两行文本，parity ①）
  return `${item.type.name}·${item.tag || "未分类"}`
}

function onContext(item: ItemDict, event: MouseEvent) {
  selectedId.value = item.id
  emit("context", { item, x: event.clientX, y: event.clientY })
}
</script>

<template>
  <div v-if="loading" class="empty-hint">正在连接侧车后端…</div>
  <div v-else-if="items.length === 0" class="empty-hint">物品库为空——先导入物品</div>
  <div v-else class="library-layout">
    <ul class="lib-list">
      <li
        v-for="item in items"
        :key="item.id"
        class="lib-row"
        :class="{ selected: item.id === selectedId }"
        @click="select(item)"
        @contextmenu.prevent="onContext(item, $event)"
      >
        <img
          v-if="item.cover_path"
          class="lib-thumb"
          :src="convertFileSrc(item.cover_path)"
          alt=""
        />
        <div class="lib-row-text">
          <div class="lib-row-name">{{ item.name }}</div>
          <div class="lib-row-sub">{{ rowText(item) }}</div>
        </div>
      </li>
    </ul>
    <div v-if="selected" class="lib-detail">
      <div class="detail-name">{{ selected.name }}</div>
      <div class="detail-line">类型：{{ selected.type.name }}</div>
      <div class="detail-line">Tag：{{ selected.tag || "（无）" }}</div>
      <div class="detail-line">
        总时长：{{ Math.round(selected.total_seconds) }} 秒
      </div>
      <div
        v-for="side in selected.sides"
        :key="side.label"
        class="detail-line"
      >
        {{ side.label }} 面：{{ side.tracks.length }} 首
      </div>
    </div>
    <div v-else class="lib-detail">未选中物品</div>
  </div>
</template>
