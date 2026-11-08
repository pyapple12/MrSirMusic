<script setup lang="ts">
// 单行输入模态（PL008.1：编辑改名对齐 Qt QInputDialog 语义）；Enter 确认 / Esc 取消
import { onMounted, ref } from "vue"

const props = defineProps<{
  title: string
  label: string
  initial: string
}>()

const emit = defineEmits<{
  (e: "confirm", value: string): void
  (e: "cancel"): void
}>()

const value = ref(props.initial)
const input = ref<HTMLInputElement | null>(null)

onMounted(() => {
  input.value?.focus()
  input.value?.select()
})

function submit() {
  const trimmed = value.value.trim()
  if (trimmed) {
    emit("confirm", trimmed)
  }
}
</script>

<template>
  <Teleport to="body">
    <div class="modal-overlay" @click.self="emit('cancel')">
      <div class="modal-box" @keydown.esc="emit('cancel')">
        <h3>{{ title }}</h3>
        <label class="modal-label">{{ label }}</label>
        <input
          ref="input"
          v-model="value"
          class="modal-input"
          type="text"
          @keydown.enter="submit"
        />
        <div class="modal-actions">
          <button class="btn-ghost" @click="emit('cancel')">取消</button>
          <button class="btn-primary" @click="submit">确定</button>
        </div>
      </div>
    </div>
  </Teleport>
</template>
