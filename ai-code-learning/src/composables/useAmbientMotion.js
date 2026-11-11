import {onMounted,onBeforeUnmount} from 'vue'

const selector='.drifting-backdrop, .header-motion, .topic-art, .code-illustration, .competition-sketch, .code-landscape, .animated-companion, .learning-carousel, .programming-workbench, .knowledge-map, .resource-shelf, .test-flow-scene, .podium-light, .edge-footer, .edge-rail, .floating-code, .ambient-orb, .ambient-circuit, .ambient-dot, .ambient-grid, .ambient-sweep, .nav-decoration-layer, .code-ticker'

export function useAmbientMotion(){
  const scenes=new Map()
  let observer,mutations
  function apply(el,visible){
    const paused=document.hidden || !visible
    el.classList.toggle('ambient-paused',paused)
    for(const svg of el.matches('svg')?[el]:el.querySelectorAll('svg')){
      try{paused?svg.pauseAnimations?.():svg.unpauseAnimations?.()}catch{/* SVG animation controls vary by browser. */}
    }
  }
  function register(el){
    if(scenes.has(el)||el.parentElement?.closest(selector))return
    scenes.set(el,true)
    observer?.observe(el)
    apply(el,true)
  }
  function scan(node){
    if(!(node instanceof Element))return
    if(node.matches(selector))register(node)
    node.querySelectorAll(selector).forEach(register)
  }
  function visibility(){for(const [el,visible] of scenes)apply(el,visible)}
  onMounted(()=>{
    if(typeof IntersectionObserver!=='undefined')observer=new IntersectionObserver(entries=>{
      for(const entry of entries){
        if(!entry.target.isConnected)continue
        scenes.set(entry.target,entry.isIntersecting);apply(entry.target,entry.isIntersecting)
      }
    },{rootMargin:'160px',threshold:0})
    scan(document.getElementById('app'))
    mutations=new MutationObserver(records=>{
      for(const record of records)for(const node of record.addedNodes)scan(node)
      for(const el of scenes.keys())if(!el.isConnected){observer?.unobserve(el);scenes.delete(el)}
    })
    mutations.observe(document.getElementById('app'),{childList:true,subtree:true})
    document.addEventListener('visibilitychange',visibility)
  })
  onBeforeUnmount(()=>{
    observer?.disconnect();mutations?.disconnect()
    document.removeEventListener('visibilitychange',visibility)
    for(const el of scenes.keys()){el.classList.remove('ambient-paused');for(const svg of el.querySelectorAll('svg'))try{svg.unpauseAnimations?.()}catch{}}
    scenes.clear()
  })
}
