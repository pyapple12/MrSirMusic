<script setup lang="ts">
// 设置对话框（PL008.3）：拟真度三档 + 自动翻面（对齐 Qt SettingsDialog 语义）——set_config 实时生效
// config_changed 事件回显由父级同步（props 单向下行）；档位说明文案对齐 Qt 版 _LEVEL_HINTS
import { computed, ref } from "vue"
import { parseSidecarError, sidecarCmd } from "../lib/ipc"
import type { EffectLevel, UserConfigData } from "../lib/types"

const props = defineProps<{
  userConfig: UserConfigData
  levels: Record<string, EffectLevel>
}>()

const emit = defineEmits<{
  (e: "changed", config: UserConfigData): void
  (e: "close"): void
}>()

const realism = ref(props.userConfig.realism_level)
const autoFlip = ref(props.userConfig.auto_flip)
const errorText = ref("")
const busy = ref(false)

const levelKeys = computed(() => Object.keys(props.levels))

const LEVEL_HINTS: Record<string, string> = {
  concise: "简洁：关闭磨损与动画，纯矢量拟物，最省资源",
  refined: "精致：磨损贴图 + 转盘动画 + 黑胶底噪（推荐）",
  realistic: "真实：全量磨损与风化 + 拟真音效与贴图全开",
}

async function save() {
  errorText.value = ""
  busy.value = true
  try {
    const fresh = await sidecarCmd<UserConfigData>("set_config", {
      realism_level: realism.value,
      auto_flip: autoFlip.value,
    })
    emit("changed", fresh)
    emit("close")
  } catch (err) {
    errorText.value = `保存失败：${parseSidecarError(err).message}`
  } finally {
    busy.value = false
  }
}
</script>

<template>
  <Teleport to="body">
    <div class="modal-overlay" @click.self="emit('close')">
      <div class="modal-box settings-box">
        <h3>设置</h3>
        <label class="modal-label">拟真度档位</label>
        <select v-model="realism" class="modal-input">
          <option v-for="key in levelKeys" :key="key" :value="key">
            {{ key }}
          </option>
        </select>
        <p class="settings-hint">{{ LEVEL_HINTS[realism] ?? "" }}</p>
        <label class="import-radio">
          <input v-model="autoFlip" type="checkbox" />
          面内播放结束自动翻面（A↔B）
        </label>
        <div v-if="errorText" class="import-error">{{ errorText }}</div>
        <div class="modal-actions">
          <button class="btn-ghost" :disabled="busy" @click="emit('close')">
            取消
          </button>
          <button class="btn-primary" :disabled="busy" @click="save">
            保存
          </button>
        </div>
      </div>
    </div>
  </Teleport>
</template>
