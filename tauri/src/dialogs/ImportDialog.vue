<script setup lang="ts">
// 导入对话框（PL008.2）：四分组对齐 Qt 版 PL003.3 语义——①音频文件 ②载体类型 ③命名与归类 ④封面来源
// 文件多选走 Tauri 原生 dialog 插件（parity ④）；generate 提交 + GenerateError 分类提示（不炸）
import { computed, ref } from "vue"
import { open } from "@tauri-apps/plugin-dialog"
import { parseSidecarError, sidecarCmd } from "../lib/ipc"
import type { ItemTypeConfig } from "../lib/types"

const props = defineProps<{
  itemTypes: Record<string, ItemTypeConfig>
}>()

const emit = defineEmits<{
  (e: "done", message: string): void
  (e: "close"): void
}>()

const AUDIO_FILTERS = [
  { name: "音频文件", extensions: ["wav", "mp3", "flac", "m4a"] },
]
const IMAGE_FILTERS = [
  { name: "图片文件", extensions: ["png", "jpg", "jpeg", "webp"] },
]

const files = ref<string[]>([])
const typeKey = ref<string>("")
const name = ref("")
const tag = ref("")
const coverSource = ref<"placeholder" | "local">("placeholder")
const coverFile = ref("")
const busy = ref(false)
const errorText = ref("")

const typeKeys = computed(() => Object.keys(props.itemTypes))
if (typeKeys.value.length > 0) {
  typeKey.value = typeKeys.value[0]
}

async function pickAudio() {
  const picked = await open({ multiple: true, filters: AUDIO_FILTERS })
  if (Array.isArray(picked) && picked.length > 0) {
    files.value = picked
  }
}

async function pickCover() {
  const picked = await open({ multiple: false, filters: IMAGE_FILTERS })
  if (typeof picked === "string") {
    coverFile.value = picked
  }
}

async function submit() {
  // 前端轻校验（空集业务侧也拦，双保险）；generate → GenerateError 分类透传
  errorText.value = ""
  if (files.value.length === 0) {
    errorText.value = "请先选择音频文件"
    return
  }
  if (!name.value.trim()) {
    errorText.value = "请填写物品名称"
    return
  }
  busy.value = true
  try {
    await sidecarCmd("generate", {
      files: files.value,
      type_key: typeKey.value,
      name: name.value.trim(),
      tag: tag.value.trim(),
      cover_source: coverSource.value,
      cover_file: coverSource.value === "local" ? coverFile.value : null,
    })
    emit("done", `生成成功：${name.value.trim()}`)
  } catch (err) {
    const info = parseSidecarError(err)
    if (info.category === "generate") {
      errorText.value = info.message // 选歌校验/容量类业务提示（中文，与 Qt 版同源）
    } else {
      errorText.value = `生成失败（${info.category}）：${info.message}`
    }
  } finally {
    busy.value = false
  }
}
</script>

<template>
  <Teleport to="body">
    <div class="modal-overlay" @click.self="emit('close')">
      <div class="modal-box import-box">
        <h3>导入/生成物品</h3>
        <fieldset class="import-group">
          <legend>① 音频文件</legend>
          <button class="btn-ghost" :disabled="busy" @click="pickAudio">
            选择音频文件…
          </button>
          <span class="import-hint">已选 {{ files.length }} 个</span>
        </fieldset>
        <fieldset class="import-group">
          <legend>② 载体类型</legend>
          <select v-model="typeKey" class="modal-input">
            <option v-for="key in typeKeys" :key="key" :value="key">
              {{ itemTypes[key]?.name ?? key }}
            </option>
          </select>
        </fieldset>
        <fieldset class="import-group">
          <legend>③ 命名与归类</legend>
          <input v-model="name" class="modal-input" type="text" placeholder="物品名称" />
          <input
            v-model="tag"
            class="modal-input"
            type="text"
            placeholder="Tag（置物架分组依据，可空）"
          />
        </fieldset>
        <fieldset class="import-group">
          <legend>④ 封面来源</legend>
          <label class="import-radio">
            <input v-model="coverSource" type="radio" value="placeholder" />
            占位图
          </label>
          <label class="import-radio">
            <input v-model="coverSource" type="radio" value="local" />
            本地文件
          </label>
          <button
            v-if="coverSource === 'local'"
            class="btn-ghost"
            :disabled="busy"
            @click="pickCover"
          >
            选择封面…
          </button>
          <span v-if="coverSource === 'local' && coverFile" class="import-hint">
            {{ coverFile.split(/[\\/]/).pop() }}
          </span>
        </fieldset>
        <div v-if="errorText" class="import-error">{{ errorText }}</div>
        <div class="modal-actions">
          <button class="btn-ghost" :disabled="busy" @click="emit('close')">
            取消
          </button>
          <button class="btn-primary" :disabled="busy" @click="submit">
            {{ busy ? "生成中…" : "生成" }}
          </button>
        </div>
      </div>
    </div>
  </Teleport>
</template>
