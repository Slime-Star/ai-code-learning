<template>
  <Teleport to="body"><div v-if="active && reward" class="signin-reward-flight" aria-hidden="true"><i v-for="n in 9" :key="`${reward.id}-${n}`" class="reward-code-particle" :class="{'particle-outline': n%3===0}" :style="particleStyle(n)">{{ n%3===0 ? '+' : '' }}</i><span class="reward-arrival" :style="{left:`${reward.to.x}px`,top:`${reward.to.y}px`}">+{{ reward.amount }}</span></div></Teleport>
</template>
<script setup>
import {ref,watch,onBeforeUnmount} from 'vue'
const props=defineProps({reward:{type:Object,default:null}})
const emit=defineEmits(['finished'])
const active=ref(false)
let timer
watch(()=>props.reward?.id,id=>{
  clearTimeout(timer)
  active.value=!!id && Number.isFinite(props.reward.amount) && props.reward.amount>0
  if(active.value)timer=setTimeout(()=>{active.value=false;emit('finished',id)},1700)
},{immediate:true})
function particleStyle(index){
  const {from,to}=props.reward
  const dx=to.x-from.x,dy=to.y-from.y
  return {left:`${from.x}px`,top:`${from.y}px`,'--dx':`${dx}px`,'--dy':`${dy}px`,'--mx':`${dx*.45+(index-5)*7}px`,'--my':`${dy*.45-42-index*4}px`,'--delay':`${index*35}ms`}
}
onBeforeUnmount(()=>clearTimeout(timer))
</script>
<style scoped>
.signin-reward-flight{position:fixed;inset:0;z-index:2100;pointer-events:none;user-select:none}.reward-code-particle{position:absolute;display:grid;place-items:center;width:7px;height:7px;border-radius:2px;background:#c4a1eb;box-shadow:0 0 9px #b38bd977;animation:reward-travel 850ms cubic-bezier(.25,.65,.35,1) var(--delay) both;color:#b698d0;font:15px Consolas,monospace;font-style:normal}.particle-outline{width:13px;height:13px;background:transparent;box-shadow:none}.reward-arrival{position:absolute;padding:4px 9px;border-radius:12px;background:#f3eafa;color:#9268b4;font:600 15px Consolas,monospace;animation:reward-arrive 1s ease-out 550ms both;box-shadow:0 3px 14px #9c76b62b}
@keyframes reward-travel{0%{translate:0 0;scale:.4;opacity:0}12%{opacity:1;scale:1}52%{translate:var(--mx) var(--my);opacity:1;rotate:90deg}100%{translate:var(--dx) var(--dy);scale:.2;opacity:0;rotate:180deg}}@keyframes reward-arrive{0%{translate:-50% 0;scale:.7;opacity:0}24%{opacity:1;scale:1}75%{opacity:1}100%{translate:-50% -30px;opacity:0;scale:.96}}
</style>
