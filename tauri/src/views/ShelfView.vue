<script setup lang="ts">
// 置物架视图（PL007.5）：按 Tag 分组卡片流（对齐 Qt 版 ShelfView 语义；无 Tag 归"未分类"）
// 卡片 = 封面（convertFileSrc 直读本地）+ 名称 + 形态·曲数两行——128×128 对齐 card_size
import { computed } from "vue"
import { convertFileSrc } from "@tauri-apps/api/core"
import type { ItemDict } from "../lib/types"

const props = defineProps<{
  items: ItemDict[]
  loading: boolean
}>()

const emit = defineEmits<{
  (e: "play", item: ItemDict): void
}>()

const groups = computed(() => {
  // 按 tag 分组（key 排序对齐 Qt 版 sorted(groups.items())；空 Tag 归未分类）
  const map = new Map<string, ItemDict[]>()
  for (const item of props.items) {
    const key = item.tag || "未分类"
    const bucket = map.get(key)
    if (bucket) {
      bucket.push(item)
    } else {
      map.set(key, [item])
    }
  }
  return [...map.entries()].sort((a, b) => a[0].localeCompare(b[0], "zh-CN"))
})

function trackCount(item: ItemDict): number {
  return item.sides.reduce((sum, side) => sum + side.tracks.length, 0)
}

function coverUrl(item: ItemDict): string | null {
  if (item.cover_path) {
    return convertFileSrc(item.cover_path)
  }
  return null
}
</script>

<template>
  <div v-if="loading" class="empty-hint">正在连接侧车后端…</div>
  <div v-else-if="items.length === 0" class="empty-hint">
    置物架空荡荡——先用 Qt 版（python main.py）导入一件物品吧
  </div>
  <div v-else>
    <section v-for="[tag, group] in groups" :key="tag" class="shelf-group">
      <h3>{{ tag }}</h3>
      <div class="shelf-cards">
        <button
          v-for="item in group"
          :key="item.id"
          class="card"
          @click="emit('play', item)"
        >
          <img v-if="coverUrl(item)" :src="coverUrl(item)!" alt="封面" />
          <div class="card-name">{{ item.name }}</div>
          <div class="card-sub">{{ item.type.name }}·{{ trackCount(item) }}曲</div>
        </button>
      </div>
    </section>
  </div>
</template>
