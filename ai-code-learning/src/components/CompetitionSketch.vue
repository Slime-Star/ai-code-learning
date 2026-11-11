<template>
  <div class="competition-sketch" :class="variant" aria-hidden="true">
    <svg viewBox="0 0 340 220" fill="none" xmlns="http://www.w3.org/2000/svg" focusable="false">
      <defs><pattern :id="patternId" width="16" height="16" patternUnits="userSpaceOnUse"><rect width="8" height="8" fill="currentColor" opacity=".22" /><rect x="8" y="8" width="8" height="8" fill="currentColor" opacity=".22" /></pattern></defs>
      <g stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round">
        <g v-if="variant === 'target'">
          <circle cx="164" cy="106" r="70" fill="currentColor" fill-opacity=".035" stroke-opacity=".3" /><circle cx="164" cy="106" r="48" stroke-opacity=".45" /><circle cx="164" cy="106" r="25" fill="currentColor" fill-opacity=".08" stroke-opacity=".6" /><circle cx="164" cy="106" r="5" fill="currentColor" opacity=".6" />
          <circle class="target-wave" cx="164" cy="106" r="25" stroke-opacity=".5" />
          <g class="target-arrow"><path d="m164 106 78-63m-14 11-1-18 15 7 15-1-3 17-17 2" /><path d="m164 106 13-3-6 12" /></g>
          <path d="M42 98h30l13-13m160 56h33l17 16M102 187l17-18m93 19-17-18" stroke-dasharray="3 6" opacity=".5" />
          <rect x="30" y="79" width="44" height="26" rx="6" fill="currentColor" fill-opacity=".04" /><path d="m41 87-5 5 5 5m17-10 5 5-5 5m-8-13-3 15" opacity=".6" />
        </g>
        <g v-else-if="variant === 'timer'">
          <circle cx="154" cy="116" r="60" fill="currentColor" fill-opacity=".04" stroke-opacity=".5" /><circle cx="154" cy="116" r="49" stroke-dasharray="2 10" stroke-opacity=".3" /><path d="M154 43V31m-15 0h30m28 29 10-12m-4-5 9 9" />
          <path class="timer-hand" d="M154 116V76" stroke-width="3" /><circle cx="154" cy="116" r="4" fill="currentColor" />
          <path d="M154 116h26" stroke-opacity=".4" /><path d="M81 181h145" opacity=".3" />
          <g class="code-ticket"><rect x="208" y="133" width="79" height="49" rx="9" fill="#f4eefb" stroke-opacity=".5" /><path d="m231 147-10 10 10 10m30-20 10 10-10 10m-13-25-7 29" opacity=".6" /></g>
          <path d="M61 63v12m-6-6h12m222 20v10m-5-5h10" opacity=".4" />
        </g>
        <g v-else>
          <path d="M44 178c25-50 58-62 91-34s57 20 79-9 54-38 89-22" stroke-dasharray="4 8" opacity=".4" />
          <circle r="4" fill="currentColor" stroke="none"><animateMotion path="M44 178c25-50 58-62 91-34s57 20 79-9 54-38 89-22" dur="7s" repeatCount="indefinite" /></circle>
          <path d="M80 151V60m-12 96h24m146-15V35m-12 111h24" stroke-opacity=".65" />
          <g class="race-flag flag-one"><path d="M80 60h55l-8 18 8 18H80V60Z" :fill="`url(#${patternId})`" stroke-opacity=".5" /></g>
          <g class="race-flag flag-two"><path d="M238 35h58l-9 20 9 20h-58V35Z" :fill="`url(#${patternId})`" stroke-opacity=".5" /></g>
          <path d="m166 62-12 11 12 11m29-22 12 11-12 11m-12-26-8 31M47 43v10m-5-5h10" stroke-opacity=".4" />
        </g>
      </g>
      <g fill="currentColor" opacity=".42" font-size="9" font-family="Consolas, monospace"><text x="26" y="25">{{ variant === 'target' ? 'focus()' : variant === 'timer' ? 'think → solve' : 'ready → go' }}</text><text x="247" y="204">{{ variant === 'target' ? 'one step closer' : variant === 'timer' ? 'keep calm' : 'challenge++' }}</text></g>
    </svg>
  </div>
</template>
<script setup>
import {useId} from 'vue'
defineProps({variant:{type:String,default:'target'}})
const patternId=`race-pattern-${useId()}`
</script>
<style scoped>
.competition-sketch { width: 100%; max-width: 360px; margin: 0 auto; pointer-events: none; user-select: none; color: #a995c3; }svg { display: block; width: 100%; height: auto; max-height: 250px; }.timer { color: #9aa9c6; }.flags { color: #b09bc4; }
.target-arrow { animation: arrow-settle 4s ease-in-out infinite; }.target-wave { transform-origin: 164px 106px; animation: target-wave 4s ease-out infinite; }.timer-hand { transform-origin: 154px 116px; animation: watch-tick 16s linear infinite; }.code-ticket { animation: ticket-float 5s ease-in-out infinite alternate; }.race-flag { transform-origin: 80px 60px; animation: flag-wave 3s ease-in-out infinite alternate; }.flag-two { transform-origin: 238px 35px; animation-delay: -1.5s; }
@keyframes arrow-settle { 0%,100% { transform: translate(3px,-3px); } 50% { transform: translate(-2px,2px); } }@keyframes target-wave { from { transform: scale(1); opacity: .5; } to { transform: scale(2.6); opacity: 0; } }@keyframes watch-tick { to { transform: rotate(360deg); } }@keyframes ticket-float { to { transform: translateY(-7px); } }@keyframes flag-wave { from { transform: skewY(-3deg) scaleX(.97); } to { transform: skewY(3deg) scaleX(1.02); } }
</style>
