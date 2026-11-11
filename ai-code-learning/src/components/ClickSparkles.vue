<template>
  <Teleport to="body">
    <div class="click-effects" aria-hidden="true">
      <span v-for="burst in bursts" :key="burst.id" class="click-burst" :style="{ left: `${burst.x}px`, top: `${burst.y}px` }">
        <span class="button-wave" :style="burst.waveBounds"><i :style="burst.wave"></i></span>
        <i class="click-ring"></i>
        <i v-for="(particle, index) in burst.particles" :key="index" class="click-particle" :style="particle.style">{{ particle.text }}</i>
      </span>
    </div>
  </Teleport>
</template>

<script setup>
import { ref, onMounted, onBeforeUnmount } from 'vue'
const bursts = ref([])
const timers = new Set()
let sequence = 0
function sparkle(event) {
  if (!(event.target instanceof Element)) return
  const target = event.target.closest('button, a, summary, [role="button"], [role="tab"], .el-menu-item, .category-tag')
  if (!target || target.matches(':disabled, [aria-disabled="true"], .is-disabled')) return
  const bounds = target.getBoundingClientRect()
  const id = ++sequence
  const x = event.detail ? event.clientX : bounds.left + bounds.width / 2
  const y = event.detail ? event.clientY : bounds.top + bounds.height / 2
  const symbols = ['+', '', '·', '', '✦', '', '·']
  const particles = symbols.map((text, i) => {
    const angle = i / symbols.length * Math.PI * 2
    const distance = 25 + (i % 3) * 10
    return { text, style: { '--dx': `${Math.cos(angle) * distance}px`, '--dy': `${Math.sin(angle) * distance}px`, '--turn': `${i % 2 ? 55 : -55}deg`, color: ['#b49af0', '#8bbef4', '#d6a8dc'][i % 3] } }
  })
  const diameter=Math.min(650,Math.hypot(bounds.width,bounds.height)*2)
  const waveBounds={left:`${bounds.left-x}px`,top:`${bounds.top-y}px`,width:`${bounds.width}px`,height:`${bounds.height}px`,borderRadius:window.getComputedStyle(target).borderRadius||'8px'}
  const wave={left:`${x-bounds.left-diameter/2}px`,top:`${y-bounds.top-diameter/2}px`,width:`${diameter}px`,height:`${diameter}px`}
  bursts.value = [...bursts.value.slice(-4), { id, x, y, particles, waveBounds, wave }]
  const timer = setTimeout(() => { bursts.value = bursts.value.filter(item => item.id !== id); timers.delete(timer) }, 650)
  timers.add(timer)
}
onMounted(() => window.addEventListener('click', sparkle, { capture: true, passive: true }))
onBeforeUnmount(() => { window.removeEventListener('click', sparkle, true); timers.forEach(clearTimeout); timers.clear() })
</script>

<style scoped>
.click-effects { position: fixed; inset: 0; pointer-events: none; overflow: hidden; z-index: 5000; }
.click-burst { position: absolute; }
.button-wave { position: absolute; overflow: hidden; pointer-events: none; }
.button-wave i { display: block; position: absolute; border-radius: 50%; background: radial-gradient(circle,#bca0ee40,#c8b4ee20 60%,transparent 72%); animation: button-wave 600ms cubic-bezier(.12,.7,.3,1) both; }
@keyframes button-wave { from { transform: scale(0); opacity: .8; } to { transform: scale(1); opacity: 0; } }
.click-ring { position: absolute; width: 12px; height: 12px; margin: -6px; border: 1px solid #b3a0ea; border-radius: 50%; animation: click-ring 550ms ease-out both; }
.click-particle { position: absolute; display: grid; place-items: center; width: 12px; height: 12px; left: -6px; top: -6px; font: 14px/1 Consolas, monospace; font-style: normal; animation: click-scatter 600ms cubic-bezier(.12,.7,.3,1) both; }
.click-particle:empty { width: 4px; height: 4px; left: -2px; top: -2px; border-radius: 50%; background: currentColor; }
@keyframes click-ring { from { transform: scale(.5); opacity: .7; } to { transform: scale(4); opacity: 0; } }
@keyframes click-scatter { 0% { transform: translate(0,0) scale(.4); opacity: 0; } 15% { opacity: .9; } 100% { transform: translate(var(--dx),var(--dy)) rotate(var(--turn)) scale(.6); opacity: 0; } }
</style>
