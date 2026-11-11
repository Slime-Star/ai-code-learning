<template>
  <div ref="root" class="fragment-image" :class="{ 'ambient-paused': !visible }" role="img" :aria-label="alt">
    <div class="fragment-outline" aria-hidden="true"></div>
    <div class="fragment-artwork" aria-hidden="true">
      <img class="fragment-still" :src="images[settled]" alt="" decoding="async" draggable="false" />
      <canvas ref="canvas" class="fragment-canvas" :class="{ 'canvas-ready': ready }" aria-hidden="true"></canvas>
    </div>
    <span class="fragment-code code-open" aria-hidden="true">&lt;/&gt;</span>
    <span class="fragment-code code-build" aria-hidden="true"><i></i> {{ codeLabel }}</span>
    <span class="fragment-marker" aria-hidden="true">FIG. 0{{ index + 1 }} <b>／</b> CODE IN PIECES</span>
  </div>
</template>

<script setup>
import { ref, watch, onMounted, onBeforeUnmount } from 'vue'
import { createTriangleFlip } from '@/utils/triangleFlipRenderer'

const props = defineProps({
  images: { type: Array, required: true },
  index: { type: Number, default: 0 },
  alt: { type: String, default: '' },
  codeLabel: { type: String, default: 'learn, build, share' }
})
const root = ref(null), canvas = ref(null), visible = ref(true), ready = ref(false)
const settled = ref(props.index)
let renderer, observer, inView = true
function updateVisibility() { visible.value = !document.hidden && inView }
watch(() => props.index, index => {
  if (renderer) renderer.show(index)
  else settled.value = index
})
onMounted(() => {
  renderer = createTriangleFlip(canvas.value, props.images, {
    initialIndex: props.index,
    onReady: () => { ready.value = true },
    onChange: index => { settled.value = index },
    onError: () => { ready.value = false }
  })
  updateVisibility()
  document.addEventListener('visibilitychange', updateVisibility)
  if (typeof IntersectionObserver !== 'undefined') {
    observer = new IntersectionObserver(entries => {
      inView = entries[0]?.isIntersecting ?? true
      updateVisibility()
    })
    observer.observe(root.value)
  }
})
onBeforeUnmount(() => {
  renderer?.dispose()
  observer?.disconnect()
  document.removeEventListener('visibilitychange', updateVisibility)
})
</script>

<style scoped>
.fragment-image{position:relative;width:100%;height:100%;isolation:isolate}
.fragment-artwork{position:absolute;inset:0;border-radius:16px;overflow:hidden;background:#695386;animation:artwork-float 7s ease-in-out infinite alternate}
.fragment-still{position:absolute;inset:0;display:block;width:100%;height:100%;object-fit:cover;pointer-events:none;user-select:none}
.fragment-canvas{position:absolute;inset:0;width:100%;height:100%;display:block;opacity:0;pointer-events:none}
.canvas-ready{opacity:1}.fragment-still,.fragment-canvas{filter:saturate(.9) brightness(.98)}
.fragment-outline{position:absolute;inset:17px -15px -17px 15px;border:1px solid #f3dfff66;transform:rotate(-5deg);border-radius:3px;pointer-events:none}
.fragment-outline::after{content:'';position:absolute;right:-5px;top:-5px;width:9px;height:9px;background:#e7d4ff;box-shadow:0 0 20px #e8ccff88}
.fragment-code{position:absolute;z-index:4;pointer-events:none;animation:fragment-label-float 6s ease-in-out infinite alternate}
.code-open{left:-22px;top:-18px;width:63px;height:54px;display:grid;place-items:center;background:#f6edff;color:#8e67b5;box-shadow:0 12px 30px #35214f33;font:23px Consolas,monospace;transform:rotate(-10deg);border-radius:13px}
.code-build{right:-18px;bottom:24px;display:flex;align-items:center;gap:8px;padding:12px 15px;border:1px solid #f2ddff88;border-radius:10px;background:#7960aee6;box-shadow:0 12px 30px #35214f33;font:10px Consolas,monospace;color:#fff;animation-delay:-3s}
.code-build i{width:5px;height:5px;background:#c9f1e4;border-radius:50%;box-shadow:0 0 8px #d0f8e3}
.fragment-marker{position:absolute;right:4px;top:-27px;font:8px Consolas,monospace;letter-spacing:2px;color:#f2e1ff99;pointer-events:none}
.fragment-marker b{margin:0 6px;color:#e5d0ff55}
.ambient-paused .fragment-artwork,.ambient-paused .fragment-code{animation-play-state:paused}
@keyframes artwork-float{to{transform:translateY(-5px) rotate(.6deg)}}
@keyframes fragment-label-float{to{translate:0 -7px}}
@media(max-width:480px){.code-open{width:48px;height:43px;left:-12px;font-size:19px}.code-build{right:-10px;padding:10px;font-size:9px}.fragment-marker{font-size:7px;letter-spacing:1px}.fragment-outline{inset:12px -9px -12px 9px}}
</style>
