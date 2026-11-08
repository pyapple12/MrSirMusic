// 主题桥（PL007.4）：get_bootstrap → ui.json colors → CSS custom properties（配置单源不变，B2.7 惯例）
// 变量命名 --mm-*（MrSirMusic 前缀）；font_family 全局注入

import type { Bootstrap } from "./types"

const COLOR_KEYS = [
  "primary",
  "secondary",
  "hover",
  "pressed",
  "border",
  "background",
  "text",
  "text_on_primary",
  "surface",
  "panel",
  "muted",
  "disabled",
] as const

export function applyTheme(boot: Bootstrap): void {
  const colors = boot.ui?.colors ?? {}
  const root = document.documentElement
  for (const key of COLOR_KEYS) {
    const value = colors[key]
    if (typeof value === "string") {
      root.style.setProperty(`--mm-${key}`, value)
    }
  }
  const font = boot.ui?.font_family
  if (typeof font === "string") {
    root.style.setProperty("--mm-font", `"${font}"`)
  }
}
