<template>
  <div ref="overlay" class="page-motion-overlay">
    <Teleport v-if="enabled && headerHost" :to="headerHost"><HeaderMotion :page="page" :teacher="teacher" /></Teleport>
    <Teleport v-for="(host,index) in backdropHosts" :key="`${page}-${index}`" :to="host"><DriftingBackdrop :page="page" :section="index" :inverse="teacher || index === 0 && ['Home','Library'].includes(page)" /></Teleport>
    <template v-if="enabled">
      <div class="reading-progress" aria-hidden="true"><span :style="{transform:`scaleX(${progress})`}"></span></div>
      <div class="pointer-glow" aria-hidden="true"></div>
    </template>
  </div>
</template>

<script setup>
import {ref,shallowRef,onMounted,onBeforeUnmount} from 'vue'
import HeaderMotion from '@/components/HeaderMotion.vue'
import DriftingBackdrop from '@/components/DriftingBackdrop.vue'
import {isSharedNavigation} from '@/utils/sharedMotion'
const props=defineProps({enabled:{type:Boolean,default:true},page:{type:String,default:''},teacher:Boolean})
const headerHost=ref(null)
const backdropHosts=shallowRef([])
const overlay=ref(null),surface=shallowRef(null),progress=ref(0)
const selector='.banner-top, .hero, .main-header, .continue-card, .banner-panel, .path-card, .course-card, .content-card, .post-create, .post-card, .profile-card, .practice-card, .goods-card, .competition-card, .info-card, .teacher-page > .header, .teacher-page .card, .whitespace-game, .learning-interlude, .study-toolkit, .learning-art-finale, .page-title, .forum-game-side, .category-header, .class-page > .header, .list-card'
const registered=new WeakSet(),playing=new Map()
const hoverSelector='.path-card, .course-card, .profile-card, .practice-card, .exercise-card, .favorite-course, .goods-card, .competition-card, .post-card'
let hoverCard=null
let intersections,mutations,resizeObserver,scrollFrame=0,pointerFrame=0
function reveal(entries){
  let sequence=0
  for(const entry of entries){
    if(!entry.isIntersecting)continue
    intersections.unobserve(entry.target)
    const el=entry.target
    if(isSharedNavigation() || typeof el.animate!=='function'||el.contains(document.activeElement))continue
    const animation=el.animate([
      {opacity:0,translate:'0 32px',scale:'.985'},
      {opacity:1,translate:'0 0',scale:'1'}
    ],{duration:650,delay:Math.min(sequence++*65,260),easing:'cubic-bezier(.16,1,.3,1)',fill:'backwards'})
    playing.set(el,animation)
    const forget=()=>{if(playing.get(el)===animation)playing.delete(el)}
    animation.onfinish=forget;animation.oncancel=forget
  }
}
function register(el){
  if(registered.has(el)||el.parentElement?.closest(selector))return
  registered.add(el);intersections.observe(el)
}
function scan(node){
  if(!(node instanceof Element)||node.closest('.ace_editor, .monaco-editor, .micro-board, .mini-board, .message-content'))return
  if(node.matches(selector))register(node)
  node.querySelectorAll(selector).forEach(register)
}
function resetHover(){
  if(!hoverCard)return
  hoverCard.classList.remove('motion-hover-active')
  for(const key of ['--card-x','--card-y','--tilt-x','--tilt-y','--layer-x','--layer-y'])hoverCard.style.removeProperty(key)
  hoverCard=null
}
function onFocus(event){for(const [el,animation] of playing)if(el.contains(event.target))animation.cancel();resetHover()}
function updateProgress(){
  scrollFrame=0
  const length=document.documentElement.scrollHeight-window.innerHeight
  progress.value=length>0?Math.min(1,Math.max(0,window.scrollY/length)):0
}
function scheduleProgress(){if(!scrollFrame)scrollFrame=requestAnimationFrame(updateProgress)}
function movePointer(event){
  if(!props.enabled||event.pointerType!=='mouse'||pointerFrame)return
  const x=event.clientX,y=event.clientY
  const target=event.target
  pointerFrame=requestAnimationFrame(()=>{
    pointerFrame=0
    surface.value?.style.setProperty('--pointer-x',`${x}px`)
    surface.value?.style.setProperty('--pointer-y',`${y}px`)
    surface.value?.classList.add('pointer-active')
    const card=target instanceof Element?target.closest(hoverSelector):null
    if(!card||!surface.value?.contains(card)||card.contains(document.activeElement)||target.closest('input, textarea, select, [contenteditable="true"]')){resetHover();return}
    if(card!==hoverCard){resetHover();hoverCard=card;card.classList.add('motion-hover-card','motion-hover-active')}
    const bounds=card.getBoundingClientRect()
    if(!bounds.width||!bounds.height)return
    const px=Math.max(0,Math.min(1,(x-bounds.left)/bounds.width)),py=Math.max(0,Math.min(1,(y-bounds.top)/bounds.height))
    card.style.setProperty('--card-x',`${px*100}%`);card.style.setProperty('--card-y',`${py*100}%`)
    card.style.setProperty('--layer-x',`${(px-.5)*8}px`);card.style.setProperty('--layer-y',`${(py-.5)*6}px`)
    card.style.setProperty('--tilt-x',`${(0.5-py)*5}deg`);card.style.setProperty('--tilt-y',`${(px-0.5)*5}deg`)
  })
}
function leavePointer(){cancelAnimationFrame(pointerFrame);pointerFrame=0;surface.value?.classList.remove('pointer-active');resetHover()}
onMounted(()=>{
  if(!props.enabled)return
  surface.value=overlay.value.parentElement
  const root=surface.value.querySelector('.route-content')?.firstElementChild
  if(root){
    backdropHosts.value=[root,...root.querySelectorAll('.learning-path, .course-category')]
    backdropHosts.value.forEach(host=>host.classList.add('motion-scene-host'))
  }
  const hosts={Home:'.main-header',LearningCenter:'.banner-top',Library:'.page-container',Competition:'.hero-banner',Leaderboard:'.hero',DailyCheckIn:'.hero',PointsMall:'.banner',Forum:'.forum-intro',Profile:'.profile-header',Login:'.login-banner',Register:'.register-banner'}
  headerHost.value=root?.querySelector(hosts[props.page] || '.hero, .header') || root
  headerHost.value?.classList.add('motion-header-host')
  if(typeof IntersectionObserver!=='undefined'){
    intersections=new IntersectionObserver(reveal,{threshold:.06,rootMargin:'0px 0px -24px 0px'})
    scan(surface.value)
    mutations=new MutationObserver(records=>{
      for(const record of records){
        for(const node of record.addedNodes)scan(node)
        for(const node of record.removedNodes)if(node instanceof Element){
          intersections.unobserve(node)
          node.querySelectorAll(selector).forEach(el=>intersections.unobserve(el))
          for(const [el,animation] of playing)if(node===el||node.contains(el))animation.cancel()
        }
      }
    })
    mutations.observe(surface.value,{childList:true,subtree:true})
  }
  surface.value.addEventListener('focusin',onFocus)
  surface.value.addEventListener('pointermove',movePointer)
  surface.value.addEventListener('pointerleave',leavePointer)
  window.addEventListener('scroll',scheduleProgress,{passive:true})
  window.addEventListener('resize',scheduleProgress,{passive:true})
  if(typeof ResizeObserver!=='undefined'){resizeObserver=new ResizeObserver(scheduleProgress);resizeObserver.observe(surface.value)}
  updateProgress()
})
onBeforeUnmount(()=>{
  backdropHosts.value.forEach(host=>host.classList.remove('motion-scene-host'))
  headerHost.value?.classList.remove('motion-header-host')
  resetHover()
  intersections?.disconnect();mutations?.disconnect();resizeObserver?.disconnect()
  playing.forEach(animation=>animation.cancel());playing.clear()
  surface.value?.removeEventListener('focusin',onFocus)
  surface.value?.removeEventListener('pointermove',movePointer)
  surface.value?.removeEventListener('pointerleave',leavePointer)
  window.removeEventListener('scroll',scheduleProgress);window.removeEventListener('resize',scheduleProgress)
  cancelAnimationFrame(scrollFrame);cancelAnimationFrame(pointerFrame)
})
</script>

<style scoped>
.page-motion-overlay { position: absolute; inset: 0; pointer-events: none; }
.reading-progress { position: fixed; left: 0; right: 0; top: 0; height: 3px; z-index: 1100; pointer-events: none; }
.reading-progress span { display: block; width: 100%; height: 100%; transform-origin: left; background: linear-gradient(90deg,#a9afff,#d1a2ef,#93d5e2); box-shadow: 0 0 9px #b49ddc75; transition: transform 100ms linear; }
.pointer-glow { position: fixed; left: var(--pointer-x, -500px); top: var(--pointer-y, -500px); width: 260px; height: 260px; border-radius: 50%; transform: translate(-50%,-50%); background: radial-gradient(circle,#baa0f21f,transparent 70%); pointer-events: none; z-index: 3; opacity: 0; transition: opacity 250ms; }
.pointer-active .pointer-glow { opacity: 1; }
@media (hover: none) { .pointer-glow { display: none; } }
</style>
