<template>
  <div class="topic-art" :class="[scene, { inverse, compact, featured }]" aria-hidden="true">
    <svg v-if="['books', 'debug', 'data'].includes(scene)" class="art-trail" viewBox="0 0 800 120" fill="none" focusable="false"><path d="M25 70h95l20-20h95m300 10h90l20 20h110" stroke="currentColor" stroke-dasharray="4 8" /><circle cx="25" cy="70" r="4" stroke="currentColor" /><circle cx="755" cy="80" r="4" stroke="currentColor" /><path d="m265 43-10 17 10 17m270-34 10 17-10 17" stroke="currentColor" stroke-width="2" /></svg>
    <svg class="art-scene" viewBox="0 0 320 200" fill="none" xmlns="http://www.w3.org/2000/svg" focusable="false">
      <g stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round">
        <g v-if="scene === 'books'">
          <path d="M48 164h224" opacity=".45" />
          <rect x="72" y="65" width="32" height="98" rx="5" fill="currentColor" fill-opacity=".06" /><path d="M80 78h16m-16 7h16m-8 58v9" />
          <rect x="110" y="45" width="43" height="118" rx="5" fill="currentColor" fill-opacity=".1" /><path d="m121 78 7-7-7-7m14 20h8M120 143h23m-23 7h23" />
          <path d="m170 60 31-9 28 105-31 8-28-104Z" fill="currentColor" fill-opacity=".07" /><path d="m177 75 30-8m-7 79 20-5" />
          <rect x="230" y="102" width="25" height="61" rx="4" /><path d="M237 112h11m-11 7h11" />
          <path d="M52 47h12m-6-6v12m189-20h10m-5-5v10" opacity=".4" />
        </g>
        <g v-else-if="scene === 'chat'">
          <path d="M65 48h125a12 12 0 0 1 12 12v58a12 12 0 0 1-12 12h-76l-28 20v-20H65a12 12 0 0 1-12-12V60a12 12 0 0 1 12-12Z" fill="currentColor" fill-opacity=".05" />
          <path d="m84 76-12 12 12 12m41-24 12 12-12 12m-15-31-11 37" /><path d="M151 80h29m-29 13h20" opacity=".55" />
          <path d="M220 85h28a12 12 0 0 1 12 12v57a12 12 0 0 1-12 12h-7v16l-22-16h-60a12 12 0 0 1-12-12v-10" />
          <circle cx="180" cy="148" r="2" fill="currentColor" /><circle cx="199" cy="148" r="2" fill="currentColor" /><circle cx="218" cy="148" r="2" fill="currentColor" />
          <path d="m238 45 8-8 8 8-8 8-8-8Z" opacity=".4" />
        </g>
        <g v-else-if="scene === 'trophy'">
          <path d="M62 170h195m-174 0v-28h48v28m0 0v-48h55v48m0 0v-19h45v19" opacity=".5" />
          <path d="M133 38h53v35a26.5 26.5 0 0 1-53 0V38Z" fill="currentColor" fill-opacity=".08" /><path d="M133 47h-17v15a21 21 0 0 0 21 21m49-36h17v15a21 21 0 0 1-21 21m-23 17v14m-16 0h32m-16-68 4 9 10 1-8 7 2 10-8-5-9 5 2-10-8-7 11-1 4-9Z" />
          <path d="m92 68-5-12m137 8 7-9M82 103H70m166 0h12" opacity=".6" />
        </g>
        <g v-else-if="scene === 'gift'">
          <rect x="108" y="89" width="106" height="72" rx="7" fill="currentColor" fill-opacity=".06" /><rect x="99" y="73" width="124" height="24" rx="5" /><path d="M151 73v88m20-88v88" />
          <path d="M160 73c-6-39-51-34-40-12 6 11 40 12 40 12Zm0 0c6-39 51-34 40-12-6 11-40 12-40 12Z" fill="currentColor" fill-opacity=".07" />
          <circle cx="63" cy="115" r="16" /><path d="m58 111 4-4 4 4m-4-4v15m-6-1h12" /><circle cx="255" cy="66" r="12" /><path d="M255 61v10m-4-5h8m-7 76 7-8 7 8-7 8-7-8ZM69 54v12m-6-6h12" />
        </g>
        <g v-else-if="scene === 'calendar'">
          <rect x="87" y="46" width="139" height="118" rx="12" fill="currentColor" fill-opacity=".04" /><path d="M87 78h139M116 35v22m81-22v22" />
          <g opacity=".5"><path d="M108 96h12m18 0h12m18 0h12m18 0h10M108 116h12m18 0h12m18 0h12m18 0h10M108 136h12m18 0h12" /></g>
          <circle cx="205" cy="146" r="27" fill="currentColor" fill-opacity=".08" /><path d="m192 145 9 9 17-20" stroke-width="3" /><path d="m51 98 13 6-13 6m201-54h12m-6-6v12" opacity=".6" />
        </g>
        <g v-else-if="scene === 'team'">
          <circle cx="160" cy="56" r="17" /><path d="M132 107V99a28 28 0 0 1 56 0v8Z" fill="currentColor" fill-opacity=".08" /><circle cx="84" cy="129" r="13" /><circle cx="236" cy="129" r="13" /><path d="M61 171a23 23 0 0 1 46 0m106 0a23 23 0 0 1 46 0M160 119v27m-51-13 23-18m55 0 24 18" />
          <rect x="142" y="151" width="36" height="27" rx="6" /><path d="m154 160-5 5 5 5m13-10 5 5-5 5" /><path d="M53 73h30m154 0h30" stroke-dasharray="3 6" opacity=".45" />
        </g>
        <g v-else-if="scene === 'debug'">
          <rect x="68" y="40" width="144" height="111" rx="10" fill="currentColor" fill-opacity=".04" /><path d="M68 65h144m-127 17h20m10 0h39M85 97h54m-54 15h32" opacity=".7" />
          <circle cx="205" cy="133" r="34" fill="currentColor" fill-opacity=".05" /><path d="m229 157 28 28" stroke-width="5" /><rect x="195" y="122" width="20" height="25" rx="9" /><path d="M200 121v-7m10 7v-7m-15 16h-8m8 10h-8m28-10h8m-8 10h8m-18-13v13M82 162l-7 7 7 7" />
        </g>
        <g v-else-if="scene === 'identity'">
          <rect x="69" y="44" width="182" height="117" rx="13" fill="currentColor" fill-opacity=".05" /><circle cx="118" cy="90" r="18" /><path d="M91 139v-6a27 27 0 0 1 54 0v6m21-54h58m-58 15h40m-40 21h49" />
          <path d="m218 137 8 8 17-18" stroke-width="3" /><path d="M53 70H35m249 53h-18m-209 52 8 8m197-147 7 7" opacity=".5" />
        </g>
        <g v-else-if="scene === 'shield'">
          <path d="M160 32c18 15 41 23 67 25v48c0 34-28 59-67 76-39-17-67-42-67-76V57c26-2 49-10 67-25Z" fill="currentColor" fill-opacity=".05" />
          <rect x="136" y="87" width="48" height="41" rx="8" /><path d="M145 87V75a15 15 0 0 1 30 0v12m-15 16v9M54 81l12-8m195 40 12 8m-211 34h20m176-104h12m-6-6v12" />
        </g>
        <g v-else-if="scene === 'launch'">
          <path d="M126 125c7-43 32-72 75-88 8 45-2 81-37 107l-38-19Z" fill="currentColor" fill-opacity=".06" /><circle cx="173" cy="82" r="12" /><path d="m128 109-27 9-7 27 33-9m45 0-1 31-24 17-2-34m-24-7-17 30m6-38-18 25m43-17-10 25M219 53h15m-7-7v14m-157 4h10m-5-5v10" />
          <path d="M199 169h47m-174 15h33" stroke-dasharray="2 7" opacity=".5" />
        </g>
        <g v-else-if="scene === 'chip'">
          <rect x="115" y="56" width="90" height="90" rx="12" fill="currentColor" fill-opacity=".06" /><rect x="130" y="71" width="60" height="60" rx="7" />
          <path d="M133 43v13m18-13v13m18-13v13m18-13v13m-54 90v13m18-13v13m18-13v13m18-13v13M102 74h13m-13 18h13m-13 18h13m-13 18h13m90-54h13m-13 18h13m-13 18h13m-13 18h13" />
          <path d="m147 91-10 10 10 10m26-20 10 10-10 10m-9-24-8 28M68 71h13m159 66h13M57 148h22m167-97h19" opacity=".65" />
        </g>
        <g v-else-if="scene === 'orbit'">
          <ellipse cx="160" cy="102" rx="105" ry="36" transform="rotate(-25 160 102)" opacity=".5" /><ellipse cx="160" cy="102" rx="105" ry="36" transform="rotate(35 160 102)" opacity=".4" />
          <circle cx="160" cy="102" r="28" fill="currentColor" fill-opacity=".08" /><path d="m151 91-11 11 11 11m18-22 11 11-11 11m-5-25-8 28" />
          <circle cx="66" cy="84" r="7" fill="currentColor" fill-opacity=".2" /><circle cx="237" cy="62" r="9" fill="currentColor" fill-opacity=".12" /><circle cx="228" cy="145" r="5" fill="currentColor" fill-opacity=".3" /><path d="M92 163v12m-6-6h12m139-132v9m-4-4h8" opacity=".5" />
        </g>
        <g v-else-if="scene === 'pipeline'">
          <path d="M74 103h171m-84-35v35" stroke-dasharray="4 5" opacity=".5" /><rect x="40" y="80" width="68" height="46" rx="8" fill="currentColor" fill-opacity=".05" /><rect x="128" y="80" width="68" height="46" rx="8" fill="currentColor" fill-opacity=".05" /><rect x="216" y="80" width="68" height="46" rx="8" fill="currentColor" fill-opacity=".05" />
          <path d="m63 95-8 8 8 8m20-16 8 8-8 8m-10-20-6 24m83-20 7 7 14-14m65 14h27m-8-7 8 7-8 7" />
          <circle cx="162" cy="47" r="18" /><path d="m155 47 5 5 9-10M56 149h33m57 0h33m58 0h27" opacity=".55" />
        </g>
        <g v-else>
          <path d="M72 160h183M88 147V94h26v53m22 0V61h26v86m22 0v-38h26v38m22 0V79h26v68" fill="currentColor" fill-opacity=".07" /><path d="m92 70 54-33 51 35 49-34" stroke-dasharray="4 6" /><circle cx="146" cy="37" r="5" /><circle cx="197" cy="72" r="5" /><path d="M55 41v10m-5-5h10" opacity=".5" />
        </g>
      </g>
      <g class="art-code-notes" fill="currentColor" opacity=".35" font-family="Consolas, monospace" font-size="8">
        <text x="25" y="25">{{ (codeNotes[scene] || codeNotes.data)[0] }}</text>
        <text x="230" y="185">{{ (codeNotes[scene] || codeNotes.data)[1] }}</text>
        <circle cx="284" cy="34" r="2" /><circle cx="36" cy="178" r="2" />
      </g>
      <circle r="2.7" fill="currentColor" opacity=".65"><animateMotion dur="8s" repeatCount="indefinite" path="M25 100 C25 30 295 30 295 100 C295 180 25 180 25 100" /></circle>
    </svg>
    <AnimatedCompanion v-if="!compact && scene === 'launch'" class="corner-companion" kind="rocket" />
  </div>
</template>

<script setup>
import AnimatedCompanion from '@/components/AnimatedCompanion.vue'
defineProps({ scene: { type: String, default: 'data' }, inverse: Boolean, compact: Boolean, featured: Boolean })
const codeNotes = {
  books: ['read(doc)', '.md'], chat: ['ask()', 'reply()'], trophy: ['level++', 'next()'],
  gift: ['collect()', '+1'], calendar: ['today()', 'done'], team: ['branch', 'merge'],
  debug: ['inspect()', 'fix()'], identity: ['profile', 'grow++'], shield: ['verify()', 'secure'],
  launch: ['build()', 'go!'], chip: ['1010', '0101'], orbit: ['explore()', '∞'],
  pipeline: ['input', 'output'], data: ['data[]', 'sum()']
}
</script>

<style scoped>
.topic-art { position: relative; isolation: isolate; max-width: 1100px; width: calc(100% - 40px); margin: 20px auto 0; height: 164px; display: flex; justify-content: center; align-items: center; pointer-events: none; user-select: none; color: #a699c8; opacity: .7; flex-shrink: 0; }
.art-scene { width: 250px; max-width: 100%; height: 156px; display: block; }
.art-trail { position: absolute; inset: 20px 0; width: 100%; height: 120px; opacity: .3; z-index: -1; }
.books { justify-content: flex-start; padding-left: 10%; color: #9c8abe; }
.chat { justify-content: flex-end; padding-right: 12%; color: #8c9dc5; }
.trophy { color: #b89b6a; }
.gift { justify-content: flex-start; padding-left: 15%; color: #b391bc; }
.calendar { color: #8c9cbe; }
.team { justify-content: flex-end; padding-right: 15%; color: #97a3c2; }
.debug { justify-content: flex-start; padding-left: 12%; color: #a78fba; }
.identity { color: #a5a0c6; }
.shield { color: #a79cc4; }
.launch { justify-content: flex-end; padding-right: 8%; color: #a191c3; }
.orbit { color: #919fc8; }
.pipeline { justify-content: flex-start; padding-left: 8%; color: #9d92bd; }
.chip { justify-content: flex-end; padding-right: 10%; color: #9690b7; }
.inverse { color: #e3d7ff; opacity: .65; }
.compact { width: 100%; max-width: 300px; padding: 0; height: 145px; margin-top: 18px; justify-content: center; }
.compact .art-scene { height: 145px; }
.compact .art-trail { display: none; }
.corner-companion { position: absolute; right: 8%; bottom: 8px; width: 135px; }
.chat .corner-companion,.team .corner-companion,.launch .corner-companion,.chip .corner-companion { left: 8%; right: auto; }
@media (max-width: 1100px) { .corner-companion { display: none; } }
.featured { height: 212px; }
.featured .art-scene { width: 340px; height: 212px; }
.featured::before { content: ''; position: absolute; left: 50%; top: 50%; width: 220px; height: 150px; border-radius: 50%; transform: translate(-50%,-50%); background: radial-gradient(ellipse,#c8b5e414,transparent 70%); z-index: -1; }
.art-scene { animation: illustration-float 7s ease-in-out infinite alternate; }
.art-trail path { animation: illustration-flow 5s linear infinite; }
.art-code-notes circle { transform-box: fill-box; transform-origin: center; animation: note-pulse 3s ease-in-out infinite alternate; }
.art-code-notes circle:nth-last-child(1) { animation-delay: -1.5s; }
@keyframes note-pulse { from { transform: scale(.7); opacity: .3; } to { transform: scale(1.4); opacity: 1; } }
.books .art-scene, .identity .art-scene { animation-name: illustration-sway; animation-duration: 9s; transform-origin: center bottom; }
.launch .art-scene { animation-name: illustration-launch; animation-duration: 5s; }
.orbit .art-scene { animation-name: illustration-orbit; animation-duration: 12s; }
.gift .art-scene, .trophy .art-scene { animation-delay: -3s; }
.chip .art-scene { animation-name: illustration-breathe; animation-duration: 4s; }
@keyframes illustration-float { from { transform: translateY(3px); } to { transform: translateY(-8px); } }
@keyframes illustration-sway { from { transform: rotate(-2deg); } to { transform: rotate(2deg); } }
@keyframes illustration-launch { from { transform: translate(-4px, 5px); } to { transform: translate(6px, -9px); } }
@keyframes illustration-orbit { from { transform: rotate(-7deg); } to { transform: rotate(7deg); } }
@keyframes illustration-breathe { from { opacity: .6; transform: scale(.98); } to { opacity: 1; transform: scale(1.02); } }
@keyframes illustration-flow { to { stroke-dashoffset: -120; } }
@media (max-width: 768px) { .topic-art { height: 115px; padding: 0; justify-content: center; margin-top: 12px; } .art-scene { height: 110px; width: 180px; } .art-trail { display: none; } .compact { height: 105px; } .compact .art-scene { height: 105px; } }
@media (prefers-contrast: more) { .topic-art { opacity: .4; } }
@media (max-width: 768px) { .topic-art.featured { height: 125px; }.topic-art.featured .art-scene { width: 180px; height: 110px; }.topic-art.featured::before { width: 160px; height: 100px; } }
</style>
