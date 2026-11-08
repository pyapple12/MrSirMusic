// 侧车协议类型（PL007）：与 Python sidecar/protocol.py 信封同契约——字段表单源约定见 z.plan PL006
// 前端只消费：ItemDict（列表渲染）/ Bootstrap（启动快照）/ WireEvent（事件信封）

export interface TrackDict {
  path: string
  title: string
  artist: string
  album: string
  duration_seconds: number
  format: string
  is_missing: boolean
}

export interface SideDict {
  label: string
  tracks: TrackDict[]
}

export interface ItemDict {
  id: string
  name: string
  type: { key: string; name: string; shape: string }
  cover_source: string
  cover_path: string
  tag: string
  play_count: number
  total_seconds: number
  sides: SideDict[]
}

export interface UserConfig {
  realism_level: string
  auto_flip: boolean
}

export interface Bootstrap {
  base: Record<string, unknown>
  ui: { colors?: Record<string, string>; font_family?: string }
  effects: Record<string, unknown>
  item_types: Record<string, unknown>
  user_config: UserConfig
  items: ItemDict[]
}

export interface WireEvent {
  event: string
  data: unknown
}

export interface TrackChangedData {
  track: TrackDict | null
  side: string | null
  side_offset_seconds: number | null
  side_total_seconds: number | null
}

export interface ProgressData {
  position_ms: number
  duration_ms: number
}

export interface ItemTypeConfig {
  name: string
  minutes_per_side: number
  sides: string[]
  shape: string
  spin_ms_per_rev?: number
}

export interface SidecarCommandError {
  category: string
  message: string
}

export interface UserConfigData {
  realism_level: string
  auto_flip: boolean
}

export interface EffectLevel {
  animations: boolean
  wear: boolean
  weathering: boolean
  texture: boolean
  ambience_intensity: number
  wear_intensity?: number
  weathering_intensity?: number
}
