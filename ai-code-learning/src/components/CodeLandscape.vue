<template>
  <div class="code-landscape" :class="[variant,{inverse}]" aria-hidden="true">
    <svg viewBox="0 0 500 250" fill="none" xmlns="http://www.w3.org/2000/svg" focusable="false">
      <ellipse cx="250" cy="218" rx="178" ry="13" fill="currentColor" opacity=".035" />
      <g stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">
        <g v-if="variant === 'planet'">
          <circle cx="248" cy="125" r="75" fill="currentColor" fill-opacity=".045" stroke-opacity=".35" />
          <ellipse cx="248" cy="125" rx="155" ry="40" transform="rotate(-20 248 125)" stroke-opacity=".55" />
          <g transform="rotate(-20 248 125)"><circle r="5" fill="currentColor" fill-opacity=".8" stroke="none"><animateMotion dur="9s" repeatCount="indefinite" path="M93 125 A155 40 0 1 0 403 125 A155 40 0 1 0 93 125" /></circle></g>
          <ellipse cx="248" cy="125" rx="55" ry="75" transform="rotate(20 248 125)" stroke-dasharray="3 7" stroke-opacity=".2" />
          <g transform="rotate(20 248 125)"><circle r="3" fill="currentColor" fill-opacity=".65" stroke="none"><animateMotion dur="12s" begin="-4s" repeatCount="indefinite" path="M193 125 A55 75 0 1 1 303 125 A55 75 0 1 1 193 125" /></circle></g>
          <path d="m221 104-22 21 22 21m53-42 22 21-22 21m-18-50-16 59" stroke-width="3" stroke-opacity=".65" />
          <g class="satellite"><rect x="349" y="40" width="55" height="38" rx="8" fill="currentColor" fill-opacity=".065" stroke-opacity=".4" /><path d="M359 52h24m-24 7h34m-34 7h17" stroke-opacity=".5" /></g>
          <circle cx="111" cy="166" r="12" fill="currentColor" fill-opacity=".12" stroke-opacity=".5" /><circle cx="345" cy="177" r="5" fill="currentColor" fill-opacity=".4" stroke="none" />
          <path d="m82 66 8-11 8 11-8 11-8-11Zm311 112h15m-7-7v14m-277 37h16m-8-8v16" stroke-opacity=".4" />
        </g>
        <g v-else-if="variant === 'terminal'">
          <rect x="136" y="29" width="239" height="145" rx="14" transform="rotate(6 136 29)" fill="currentColor" fill-opacity=".025" stroke-opacity=".2" />
          <rect x="103" y="49" width="250" height="150" rx="13" fill="currentColor" fill-opacity=".04" stroke-opacity=".5" /><path d="M103 77h250" stroke-opacity=".3" />
          <g fill="currentColor" stroke="none" opacity=".45"><circle cx="120" cy="63" r="3" /><circle cx="131" cy="63" r="3" /><circle cx="142" cy="63" r="3" /></g>
          <path d="m125 99 11 10-11 10" stroke-opacity=".7" stroke-width="2.5" /><path class="terminal-cursor" d="M146 119h18" stroke-opacity=".7" stroke-width="2.5" />
          <g stroke-width="5" opacity=".42"><path class="code-line line-a" pathLength="1" d="M126 142h32m12 0h68" /><path class="code-line line-b" pathLength="1" d="M138 157h46m12 0h83" /><path class="code-line line-c" pathLength="1" d="M126 172h25m13 0h61" /></g>
          <g class="satellite"><rect x="315" y="137" width="86" height="67" rx="12" fill="currentColor" fill-opacity=".07" stroke-opacity=".5" /><path d="m344 159-12 12 12 12m27-24 12 12-12 12m-9-30-9 37" stroke-opacity=".6" stroke-width="2" /></g>
          <path d="M71 101H53m9-9v18m334-76 9-6 9 6-9 6-9-6Zm-327 76h-8m4-4v8" stroke-opacity=".4" /><path d="M54 194h24m327-84h35" stroke-dasharray="2 6" stroke-opacity=".4" />
        </g>
        <g v-else>
          <path d="M184 118h-57l-25-25H48m136 44h-44l-33 33H57m255-52h46l22-22h73m-141 41h61l25 25h51M218 74V45l-20-20m79 49V44l20-19m-79 153v29l-20 20m79-49v29l20 20" stroke-opacity=".3" />
          <rect x="180" y="70" width="138" height="110" rx="16" fill="currentColor" fill-opacity=".045" stroke-opacity=".55" /><rect x="197" y="87" width="104" height="76" rx="9" stroke-opacity=".3" />
          <path d="m231 110-15 15 15 15m35-30 15 15-15 15m-13-37-9 43" stroke-opacity=".65" stroke-width="2.5" />
          <g stroke-opacity=".45"><path d="M205 58v12m22-12v12m22-12v12m22-12v12m22-12v12M205 180v12m22-12v12m22-12v12m22-12v12m22-12v12M168 94h12m-12 21h12m-12 21h12m-12 21h12m138-63h12m-12 21h12m-12 21h12m-12 21h12" /></g>
          <g fill="currentColor" fill-opacity=".12" stroke-opacity=".5"><circle cx="48" cy="93" r="5" /><circle cx="57" cy="170" r="5" /><circle cx="453" cy="96" r="5" /><circle cx="449" cy="162" r="5" /></g>
          <circle r="3.5" fill="currentColor" stroke="none"><animateMotion dur="3.8s" repeatCount="indefinite" path="M48 93 H102 L127 118 H184" /><animate attributeName="opacity" values="0;.9;.9;0" keyTimes="0;.1;.8;1" dur="3.8s" repeatCount="indefinite" /></circle>
          <circle r="3.5" fill="currentColor" stroke="none"><animateMotion dur="4.5s" begin="-2s" repeatCount="indefinite" path="M318 137 H379 L404 162 H449" /><animate attributeName="opacity" values="0;.8;.8;0" keyTimes="0;.1;.8;1" dur="4.5s" begin="-2s" repeatCount="indefinite" /></circle>
          <rect class="chip-wave" x="180" y="70" width="138" height="110" rx="16" stroke-opacity=".5" />
        </g>
      </g>
      <g fill="currentColor" opacity=".32" font-family="Consolas, monospace" font-size="9"><text x="38" y="38">{{ variant === 'planet' ? 'explore()' : variant === 'terminal' ? 'hello, ideas' : '0101 1010' }}</text><text x="389" y="224">{{ variant === 'planet' ? '∞ possibilities' : variant === 'terminal' ? 'keep coding' : 'process()' }}</text></g>
    </svg>
  </div>
</template>

<script setup>
defineProps({variant:{type:String,default:'planet'},inverse:Boolean})
</script>

<style scoped>
.code-landscape { width: 100%; max-width: 560px; min-width: 0; color: #ad97cd; opacity: .8; pointer-events: none; user-select: none; margin: 0 auto; }
svg { display: block; width: 100%; height: auto; max-height: 220px; animation: landscape-drift 11s ease-in-out infinite alternate; }
.code-line { stroke-dasharray: 1; animation: code-writing 7s ease-in-out infinite both; }
.line-b { animation-delay: .7s; }.line-c { animation-delay: 1.4s; }
.terminal-cursor { animation: terminal-blink 1.3s step-end infinite; }
.chip-wave { transform-origin: 249px 125px; animation: chip-wave 4s ease-out infinite; }
@keyframes code-writing { 0%,12% { stroke-dashoffset: 1; opacity: .1; } 40%,80% { stroke-dashoffset: 0; opacity: 1; } 100% { stroke-dashoffset: 0; opacity: 0; } }
@keyframes terminal-blink { 50% { opacity: 0; } }
@keyframes chip-wave { from { transform: scale(1); opacity: .6; } to { transform: scale(1.25); opacity: 0; } }
.inverse { color: #dfd1fc; opacity: .7; }.chip { color: #9fafd0; }.inverse.chip { color: #d9d9fc; }.satellite { animation: satellite-float 6s ease-in-out infinite alternate; }.signal-dot { animation: signal-breathe 3s ease-in-out infinite alternate; }
@keyframes landscape-drift { from { transform: translateY(3px); } to { transform: translateY(-10px); } }
@keyframes satellite-float { from { transform: translateY(0); } to { transform: translateY(-14px); } }
@keyframes signal-breathe { from { opacity: .2; } to { opacity: .9; } }
@media (max-width: 768px) { svg { max-height: 145px; } }
</style>
