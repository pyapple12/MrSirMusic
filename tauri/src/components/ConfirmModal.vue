<script setup lang="ts">
// 确认模态（PL008.1：删除等危险操作对齐 Qt 确认语义）；Enter/Esc 支持
defineProps<{
  title: string
  message: string
  danger?: boolean
}>()

const emit = defineEmits<{
  (e: "confirm"): void
  (e: "cancel"): void
}>()
</script>

<template>
  <Teleport to="body">
    <div class="modal-overlay" @click.self="emit('cancel')">
      <div class="modal-box" @keydown.esc="emit('cancel')">
        <h3>{{ title }}</h3>
        <p class="modal-message">{{ message }}</p>
        <div class="modal-actions">
          <button class="btn-ghost" @click="emit('cancel')">取消</button>
          <button
            class="btn-primary"
            :class="{ 'btn-danger': danger }"
            @click="emit('confirm')"
          >
            确定
          </button>
        </div>
      </div>
    </div>
  </Teleport>
</template>
