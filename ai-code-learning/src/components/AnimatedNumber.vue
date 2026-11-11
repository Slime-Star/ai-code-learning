<template><span>{{ displayed }}</span></template>
<script setup>
import {ref,watch,onBeforeUnmount} from 'vue'
const props=defineProps({value:{type:Number,default:0},animate:Boolean})
const displayed=ref(0)
let frame=0
watch(()=>[props.value,props.animate],()=>{
  cancelAnimationFrame(frame)
  const target=Number.isFinite(props.value)?Math.max(0,Math.round(props.value)):0
  if(!props.animate || target===displayed.value){displayed.value=target;return}
  const from=displayed.value,start=performance.now()
  function update(time){
    const progress=Math.min(1,Math.max(0,(time-start)/700))
    displayed.value=Math.round(from+(target-from)*(1-Math.pow(1-progress,3)))
    if(progress<1)frame=requestAnimationFrame(update)
  }
  frame=requestAnimationFrame(update)
},{immediate:true})
onBeforeUnmount(()=>cancelAnimationFrame(frame))
</script>
