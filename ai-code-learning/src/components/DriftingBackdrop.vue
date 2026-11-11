<template>
  <div :key="`${page}-${section}`" ref="backdrop" class="drifting-backdrop" :class="[pack.theme, `motion-${pack.motion}`, {inverse}]" :data-backdrop-theme="pack.theme" aria-hidden="true">
    <code class="drifting-item big-statement">{{ pack.phrase }}</code>
    <div class="drifting-item background-motif">
      <CodeIllustration v-if="pack.kind === 'code'" :variant="pack.scene" />
      <TopicArt v-else-if="pack.kind === 'topic'" :scene="pack.scene" compact />
      <CompetitionSketch v-else-if="pack.kind === 'competition'" :variant="pack.scene" />
      <svg v-else viewBox="0 0 460 230" fill="none" xmlns="http://www.w3.org/2000/svg" focusable="false"><g stroke="currentColor" stroke-width="2.5" stroke-linejoin="round"><rect x="82" y="58" width="234" height="136" rx="13" fill="currentColor" fill-opacity=".035" /><path d="m82 63 117 78L316 63M82 188l81-69m153 69-81-69m67-83 92-29-27 80-24-30-41-21Zm41 21 51-50" /><path d="M35 86h28m-40 18h40m-22 18h22" stroke-dasharray="4 6" /></g></svg>
    </div>
    <div class="drifting-item code-outline"><span>{{ pack.symbol }}</span><pre>{{ pack.example }}</pre></div>
  </div>
</template>
<script setup>
import {computed,ref} from 'vue'
import {usePersistentMotion} from '@/composables/usePersistentMotion'
import CodeIllustration from '@/components/CodeIllustration.vue'
import TopicArt from '@/components/TopicArt.vue'
import CompetitionSketch from '@/components/CompetitionSketch.vue'
import {getBackdropTheme} from '@/config/backdropThemes'
const props=defineProps({page:{type:String,default:'Home'},section:{type:Number,default:0},inverse:Boolean})
const pack=computed(()=>getBackdropTheme(props.page,props.section))
const backdrop=ref(null)
usePersistentMotion(backdrop,()=>`backdrop:${props.page}:${props.section}`)
</script>
<style scoped>
.drifting-backdrop { position: absolute; inset: 0; overflow: hidden; pointer-events: none; user-select: none; z-index: -1; color: #8f70b0; opacity: .15; }
.drifting-backdrop.inverse { color: #e8dcfa; }
.documents { color: #8b82ae; }.discussion,.mail { color: #7e9bb8; }.challenge,.assessment { color: #9392bc; }.ranking { color: #b49b69; }.rewards { color: #b68aab; }.calendar { color: #8a99be; }.teamwork { color: #7c9eaa; }.identity { color: #a48bae; }.debug { color: #aa86a0; }.analytics { color: #7b9caa; }
.drifting-item { position: absolute; left: 0; pointer-events: none; animation: backdrop-drift 52s linear infinite both; }
.big-statement { top: 12%; white-space: nowrap; font: 600 clamp(30px,4.5vw,74px)/1.4 Consolas,monospace; animation-duration: 62s; }
.background-motif { top: 43%; width: clamp(280px,37vw,500px); animation-duration: 57s; animation-direction: reverse; animation-delay: .35s; }
.background-motif > svg { display: block; width: 100%; height: auto; }
.background-motif :deep(.code-illustration),.background-motif :deep(.topic-art),.background-motif :deep(.competition-sketch) { color: inherit; width: 100%; height: auto; max-width: none; margin: 0; padding: 0; opacity: 1; justify-content: center; }
.background-motif :deep(.art-scene) { width: 100%; height: auto; max-height: none; }
.background-motif :deep(.art-trail),.background-motif :deep(.corner-companion) { display: none; }
.code-outline { bottom: 6%; display: flex; align-items: center; gap: 30px; animation-duration: 69s; animation-delay: .7s; white-space: nowrap; }
.code-outline > span { font: 200 clamp(90px,12vw,170px)/1 Consolas,monospace; }.code-outline pre { font: 500 clamp(20px,2.5vw,36px)/1.6 Consolas,monospace; margin: 0; background: none; border: 0; }
.motion-reverse .big-statement,.motion-reverse .code-outline { animation-direction: reverse; }.motion-reverse .background-motif { animation-direction: normal; }
.motion-diagonal .drifting-item { animation-name: backdrop-diagonal; }
.motion-rise .drifting-item { animation-name: backdrop-rise; }.motion-rise .background-motif { left: 30%; animation-direction: normal; }
.motion-shelves .drifting-item { animation-name: backdrop-shelves; }.motion-shelves .background-motif { animation-direction: normal; }
.motion-sway .drifting-item { animation-name: backdrop-sway; }
.motion-scan .drifting-item { animation-direction: alternate; animation-duration: 48s; }.motion-scan .background-motif { animation-direction: alternate-reverse; }
@keyframes backdrop-drift { 0% { transform: translate3d(-115%,-8px,0) rotate(-3deg); opacity: 0; } 8% { opacity: 1; } 90% { opacity: 1; } 100% { transform: translate3d(calc(100vw + 20%),16px,0) rotate(3deg); opacity: 0; } }
@keyframes backdrop-diagonal { 0% { transform: translate(-110%,95px) rotate(-4deg); opacity: 0; } 10%,88% { opacity: 1; } 100% { transform: translate(calc(100vw + 20%),-100px) rotate(3deg); opacity: 0; } }
@keyframes backdrop-rise { 0% { transform: translate(-20px,200px) rotate(-3deg); opacity: 0; } 15%,80% { opacity: 1; } 100% { transform: translate(35vw,-200px) rotate(3deg); opacity: 0; } }
@keyframes backdrop-shelves { 0% { transform: translate(-110%,0); opacity: 0; } 12%,85% { opacity: 1; } 50% { transform: translate(40vw,-20px); } 100% { transform: translate(110vw,0); opacity: 0; } }
@keyframes backdrop-sway { 0% { transform: translate(-110%,20px) rotate(-7deg); opacity: 0; } 10%,90% { opacity: 1; } 50% { transform: translate(40vw,-45px) rotate(5deg); } 100% { transform: translate(110vw,20px) rotate(-4deg); opacity: 0; } }
@media (max-width: 768px) { .drifting-backdrop { opacity: .1; }.big-statement { font-size: 30px; }.background-motif { width: 280px; }.code-outline { gap: 12px; }.code-outline > span { font-size: 90px; }.code-outline pre { font-size: 18px; } }
</style>
