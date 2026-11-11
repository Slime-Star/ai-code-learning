<template>
  <div class="code-ticker" :class="{inverse,reverse}" aria-hidden="true">
    <div class="ticker-track"><div v-for="copy in 2" :key="copy" class="ticker-copy"><span v-for="item in snippets" :key="item"><i>✦</i><code>{{ item }}</code></span></div></div>
  </div>
</template>

<script setup>
defineProps({inverse:Boolean,reverse:Boolean})
const snippets=['const curiosity = true;','learn() → practice()','if (stuck) ask();','ideas.push("try again");','while (curious) build();','// small steps, real progress']
</script>

<style scoped>
.code-ticker { width: calc(100% - 40px); max-width: 1280px; height: 42px; margin: 12px auto; overflow: hidden; color: #a38abb; opacity: .72; pointer-events: none; user-select: none; mask-image: linear-gradient(90deg,transparent,#000 8%,#000 92%,transparent); border-top: 1px solid #d8c9e529; border-bottom: 1px solid #d8c9e529; }
.ticker-track { display: flex; width: max-content; animation: code-marquee 42s linear infinite; }
.ticker-copy { display: flex; flex-shrink: 0; align-items: center; justify-content: space-around; min-width: 1280px; height: 42px; padding-right: 32px; gap: 32px; }
.ticker-copy span { display: inline-flex; align-items: center; gap: 18px; white-space: nowrap; }.ticker-copy i { font-size: 10px; font-style: normal; color: #bda5d3; }.ticker-copy code { font: 11px Consolas,monospace; }
.inverse { color: #e7dafa; border-color: #ffffff18; }.reverse .ticker-track { animation-direction: reverse; animation-duration: 48s; }
@keyframes code-marquee { from { transform: translateX(0); } to { transform: translateX(-50%); } }
@media (max-width: 768px) { .code-ticker { height: 36px; }.ticker-copy { height: 36px; } }
</style>
