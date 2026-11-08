<script setup lang="ts">
// 磁带仓形态（PL009.4）：壳体贴图 + 观察窗双卷轴（draw_reel 同构 SVG：带卷/缠绕纹/花键 3 齿）
// + 双飞轮 + 走带路径；半径按带卷物理因子胀缩（deckMath.reelFactor 同源）
import { computed } from "vue"
import {
  REEL_RADIUS_MAX,
  REEL_RADIUS_MIN,
  reelFactor,
} from "../../lib/deckMath"

const props = defineProps<{
  angle: number
  sideProgress: number
  reelL: number
  reelR: number
  playing: boolean
  textures: boolean
  textureUrl: string | null
}>()

const VIEW = 240 // viewBox 常量（正方形坐标系，与容器 1:1）

// 观察窗（deck_widget._paint_cassette_deck 同比例：x16% y18% w68% h40%）
const win = {
  x: VIEW * 0.16,
  y: VIEW * 0.18,
  w: VIEW * 0.68,
  h: VIEW * 0.4,
}

// 卷轴参数（deck_widget 磁带仓同式：r_max=窗高42%、r_min=r_max×42%、hub=r_min×62%）
const rMax = win.h * 0.42
const rMin = rMax * 0.42
const hub = rMin * 0.62

interface Reel {
  cx: number
  cy: number
  radius: number
  angle: number
}

const reels = computed<Reel[]>(() => {
  const centers = [
    { x: win.x + win.w * 0.26, y: win.y + win.h / 2 },
    { x: win.x + win.w * 0.74, y: win.y + win.h / 2 },
  ]
  const fills = [1 - props.sideProgress, props.sideProgress]
  const angles = [props.reelL, props.reelR]
  return centers.map((c, i) => {
    const t =
      (reelFactor(fills[i]) - REEL_RADIUS_MIN) / (REEL_RADIUS_MAX - REEL_RADIUS_MIN)
    return { cx: c.x, cy: c.y, radius: rMin + (rMax - rMin) * t, angle: angles[i] }
  })
})

function toothPoints(reel: Reel, index: number): string {
  // 3 齿（120° 分布随角度旋转）——deck_widget/parts.draw_reel 同构（矩形齿近似为多边形点串）
  const base = reel.angle + index * 120
  const rad = (base * Math.PI) / 180
  const x1 = reel.cx + Math.sin(rad) * hub
  const y1 = reel.cy - Math.cos(rad) * hub
  const x2 = reel.cx + Math.sin(rad) * (hub + 1.5)
  const y2 = reel.cy - Math.cos(rad) * (hub + 1.5)
  return `${x1},${y1 - 2} ${x2},${y2} ${x1 + 3},${y1 + 2}`
}
</script>

<template>
  <div class="cassette-stage">
    <svg :viewBox="`0 0 ${VIEW} ${VIEW}`" class="cassette-svg">
      <defs>
        <clipPath id="cassette-clip">
          <rect x="8" y="8" :width="VIEW - 16" :height="VIEW - 16" rx="10" />
        </clipPath>
      </defs>
      <!-- 壳体：贴图或深色渐变 -->
      <g clip-path="url(#cassette-clip)">
        <image
          v-if="textures && textureUrl"
          :href="textureUrl"
          x="8"
          y="8"
          :width="VIEW - 16"
          :height="VIEW - 16"
          preserveAspectRatio="xMidYMid slice"
        />
        <rect v-else x="8" y="8" :width="VIEW - 16" :height="VIEW - 16" fill="#262019" />
      </g>
      <rect
        x="8"
        y="8"
        :width="VIEW - 16"
        :height="VIEW - 16"
        rx="10"
        fill="none"
        stroke="#55556a"
      />
      <!-- 四角螺丝 -->
      <circle
        v-for="(screw, i) in [
          { x: 20, y: 20 },
          { x: VIEW - 20, y: 20 },
          { x: 20, y: VIEW - 20 },
          { x: VIEW - 20, y: VIEW - 20 },
        ]"
        :key="i"
        :cx="screw.x"
        :cy="screw.y"
        r="2.5"
        fill="#777788"
        stroke="#44445a"
      />
      <!-- 观察窗 -->
      <rect
        :x="win.x"
        :y="win.y"
        :width="win.w"
        :height="win.h"
        rx="4"
        fill="#14141a"
        stroke="#55556a"
      />
      <!-- 双卷轴（draw_reel 同构：带卷体+缠绕纹+hub+3 齿随角旋转） -->
      <g v-for="(reel, i) in reels" :key="i">
        <circle :cx="reel.cx" :cy="reel.cy" :r="reel.radius" fill="#2e2620" stroke="#5a4a3a" />
        <circle
          :cx="reel.cx"
          :cy="reel.cy"
          :r="reel.radius * 0.72"
          fill="none"
          stroke="rgba(90,74,58,0.43)"
        />
        <circle
          :cx="reel.cx"
          :cy="reel.cy"
          :r="reel.radius * 0.5"
          fill="none"
          stroke="rgba(90,74,58,0.43)"
        />
        <circle :cx="reel.cx" :cy="reel.cy" :r="hub" fill="#d8d8d8" stroke="#777" />
        <g :transform="`rotate(${reel.angle} ${reel.cx} ${reel.cy})`">
          <rect
            v-for="t in 3"
            :key="t"
            :x="reel.cx - 1.5"
            :y="reel.cy - hub"
            width="3"
            :height="hub * 0.85"
            fill="#8a8a8a"
            :transform="`rotate(${(t - 1) * 120} ${reel.cx} ${reel.cy})`"
          />
        </g>
      </g>
      <!-- 走带路径（窗内底部横线） -->
      <line
        :x1="win.x + win.w * 0.12"
        :y1="win.y + win.h - 3"
        :x2="win.x + win.w * 0.88"
        :y2="win.y + win.h - 3"
        stroke="#4a3f36"
      />
      <!-- 双飞轮（窗下两侧，辐条随角旋转） -->
      <g
        v-for="(fx, i) in [VIEW * 0.22, VIEW * 0.78]"
        :key="`fly${i}`"
        :transform="`translate(${fx} ${VIEW * 0.72}) rotate(${angle * 1.8})`"
      >
        <circle r="13" fill="#8a8a9a" stroke="#55556a" />
        <line
          v-for="s in 3"
          :key="s"
          x1="0"
          y1="0"
          x2="0"
          :y2="-13 * 0.85"
          stroke="#3a3a46"
          :transform="`rotate(${(s - 1) * 120})`"
        />
      </g>
      <!-- 铭牌条 -->
      <rect
        :x="VIEW * 0.3"
        :y="VIEW * 0.06"
        :width="VIEW * 0.4"
        :height="VIEW * 0.05"
        fill="#2a2a34"
        stroke="#44445a"
      />
    </svg>
  </div>
</template>

<style scoped>
.cassette-stage {
  position: absolute;
  inset: 0;
}

.cassette-svg {
  width: 100%;
  height: 100%;
}
</style>
