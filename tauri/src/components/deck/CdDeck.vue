<script setup lang="ts">
// CD 碟舱形态（PL009.4）：贴图碟面（彩虹反射与中心孔已烘焙）随角旋转 + 封面环带 + 3 夹持爪
// refined 档跳过手绘槽纹（防与烘焙纹理打架，PL005 定案语义平移）
const props = defineProps<{
  angle: number
  sideProgress: number
  textures: boolean
  realismLevel: string
  textureUrl: string | null
  coverUrl: string | null
}>()

const VIEW = 240
const R = VIEW / 2

// 封面环带（deck_widget._paint_cd 同比例：r 22%..55%）
const ringClipId = `cd-ring-${Math.random().toString(36).slice(2, 8)}`
</script>

<template>
  <div class="cd-stage">
    <svg :viewBox="`0 0 ${VIEW} ${VIEW}`" class="cd-svg">
      <defs>
        <clipPath :id="ringClipId">
          <path
            :d="`M ${R} ${R - R * 0.55} A ${R * 0.55} ${R * 0.55} 0 1 1 ${R - 0.01} ${R - R * 0.55} Z M ${R} ${R - R * 0.22} A ${R * 0.22} ${R * 0.22} 0 1 0 ${R + 0.01} ${R - R * 0.22} Z`"
            clip-rule="evenodd"
          />
        </clipPath>
      </defs>
      <g :transform="`rotate(${angle} ${R} ${R})`">
        <!-- 碟面：贴图（含彩虹反射+孔镂空）或银灰渐变回退 -->
        <image
          v-if="textures && textureUrl"
          :href="textureUrl"
          :x="0"
          :y="0"
          :width="VIEW"
          :height="VIEW"
          preserveAspectRatio="xMidYMid slice"
        />
        <g v-else>
          <circle :cx="R" :cy="R" :r="R * 0.96" fill="#c8ccd4" />
          <circle :cx="R" :cy="R" :r="R * 0.08" fill="#232323" />
        </g>
        <!-- 封面环带 -->
        <g :clip-path="`url(#${ringClipId})`">
          <image
            v-if="coverUrl"
            :href="coverUrl"
            :x="R - R * 0.55"
            :y="R - R * 0.55"
            :width="R * 1.1"
            :height="R * 1.1"
            preserveAspectRatio="xMidYMid slice"
          />
          <circle v-else :cx="R" :cy="R" :r="R * 0.55" fill="#8a9098" />
        </g>
        <!-- 淡槽纹两圈（realistic 全量叠加，refined 跳过） -->
        <circle
          v-if="!(textures && realismLevel === 'refined')"
          :cx="R"
          :cy="R"
          :r="R * 0.66"
          fill="none"
          stroke="rgba(90,95,102,0.47)"
        />
        <circle
          v-if="!(textures && realismLevel === 'refined')"
          :cx="R"
          :cy="R"
          :r="R * 0.78"
          fill="none"
          stroke="rgba(90,95,102,0.47)"
        />
        <!-- 3 夹持爪（孔缘 120° 分布）+ 中轴环 -->
        <g :transform="`translate(${R} ${R})`">
          <rect
            v-for="i in 3"
            :key="i"
            :x="-R * 0.08 * 0.5"
            :y="-R * 0.08 * 1.9"
            :width="R * 0.08"
            :height="R * 0.08 * 1.5"
            fill="#6a6f76"
            :transform="`rotate(${(i - 1) * 120})`"
          />
          <circle :r="R * 0.08 * 0.8" fill="#3a3f46" />
        </g>
      </g>
    </svg>
  </div>
</template>

<style scoped>
.cd-stage {
  position: absolute;
  inset: 0;
}

.cd-svg {
  width: 100%;
  height: 100%;
}
</style>
