<script setup lang="ts">
// 右键菜单（PL008.1）：fixed 定位于鼠标坐标，点击项发 action；点击外部/Esc 关闭
import { onBeforeUnmount, onMounted } from "vue"

export interface MenuItem {
  label: string
  danger?: boolean
  action: () => void
}

const props = defineProps<{
  x: number
  y: number
  items: MenuItem[]
}>()

const emit = defineEmits<{
  (e: "close"): void
}>()

function run(item: MenuItem) {
  emit("close")
  item.action()
}

function onDocClick() {
  emit("close")
}

function onKey(e: KeyboardEvent) {
  if (e.key === "Escape") emit("close")
}

onMounted(() => {
  document.addEventListener("click", onDocClick)
  document.addEventListener("keydown", onKey)
})

onBeforeUnmount(() => {
  document.removeEventListener("click", onDocClick)
  document.removeEventListener("keydown", onKey)
})
</script>

<template>
  <Teleport to="body">
    <div class="ctx-menu" :style="{ left: `${x}px`, top: `${y}px` }">
      <button
        v-for="item in items"
        :key="item.label"
        class="ctx-item"
        :class="{ danger: item.danger }"
        @click.stop="run(item)"
      >
        {{ item.label }}
      </button>
    </div>
  </Teleport>
</template>
