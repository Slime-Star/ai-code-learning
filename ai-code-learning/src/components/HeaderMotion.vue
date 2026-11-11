<template>
  <div class="header-motion" :class="{purple, warm:page==='PointsMall', teacher}" aria-hidden="true">
    <svg class="desktop-scene" viewBox="0 0 1200 72" fill="none" xmlns="http://www.w3.org/2000/svg" focusable="false">
      <path d="M150 39h103l16-10h75m382 12h93l22-12h82" stroke="currentColor" stroke-opacity=".15" stroke-dasharray="3 7" />
      <circle r="2.5" fill="currentColor" opacity=".6"><animateMotion path="M150 39h103l16-10h75" dur="8s" repeatCount="indefinite" /></circle>
      <g class="header-terminal" stroke="currentColor" stroke-width="1.3" stroke-linejoin="round" opacity=".65">
        <rect x="71" y="14" width="75" height="44" rx="7" fill="currentColor" fill-opacity=".04" /><path d="M71 26h75" opacity=".5" /><circle cx="80" cy="20" r="1" /><circle cx="86" cy="20" r="1" /><path d="m82 35 7 5-7 5m15 0h12" /><path class="header-code-line" d="M116 36h17m-17 9h10" stroke-dasharray="30" />
      </g>
      <g class="header-brackets" fill="currentColor" opacity=".38" font-family="Consolas, monospace" font-size="24"><text x="349" y="46">{{ pack.symbol }}</text></g>
      <g v-if="theme!==1" stroke="currentColor" stroke-width="1.1"><ellipse cx="600" cy="36" rx="59" ry="15" transform="rotate(-10 600 36)" opacity=".3" /><circle cx="600" cy="36" r="22" stroke-dasharray="2 6" opacity=".3" /><g transform="rotate(-10 600 36)"><circle r="3" fill="currentColor" opacity=".7"><animateMotion path="M541 36A59 15 0 1 0 659 36A59 15 0 1 0 541 36" dur="9s" repeatCount="indefinite" /></circle></g><path d="m594 30-6 6 6 6m12-12 6 6-6 6" opacity=".5" /></g>
      <g v-else class="header-chip" stroke="currentColor" stroke-width="1.2" opacity=".5"><rect x="579" y="17" width="42" height="38" rx="7" fill="currentColor" fill-opacity=".04" /><path d="M588 11v6m12-6v6m12-6v6m-24 38v6m12-6v6m12-6v6M573 26h6m-6 11h6m-6 11h6m42-22h6m-6 11h6m-6 11h6" /><path class="chip-check" d="m590 36 6 6 14-15" /></g>
      <g class="header-label" stroke="currentColor" stroke-width="1.1"><rect x="873" y="21" width="108" height="30" rx="8" fill="currentColor" fill-opacity=".035" opacity=".45" /><text x="887" y="40" fill="currentColor" stroke="none" opacity=".55" font-family="Consolas, monospace" font-size="10">{{ theme===0?'hello, ideas':theme===1?'keep exploring':'build(something)' }}</text></g>
      <g class="header-spark" stroke="currentColor" stroke-width="1.3" stroke-linecap="round" opacity=".45"><path d="M1105 20v14m-7-7h14m-40 20v8m-4-4h8" /><circle cx="1142" cy="47" r="2" fill="currentColor" stroke="none" /></g>
    </svg>
    <svg class="mobile-scene" viewBox="0 0 360 48" fill="none" focusable="false"><path d="M30 25h75m150 0h75" stroke="currentColor" stroke-opacity=".18" stroke-dasharray="3 6" /><text x="139" y="30" fill="currentColor" opacity=".4" font-family="Consolas, monospace" font-size="13">{{ pack.symbol }}</text><circle r="2" fill="currentColor" opacity=".5"><animateMotion path="M30 25h75m150 0h75" dur="9s" repeatCount="indefinite" /></circle><g class="header-spark" stroke="currentColor" stroke-opacity=".4"><path d="M21 18v10m-5-5h10m297-5v10m-5-5h10" /></g></svg>
  </div>
</template>
<script setup>
import {computed} from 'vue'
import {getBackdropTheme} from '@/config/backdropThemes'
const props=defineProps({page:{type:String,default:''},teacher:Boolean})
const pack=computed(()=>getBackdropTheme(props.page))
const purple=computed(()=>['Home','LearningCenter','Library','Competition','Leaderboard','DailyCheckIn','DailySignin'].includes(props.page))
const theme=computed(()=>Array.from(props.page).reduce((sum,char)=>sum+char.charCodeAt(0),0)%3)
</script>
<style scoped>
.header-motion { --header-ink: #a78fbe; position: absolute; inset: 0; overflow: hidden; color: var(--header-ink); pointer-events: none; user-select: none; z-index: -1; opacity: .65; }
.header-motion.purple { --header-ink: #e4d8fb; }.header-motion.warm { --header-ink: #a77a83; }.header-motion.teacher { --header-ink: #ddcef8; }
.desktop-scene { display: block; position: absolute; top: 5px; right: 0; width: min(78%,1000px); height: 110px; margin: 0; }.mobile-scene { display: none; }
.header-terminal { animation: header-terminal 5.5s ease-in-out infinite alternate; }.header-brackets { transform-origin: 370px 36px; animation: header-brackets 7s ease-in-out infinite alternate; }.header-label { animation: header-label 6.5s ease-in-out infinite alternate; }.header-code-line { animation: header-code 4s ease-in-out infinite; }.header-spark { animation: header-spark 3s ease-in-out infinite alternate; }.chip-check { stroke-dasharray: 36; animation: header-code 5s ease-in-out infinite; }
@keyframes header-terminal { to { transform: translate(4px,-4px) rotate(1deg); } }@keyframes header-brackets { from { transform: rotate(-6deg); } to { transform: rotate(6deg); } }@keyframes header-label { from { transform: translateY(-2px); } to { transform: translateY(4px); } }@keyframes header-code { 0% { stroke-dashoffset: 36; } 55%,85% { stroke-dashoffset: 0; } 100% { opacity: .15; } }@keyframes header-spark { from { opacity: .2; } to { opacity: .7; } }
@media (max-width: 640px) { .desktop-scene { display: none; }.mobile-scene { display: block; position: absolute; right: 0; top: 4px; width: 72%; height: 42px; opacity: .5; } }
</style>
