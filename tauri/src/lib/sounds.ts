// Web Audio 音效（PL009.6）：对齐 ui/sounds.py SoundKit 语义——底噪循环随播放态启停（vinyl 门控）、
// 落针/机械声一次性、档位响度 = ambience_intensity；音源 data/sounds/*.wav 经 asset protocol 拉取
// 容错：无声卡/解码失败静默降级禁用（容错登记制语义平移），一次性告警由调用方呈现

import { convertFileSrc } from "@tauri-apps/api/core"

let ctx: AudioContext | null = null
const buffers = new Map<string, AudioBuffer>()
let crackleSource: AudioBufferSourceNode | null = null
let crackleGain: GainNode | null = null
let mediaKind = "vinyl"
let active = false
let level = 0.4

// 音频资产根（App 由 bootstrap.app_root 注入一次）
let assetRoot = ""

function soundUrl(name: string): string {
  return convertFileSrc(`${assetRoot}/data/sounds/${name}.wav`)
}

async function ensureCtx(): Promise<AudioContext | null> {
  try {
    if (!ctx) ctx = new AudioContext()
    if (ctx.state === "suspended") await ctx.resume()
    return ctx
  } catch {
    return null // 无声卡/WebAudio 不可用——整体降级禁用（不抛出）
  }
}

async function loadBuffer(name: string): Promise<AudioBuffer | null> {
  const cached = buffers.get(name)
  if (cached) return cached
  const audio = await ensureCtx()
  if (!audio) return null
  try {
    const resp = await fetch(soundUrl(name))
    if (!resp.ok) throw new Error(`HTTP ${resp.status}`)
    const bytes = await resp.arrayBuffer()
    const buf = await audio.decodeAudioData(bytes)
    buffers.set(name, buf)
    return buf
  } catch {
    buffers.set(name, undefined as unknown as AudioBuffer) // 负缓存：失败不再重试
    return null
  }
}

async function startCrackle() {
  if (crackleSource || !active || mediaKind !== "vinyl") return
  const audio = await ensureCtx()
  const buf = await loadBuffer("vinyl_crackle")
  if (!audio || !buf || !buf.duration) return
  const src = audio.createBufferSource()
  src.buffer = buf
  src.loop = true
  const gain = audio.createGain()
  gain.gain.value = level
  src.connect(gain).connect(audio.destination)
  src.start()
  crackleSource = src
  crackleGain = gain
}

function stopCrackle() {
  if (crackleSource) {
    try {
      crackleSource.stop()
    } catch {
      // 已停止——静默
    }
    crackleSource.disconnect()
    crackleSource = null
    crackleGain = null
  }
}

async function playOneShot(name: string) {
  const audio = await ensureCtx()
  const buf = await loadBuffer(name)
  if (!audio || !buf || !buf.duration) return
  const src = audio.createBufferSource()
  src.buffer = buf
  const gain = audio.createGain()
  gain.gain.value = Math.max(level, 0.4) // 一次性音效下限响度（听感保底）
  src.connect(gain).connect(audio.destination)
  src.start()
}

export const soundKit = {
  // 资产根注入（App bootstrap 后调用一次）
  setAssetRoot(root: string) {
    assetRoot = root
  },

  // 载体类型切换（PL006 同名命令语义：vinyl/cassette/cd）
  setMediaKind(kind: string) {
    mediaKind = kind
    if (mediaKind !== "vinyl") stopCrackle()
  },

  // 播放态联动：playing + vinyl → 底噪循环启停（对齐 SoundKit.set_active）
  setActive(value: boolean) {
    active = value
    if (!active || mediaKind !== "vinyl") {
      stopCrackle()
    } else {
      void startCrackle()
    }
  },

  // 档位响度（effects.json ambience_intensity；对齐 SoundKit.set_level 含恢复语义）
  setLevel(intensity: number) {
    level = intensity
    if (crackleGain) crackleGain.gain.value = intensity
  },

  // 落针刮擦声（播放态迁移沿/翻面）
  playNeedleDrop() {
    void playOneShot("needle_drop")
  },

  // 磁带换曲机械声
  playTapeMech() {
    void playOneShot("tape_mech")
  },

  // 诊断：底噪循环是否在跑（验证用）
  crackleRunning(): boolean {
    return crackleSource !== null
  },
}
