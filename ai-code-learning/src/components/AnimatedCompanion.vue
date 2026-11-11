<template>
  <div class="animated-companion" :class="kind" aria-hidden="true">
    <svg viewBox="0 0 180 160" fill="none" xmlns="http://www.w3.org/2000/svg" focusable="false">
      <ellipse cx="90" cy="145" rx="46" ry="5" fill="#a487c8" opacity=".12" />
      <g v-if="kind === 'robot'" class="robot-body" stroke="#a48ac5" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
        <path d="M77 126v13m25-13v13" stroke-width="7" /><path d="M68 141h14m16 0h14" stroke-width="5" />
        <rect x="56" y="83" width="64" height="47" rx="17" fill="#eee5f8" /><path d="m80 98-6 6 6 6m18-12 6 6-6 6" stroke="#b29bcf" />
        <g class="robot-wave"><path d="M55 94 37 88l-4-16" stroke-width="7" /><circle cx="32" cy="67" r="7" fill="#e5d5f3" /></g>
        <path class="robot-type" d="m120 96 12 15-12 12" stroke-width="7" />
        <g class="robot-head"><path d="M88 32V21" /><circle class="antenna" cx="88" cy="17" r="5" fill="#d9bbea" />
          <rect x="44" y="34" width="88" height="52" rx="21" fill="#f6f0fc" /><rect x="54" y="44" width="68" height="30" rx="12" fill="#e7dcf4" stroke="none" />
          <g class="robot-eyes" fill="#8e73b1" stroke="none"><rect x="67" y="51" width="7" height="11" rx="3.5" /><rect x="101" y="51" width="7" height="11" rx="3.5" /></g>
          <path d="M83 65q5 5 10 0" stroke="#9e7aba" /><ellipse cx="61" cy="65" rx="5" ry="2.5" fill="#e5bdd3" stroke="none" /><ellipse cx="115" cy="65" rx="5" ry="2.5" fill="#e5bdd3" stroke="none" />
        </g>
        <g class="tiny-laptop"><path d="m54 119 5 22h59l5-22H54Z" fill="#dcd0ed" /><path d="M54 143h70" stroke-width="3" /><path class="typing-line" d="M74 130h30" stroke="#ad93c9" stroke-width="2" stroke-dasharray="30" />
        </g>
        <g class="hello-bubble"><path d="M137 24h25v19h-10l-9 7v-7h-6V24Z" fill="#f0e6fa" stroke="#c6addd" /><path d="m143 30 4 4-4 4m9 0h5" stroke-width="1.5" /></g>
      </g>
      <g v-else-if="kind === 'rocket'" class="little-rocket" stroke-linecap="round" stroke-linejoin="round">
        <g class="rocket-flame"><path d="M78 106q-9 22 12 36 20-14 12-36" fill="#e3bad3" opacity=".8" /><path d="M84 108q-4 12 6 21 10-9 6-21" fill="#f4d9bc" /></g>
        <path d="M70 80 57 105l16-3m37-22 13 25-16-3" fill="#d0bbe8" stroke="#ac8ac9" stroke-width="1.5" />
        <path d="M72 108C61 65 70 39 90 24c20 15 29 41 18 84H72Z" fill="#f2eafa" stroke="#aa8ac7" stroke-width="1.8" />
        <path d="M76 40h28" stroke="#d3b8e6" stroke-width="2" /><circle cx="90" cy="67" r="11" fill="#bfdce4" stroke="#a792bd" stroke-width="1.5" /><path d="M86 61q6-3 9 3" stroke="#edf8fb" stroke-width="2" /><path d="M79 101h22" stroke="#bca2d1" stroke-width="2" />
      </g>
      <g v-else>
        <path class="flight-trail" d="M16 126c34 16 83-6 69-30S33 86 56 58s71-22 100 5" stroke="#c3b4dd" stroke-width="1.5" stroke-dasharray="3 6" />
        <g class="paper-plane"><path d="m62 73 91-34-31 72-18-27-42-11Z" fill="#e4dcf3" stroke="#a896c6" stroke-width="1.7" stroke-linejoin="round" /><path d="m104 84 49-45-58 38m9 7-2 20 20 7" fill="#f6f0fc" stroke="#b4a1cf" stroke-width="1.4" stroke-linejoin="round" /></g>
        <circle r="3" fill="#bda5d4"><animateMotion path="M16 126c34 16 83-6 69-30S33 86 56 58s71-22 100 5" dur="5s" repeatCount="indefinite" /></circle>
      </g>
      <g class="companion-stars" stroke="#c1a8d8" stroke-width="1.3" stroke-linecap="round"><path d="M25 38v8m-4-4h8m117 81v8m-4-4h8" /><circle cx="151" cy="91" r="2" fill="#d2bde7" stroke="none" /></g>
    </svg>
  </div>
</template>

<script setup>
defineProps({kind:{type:String,default:'robot'}})
</script>

<style scoped>
.animated-companion { width: 150px; max-width: 100%; pointer-events: none; user-select: none; }svg { display: block; width: 100%; height: auto; }
.robot-body { animation: robot-bob 3.4s ease-in-out infinite; }.robot-eyes { transform-origin: 88px 57px; animation: robot-blink 4.8s infinite; }.robot-head { transform-origin: 88px 83px; animation: robot-nod 5.5s ease-in-out infinite; }.robot-wave { transform-origin: 54px 94px; animation: robot-wave 4s ease-in-out infinite; }.robot-type { animation: robot-type 650ms ease-in-out infinite alternate; }.antenna { animation: antenna-glow 2.4s ease-in-out infinite alternate; }.typing-line { animation: typing-line 2.5s steps(8) infinite; }.hello-bubble { animation: hello-bubble 5s ease-in-out infinite; }
.little-rocket { transform-origin: 90px 80px; animation: rocket-flight 3.6s ease-in-out infinite alternate; }.rocket-flame { transform-origin: 90px 106px; animation: flame-flicker 650ms ease-in-out infinite alternate; }.paper-plane { transform-origin: 104px 73px; animation: plane-cruise 7s ease-in-out infinite; }.flight-trail { animation: trail-flow 5s linear infinite; }.companion-stars { animation: companion-stars 3.5s ease-in-out infinite alternate; }
@keyframes robot-bob { 50% { transform: translateY(-4px); } }@keyframes robot-blink { 0%,42%,48%,100% { transform: scaleY(1); } 45% { transform: scaleY(.08); } }@keyframes robot-nod { 30% { transform: rotate(-4deg); } 65% { transform: rotate(3deg); } }@keyframes robot-wave { 0%,50%,100% { transform: rotate(0); } 15%,35% { transform: rotate(-22deg); } 25% { transform: rotate(-8deg); } }@keyframes robot-type { to { transform: translate(-2px,3px); } }@keyframes antenna-glow { to { filter: drop-shadow(0 0 4px #c9a7e9); } }@keyframes typing-line { 0% { stroke-dashoffset: 30; } 70%,100% { stroke-dashoffset: 0; } }@keyframes hello-bubble { 0%,75%,100% { opacity: 0; transform: translateY(4px); } 12%,60% { opacity: 1; transform: translateY(0); } }
@keyframes rocket-flight { from { transform: translateY(6px) rotate(-6deg); } to { transform: translateY(-15px) rotate(5deg); } }@keyframes flame-flicker { to { transform: scaleY(1.23) scaleX(.9); opacity: .65; } }@keyframes plane-cruise { 0%,100% { transform: translate(-12px,8px) rotate(-8deg); } 50% { transform: translate(9px,-13px) rotate(8deg); } }@keyframes trail-flow { to { stroke-dashoffset: -90; } }@keyframes companion-stars { from { opacity: .35; } to { opacity: .9; } }
</style>
