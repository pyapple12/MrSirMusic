// 侧车 IPC 客户端（PL007.4）：命令转发（Rust sidecar_cmd id 关联）+ 协议事件订阅（sidecar://event）
// 错误串（Rust 回传的 error JSON 字符串）由调用方解析提示——本层只透传

import { invoke } from "@tauri-apps/api/core"
import { listen, type UnlistenFn } from "@tauri-apps/api/event"
import type { WireEvent } from "./types"

// 事件 wire 名单源（与 Rust sidecar.rs EVENT_WIRE/EVENT_DEAD 对齐）
const EVENT_WIRE = "sidecar://event"
const EVENT_DEAD = "sidecar://dead"

// 命令转发：异常路径抛出 Rust 侧错误串（前端 catch 呈现）
export function sidecarCmd<T = unknown>(
  cmd: string,
  params: Record<string, unknown> = {},
): Promise<T> {
  return invoke<T>("sidecar_cmd", { cmd, params })
}

// 订阅侧车协议事件（ready/progress/playback_state/track_changed/side_flipped/error/...）
export function onSidecarEvent(
  handler: (event: WireEvent) => void,
): Promise<UnlistenFn> {
  return listen<WireEvent>(EVENT_WIRE, (evt) => handler(evt.payload))
}

// 订阅侧车死亡事件（重启×3 耗尽——前端错误横幅）
export function onSidecarDead(handler: (payload: unknown) => void): Promise<UnlistenFn> {
  return listen(EVENT_DEAD, (evt) => handler(evt.payload))
}

// 错误解析：Rust 侧 reject 的错误串 = 侧车 error 信封 JSON（{category,message}）——解析失败按原文兜底
export function parseSidecarError(err: unknown): SidecarErrorInfo {
  const fallback: SidecarErrorInfo = { category: "unknown", message: String(err) }
  if (typeof err !== "string") return fallback
  try {
    const parsed = JSON.parse(err) as Partial<SidecarErrorInfo>
    if (parsed && typeof parsed.category === "string") {
      return { category: parsed.category, message: parsed.message ?? err }
    }
  } catch {
    // 非 JSON 错误串（Rust 壳层错误如超时）——原文返回
  }
  return fallback
}

export interface SidecarErrorInfo {
  category: string
  message: string
}
