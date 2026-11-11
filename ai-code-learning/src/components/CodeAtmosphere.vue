<template>
  <div :key="page" ref="field" class="code-atmosphere" :class="`glyph-${placement}`" aria-hidden="true">
    <div class="atmosphere-depth">
    <div class="ambient-orb orb-one"></div><div class="ambient-orb orb-two"></div>
    <svg class="ambient-circuit" viewBox="0 0 250 260" fill="none" focusable="false">
      <path d="M15 20h55l30 30v55l35 35h90M20 185h60l35-35v-30m40 140v-55l35-35h55" />
      <path class="circuit-signal" d="M15 20h55l30 30v55l35 35h90" />
      <g><circle cx="15" cy="20" r="4" /><circle cx="225" cy="140" r="5" /><circle cx="20" cy="185" r="4" /><circle cx="245" cy="170" r="4" /></g>
    </svg>
    <span class="floating-code code-a">{{ pack.symbol }}</span><span class="floating-code code-b">{{ pack.kind === 'topic' ? pack.scene : pack.kind === 'mail' ? 'send()' : 'run()' }}</span>
    <span class="floating-code code-c">{{ pack.phrase }}</span><span class="floating-code code-d">{{ pack.example.split('\n')[0] }}</span>
    <span v-for="n in 8" :key="n" class="ambient-dot" :style="{ '--i': n }"></span>
    <div class="ambient-grid"></div>
    <div class="ambient-sweep"></div>
    </div>
  </div>
</template>

<script setup>
import {computed,ref,onMounted,onBeforeUnmount} from 'vue'
import {getBackdropTheme} from '@/config/backdropThemes'
import {usePersistentMotion} from '@/composables/usePersistentMotion'
const props=defineProps({page:{type:String,default:'Home'}})
const pack=computed(()=>getBackdropTheme(props.page))
const placements={Home:'top-left',LearningCenter:'right-middle',Library:'top-right',Forum:'left-middle',Competition:'right-lower',Leaderboard:'left-lower',PointsMall:'top-right',DailyCheckIn:'left-middle',Class:'right-middle',Messages:'left-lower',Profile:'right-lower',WrongQuestions:'top-right',Login:'right-middle',Register:'left-middle'}
const placement=computed(()=>placements[props.page] || ['top-right','left-middle','right-lower','left-lower','right-middle'][Array.from(props.page).reduce((sum,char)=>sum+char.charCodeAt(0),0)%5])
const field=ref(null)
usePersistentMotion(field,()=>`atmosphere:${props.page}`)
let frame=0,x=0,y=0,depth=0
function paint(){
  frame=0
  field.value?.style.setProperty('--scene-x',`${x}px`)
  field.value?.style.setProperty('--scene-y',`${y}px`)
  field.value?.style.setProperty('--scene-depth',`${depth}px`)
}
function schedule(){if(!frame)frame=requestAnimationFrame(paint)}
function scroll(){depth=-Math.min(65,window.scrollY*.025);schedule()}
function pointer(event){if(event.pointerType!=='mouse')return;x=(event.clientX/Math.max(1,window.innerWidth)-.5)*16;y=(event.clientY/Math.max(1,window.innerHeight)-.5)*12;schedule()}
function reset(){x=0;y=0;schedule()}
onMounted(()=>{scroll();window.addEventListener('scroll',scroll,{passive:true});window.addEventListener('pointermove',pointer,{passive:true});window.addEventListener('blur',reset)})
onBeforeUnmount(()=>{window.removeEventListener('scroll',scroll);window.removeEventListener('pointermove',pointer);window.removeEventListener('blur',reset);cancelAnimationFrame(frame)})
</script>

<style scoped>
.code-atmosphere { position: absolute; inset: 0; overflow: hidden; pointer-events: none; user-select: none; z-index: 2; color: #af92ec; }
.atmosphere-depth { position: absolute; inset: 0; transform: translate3d(var(--scene-x,0px),calc(var(--scene-y,0px) + var(--scene-depth,0px)),0); transition: transform 800ms cubic-bezier(.2,.75,.25,1); }
.ambient-sweep { position: absolute; right: -30px; top: 12%; width: 100px; height: 240px; background: linear-gradient(160deg,transparent,#cdb4f520,transparent); filter: blur(16px); animation: edge-sweep 11s ease-in-out infinite alternate; }
@keyframes edge-sweep { from { transform: translateY(-80px) rotate(-10deg); opacity: .3; } to { transform: translateY(180px) rotate(12deg); opacity: .8; } }
.ambient-orb { position: absolute; width: 200px; height: 200px; border: 1px solid #c8b7fa45; border-radius: 50%; box-shadow: 0 0 0 30px #c8b7fa0c, 0 0 0 60px #c8b7fa08; animation: ambient-drift 9s ease-in-out infinite alternate; }
.orb-one { top: 270px; right: -85px; }.orb-two { bottom: 100px; left: -100px; animation-delay: .3s; }
.ambient-circuit { position: absolute; right: -95px; top: 45%; width: 250px; opacity: .28; }
.ambient-circuit path, .ambient-circuit circle { stroke: currentColor; stroke-width: 1.3; }
.circuit-signal { stroke-dasharray: 18 220; animation: circuit-flow 9s linear infinite; }
.floating-code { position: absolute; font: 600 26px Consolas, monospace; opacity: .23; animation: ambient-drift 8s ease-in-out infinite alternate; }
.code-a { left: 14px; top: 12px; font-size: 50px; }.code-b { right: 16px; bottom: 14px; font-size: 46px; animation-delay: .2s; }
.glyph-top-right .code-a { left: auto; right: 24px; top: 100px; transform: rotate(9deg); }
.glyph-left-middle .code-a { left: 12px; top: 32%; transform: rotate(-12deg); }
.glyph-right-middle .code-a { left: auto; right: 18px; top: 43%; transform: rotate(8deg); }
.glyph-left-lower .code-a { left: 20px; top: auto; bottom: 25%; transform: rotate(-7deg); }
.glyph-right-lower .code-a { left: auto; right: 22px; top: auto; bottom: 33%; transform: rotate(12deg); }
.code-c { left: 24px; bottom: 140px; font-size: 11px; transform: rotate(-8deg); animation-delay: .4s; }
.code-d { right: 12px; top: 46px; font-size: 12px; animation-delay: .6s; }
.ambient-dot { position: absolute; width: 4px; height: 4px; background: #c8b7fa; border-radius: 50%; opacity: .35; left: calc(4% + var(--i) * 12%); bottom: calc(12px + var(--i) * 3px); animation: dot-rise calc(7s + var(--i) * .6s) ease-in-out infinite; animation-delay: calc(var(--i) * .12s); }
.ambient-grid { position: absolute; bottom: 0; left: 0; right: 0; height: 100px; opacity: .1; background-image: linear-gradient(#ad95dd 1px, transparent 1px), linear-gradient(90deg, #ad95dd 1px, transparent 1px); background-size: 32px 32px; mask-image: linear-gradient(transparent, #000); animation: grid-travel 12s linear infinite; }
@keyframes grid-travel { to { background-position: 32px 32px; } }
@keyframes ambient-drift { from { translate: -3px 4px; } to { translate: 9px -22px; } }
@keyframes dot-rise { 0%, 100% { transform: translateY(0); opacity: .08; } 50% { transform: translateY(-65px); opacity: .45; } }
@keyframes circuit-flow { to { stroke-dashoffset: -476; } }
</style>
