<template>
  <div class="code-illustration" aria-hidden="true">
    <svg viewBox="0 0 320 240" fill="none" xmlns="http://www.w3.org/2000/svg" focusable="false">
      <defs>
        <pattern :id="gridId" width="20" height="20" patternUnits="userSpaceOnUse"><circle cx="1" cy="1" r="1" fill="currentColor" opacity=".22" /></pattern>
      </defs>
      <rect x="12" y="12" width="296" height="216" rx="24" :fill="`url(#${gridId})`" />
      <g v-if="variant === 'terminal'">
        <path d="M34 184h36m180-128h34M52 44v22m232 112v22" stroke="currentColor" opacity=".3" />
        <rect x="55" y="43" width="222" height="155" rx="14" fill="currentColor" fill-opacity=".05" stroke="currentColor" stroke-opacity=".45" />
        <path d="M55 73h222" stroke="currentColor" stroke-opacity=".3" />
        <g fill="currentColor" opacity=".65"><circle cx="71" cy="58" r="3" /><circle cx="83" cy="58" r="3" /><circle cx="95" cy="58" r="3" /></g>
        <path d="m79 96 13 10-13 10m23 0h19" stroke="currentColor" stroke-width="3" stroke-linecap="round" stroke-linejoin="round" />
        <g stroke="currentColor" stroke-width="5" stroke-linecap="round"><path d="M79 139h26m12 0h48" opacity=".6" /><path d="M91 153h62m12 0h34" opacity=".35" /><path d="M79 167h34m12 0h59" opacity=".45" /></g>
        <rect x="222" y="158" width="61" height="52" rx="10" fill="currentColor" fill-opacity=".1" stroke="currentColor" stroke-opacity=".6" />
        <path d="m243 176-8 8 8 8m19-16 8 8-8 8m-7-21-6 26" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" />
      </g>
      <g v-else-if="variant === 'network'">
        <g stroke="currentColor" stroke-opacity=".45" stroke-width="1.5"><path d="M160 65v40m-70 52h140M90 157v35m140-35v35m-70-60v60" /><path d="M90 157v-25h140v25" /></g>
        <rect x="127" y="30" width="66" height="44" rx="10" fill="currentColor" fill-opacity=".08" stroke="currentColor" stroke-opacity=".5" />
        <path d="m146 45-8 7 8 7m28-14 8 7-8 7m-12-16-5 18" stroke="currentColor" stroke-width="2" stroke-linecap="round" />
        <circle cx="160" cy="114" r="18" fill="currentColor" fill-opacity=".12" stroke="currentColor" stroke-opacity=".55" />
        <path d="m153 114 5 5 9-10" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" />
        <g fill="currentColor" fill-opacity=".07" stroke="currentColor" stroke-opacity=".4"><rect x="63" y="185" width="54" height="30" rx="7" /><rect x="133" y="185" width="54" height="30" rx="7" /><rect x="203" y="185" width="54" height="30" rx="7" /></g>
        <g stroke="currentColor" stroke-linecap="round" stroke-width="2" opacity=".65"><path d="M78 200h24m46 0h24m46 0h24" /></g>
        <g fill="currentColor" opacity=".4"><circle cx="90" cy="157" r="3" /><circle cx="230" cy="157" r="3" /><circle cx="160" cy="157" r="3" /></g>
        <path d="m42 92 9 5-9 5m230 38 8 5-8 5M46 164h10" stroke="currentColor" stroke-linecap="round" opacity=".35" />
      </g>
      <g v-else>
        <path d="m160 143 109 38-109 38-109-38 109-38Z" fill="currentColor" fill-opacity=".05" stroke="currentColor" stroke-opacity=".25" />
        <path d="m160 104 109 38-109 38-109-38 109-38Z" fill="currentColor" fill-opacity=".07" stroke="currentColor" stroke-opacity=".4" />
        <path d="m160 64 109 38-109 38-109-38 109-38Z" fill="currentColor" fill-opacity=".1" stroke="currentColor" stroke-opacity=".65" />
        <path d="m144 91-17 11 17 8m32-19 17 11-17 8m-10-23-12 28" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round" />
        <path d="M160 24v17m-8-8h16m116 125v12m-6-6h12M34 61v12m-6-6h12" stroke="currentColor" opacity=".45" />
      </g>
    </svg>
  </div>
</template>

<script setup>
import { useId } from 'vue'
defineProps({ variant: { type: String, default: 'terminal' } })
const gridId = `code-grid-${useId()}`
</script>

<style scoped>
.code-illustration { pointer-events: none; user-select: none; color: inherit; }
svg { display: block; width: 100%; height: auto; overflow: visible; }
svg { animation: code-art-float 8s ease-in-out infinite alternate; }
@keyframes code-art-float { from { transform: translateY(3px) rotate(-1deg); } to { transform: translateY(-7px) rotate(1deg); } }
</style>
