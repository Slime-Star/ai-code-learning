<template>
  <div class="edge-decorations" :class="`edge-theme-${theme}`" aria-hidden="true">
    <div class="edge-rail left-rail"><div class="data-stream"><div v-for="copy in 2" :key="copy"><span v-for="(token,index) in tokens" :key="index">{{ token }}</span></div></div></div>
    <div class="edge-rail right-rail"><svg viewBox="0 0 24 290" fill="none" focusable="false"><path d="M12 0v290" stroke="currentColor" stroke-opacity=".15" stroke-dasharray="2 8" /><circle v-for="y in [25,85,145,205,265]" :key="y" cx="12" :cy="y" r="5" stroke="currentColor" stroke-opacity=".4" /><circle r="3" fill="currentColor"><animateMotion path="M12 0V290" dur="7s" repeatCount="indefinite" /></circle><g class="edge-spinner"><path d="M12 125v40m-8-20h16m-13-8 10 16m-10 0 10-16" stroke="currentColor" stroke-opacity=".5" /></g></svg></div>
    <div class="edge-footer"><svg viewBox="0 0 1200 110" fill="none" xmlns="http://www.w3.org/2000/svg" focusable="false">
      <g v-if="theme !== 1" class="footer-wave" stroke="currentColor" stroke-width="1.3">
        <path d="M20 68h40l15-20 18 40 22-55 22 60 20-35h65l16-15 18 31 17-17h57" opacity=".35" />
        <circle r="3" fill="currentColor" stroke="none"><animateMotion path="M20 68h40l15-20 18 40 22-55 22 60 20-35h65l16-15 18 31 17-17h57" dur="9s" repeatCount="indefinite" /></circle>
        <path d="M26 89h44m208-62h34" stroke-dasharray="2 5" opacity=".25" />
      </g>
      <g v-else stroke="currentColor" stroke-width="1.2" opacity=".5">
        <path d="M40 76h58l28-38h68l28 38h75" stroke-dasharray="3 7" />
        <rect x="30" y="62" width="34" height="26" rx="6" /><rect x="138" y="24" width="40" height="28" rx="6" /><rect x="269" y="62" width="34" height="26" rx="6" />
        <circle r="3" fill="currentColor"><animateMotion path="M40 76h58l28-38h68l28 38h75" dur="8s" repeatCount="indefinite" /></circle>
      </g>
      <g class="footer-cubes" stroke="currentColor" stroke-width="1.3">
        <g class="code-cube cube-one"><path d="m510 34 27-15 27 15-27 16-27-16Zm0 0v30l27 16 27-16V34m-27 16v30" fill="currentColor" fill-opacity=".04" stroke-opacity=".45" /><path d="m519 47 6 4m19-1 7-4" stroke-opacity=".5" /></g>
        <g class="code-cube cube-two"><path d="m606 48 21-12 21 12-21 12-21-12Zm0 0v24l21 12 21-12V48m-21 12v24" fill="currentColor" fill-opacity=".04" stroke-opacity=".35" /></g>
        <path d="M488 96h180" stroke-opacity=".12" stroke-dasharray="2 6" />
      </g>
      <g v-if="theme !== 2" stroke="currentColor" stroke-width="1.2">
        <ellipse cx="1020" cy="58" rx="93" ry="20" transform="rotate(-12 1020 58)" stroke-opacity=".3" /><circle cx="1020" cy="58" r="28" stroke-opacity=".25" stroke-dasharray="3 6" />
        <g transform="rotate(-12 1020 58)"><circle r="3.5" fill="currentColor" stroke="none"><animateMotion path="M927 58A93 20 0 1 0 1113 58A93 20 0 1 0 927 58" dur="11s" repeatCount="indefinite" /></circle></g>
        <path d="m1011 51-7 7 7 7m18-14 7 7-7 7m-8-18-4 22" stroke-opacity=".45" />
      </g>
      <g v-else stroke="currentColor" stroke-width="1.2" stroke-opacity=".4">
        <path d="m925 78 46-48 65 29 43-31 67 51" stroke-dasharray="3 6" />
        <circle v-for="(point,index) in [[925,78],[971,30],[1036,59],[1079,28],[1146,79]]" :key="index" :cx="point[0]" :cy="point[1]" :r="index%2?5:3" fill="currentColor" fill-opacity=".1" />
        <circle r="3" fill="currentColor"><animateMotion path="m925 78 46-48 65 29 43-31 67 51" dur="9s" repeatCount="indefinite" /></circle>
      </g>
      <g fill="currentColor" opacity=".3" font-family="Consolas, monospace" font-size="9"><text x="380" y="50">{{ theme === 0 ? '0110' : theme === 1 ? 'send()' : 'signal' }}</text><text x="751" y="82">{{ theme === 2 ? 'connect()' : 'code → create' }}</text></g>
    </svg></div>
  </div>
</template>

<script setup>
import {computed} from 'vue'
const props=defineProps({page:{type:String,default:''}})
const theme=computed(()=>Array.from(props.page).reduce((sum,char)=>sum+char.charCodeAt(0),0)%3)
const tokens=['01','{}','10','</>','[]','11','=>','00','()','01','++','10']
</script>

<style scoped>
.edge-decorations { color: #ad98c7; pointer-events: none; user-select: none; }.edge-theme-1 { color: #a2afcc; }.edge-theme-2 { color: #b49ac8; }
.edge-rail { position: absolute; width: 22px; height: 290px; overflow: hidden; opacity: .38; z-index: 2; }.left-rail { left: 0; top: 28%; }.right-rail { right: 0; top: 60%; }.right-rail svg { display: block; width: 100%; height: 100%; }
.data-stream { animation: edge-data-flow 28s linear infinite; }.data-stream > div { height: 312px; display: flex; flex-direction: column; align-items: center; justify-content: space-around; }.data-stream span { font: 8px/1 Consolas,monospace; }
.edge-spinner { transform-origin: 12px 145px; animation: edge-spin 12s linear infinite; }.edge-footer { height: 110px; width: 100%; max-width: 1400px; margin: 0 auto; overflow: hidden; opacity: .8; }.edge-footer > svg { display: block; width: 100%; height: 110px; }.code-cube { animation: footer-cube-float 6s ease-in-out infinite alternate; }.cube-two { animation-delay: -3s; animation-duration: 7.5s; }
@keyframes edge-data-flow { to { transform: translateY(-312px); } }@keyframes edge-spin { to { transform: rotate(360deg); } }@keyframes footer-cube-float { from { transform: translateY(3px); } to { transform: translateY(-10px); } }
@media (max-width: 1100px) { .edge-rail { display: none; } }
@media (max-width: 768px) { .edge-footer { height: 76px; }.edge-footer > svg { width: 900px; max-width: none; height: 90px; position: relative; left: 50%; transform: translateX(-50%); } }
</style>
