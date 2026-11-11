import {nextTick,onMounted,onBeforeUnmount,watch} from 'vue'

// Keep animation progress for the current app session without caching entire pages.
const scenes=new Map()
let sessionStartedAt
const now=()=>performance.now()

function animations(root){
  if(!root || typeof root.getAnimations!=='function')return []
  const counts=new Map()
  return root.getAnimations({subtree:true}).flatMap(animation=>{
    if(typeof animation.animationName!=='string')return []
    let node=animation.effect?.target
    if(!(node instanceof Element)||!root.contains(node))return []
    const path=[]
    while(node!==root){
      path.unshift(Array.prototype.indexOf.call(node.parentElement.children,node))
      node=node.parentElement
    }
    const base=`${path.join('.')}:${animation.animationName}`
    const index=counts.get(base)||0
    counts.set(base,index+1)
    return [{animation,key:`${base}:${index}`}]
  })
}

export function usePersistentMotion(root,getSceneKey){
  let mounted=false
  function save(key){
    const positions=new Map()
    for(const {animation,key:animationKey} of animations(root.value)){
      if(typeof animation.currentTime==='number' && Number.isFinite(animation.currentTime))positions.set(animationKey,animation.currentTime)
    }
    if(positions.size)scenes.set(key,positions)
  }
  function restore(key){
    if(sessionStartedAt===undefined)sessionStartedAt=now()
    const elapsed=now()-sessionStartedAt
    const positions=scenes.get(key)
    for(const {animation,key:animationKey} of animations(root.value)){
      animation.currentTime=positions?.get(animationKey) ?? elapsed
    }
  }
  onMounted(()=>{mounted=true;restore(getSceneKey())})
  watch(getSceneKey,(key,previous)=>{
    if(!mounted)return
    save(previous)
    nextTick(()=>{if(mounted && getSceneKey()===key)restore(key)})
  },{flush:'pre'})
  onBeforeUnmount(()=>{save(getSceneKey());mounted=false})
}
