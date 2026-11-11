<template>
  <div ref="scene" class="test-flow-scene" aria-label="测试阶段快捷筛选">
    <div class="test-orbit" aria-hidden="true"><i></i></div>
    <svg class="test-circuit" viewBox="0 0 430 230" fill="none" aria-hidden="true"><path d="M70 137v37q0 12 12 12h73q12 0 12-12v-48m70 0v65q0 12 12 12h67q12 0 12-12v-40" /><path class="test-signal" d="M70 137v37q0 12 12 12h73q12 0 12-12v-48m70 0v65q0 12 12 12h67q12 0 12-12v-40" /></svg>
    <button v-for="(step,index) in steps" :key="step.id" class="test-flow-card" :class="[step.id,{selected:status===step.id}]" :style="{'--step':index}" :aria-pressed="status===step.id" @click="$emit('select',step.id)">
      <span class="flow-step">0{{ index+1 }}</span><span class="flow-symbol" aria-hidden="true"><template v-if="index===0">{ }</template><svg v-else-if="index===1" viewBox="0 0 70 70" fill="none"><circle cx="35" cy="38" r="23" /><path d="M35 15V8m-8 0h16" /><path class="flow-clock-hand" d="M35 38V23" /><circle cx="35" cy="38" r="2" fill="currentColor" /></svg><svg v-else viewBox="0 0 70 70" fill="none"><path d="M14 14h42v43H14zM22 26h22m-22 9h13m-13 9h8" /><path class="flow-check" d="m37 44 6 6 14-16" pathLength="1" /></svg></span><span class="flow-title">{{ step.title }}</span><span class="flow-desc">{{ step.desc }}</span>
    </button>
    <div class="flow-footer"><span>选择阶段，查看对应测试</span><button v-if="status!=='all'" @click="$emit('select','all')">全部 ↗</button></div>
  </div>
</template>
<script setup>
import {ref} from 'vue'
import {usePersistentMotion} from '@/composables/usePersistentMotion'
defineProps({status:{type:String,default:'all'}})
defineEmits(['select'])
const scene=ref(null)
const steps=[{id:'registering',title:'报名准备',desc:'选择你的挑战'},{id:'ongoing',title:'编程作答',desc:'把思路变成代码'},{id:'ended',title:'结果回顾',desc:'在复盘中进步'}]
usePersistentMotion(scene,()=> 'competition:test-flow')
</script>
<style scoped>
.test-flow-scene{position:relative;width:430px;max-width:100%;height:252px;perspective:1100px;isolation:isolate}.test-circuit{position:absolute;inset:0;width:100%;height:230px;stroke:#e6d4ff55;stroke-width:1.5}.test-signal{stroke:#eee5ff;stroke-dasharray:10 70;animation:test-signal 6s linear infinite}.test-orbit{position:absolute;width:240px;height:72px;left:19%;top:15px;border:1px solid #e4d4ff3b;border-radius:50%;rotate:-12deg;animation:test-orbit 14s ease-in-out infinite alternate}.test-orbit i{position:absolute;top:18px;right:7px;width:5px;height:5px;border-radius:50%;background:#dfcbfb;box-shadow:0 0 10px #dfcbfb77}
.test-flow-card{position:absolute;left:calc(var(--step)*30%);top:calc(55px - var(--step)*9px);width:32%;height:151px;display:flex;flex-direction:column;align-items:flex-start;border:1px solid #e9ddff88;border-radius:15px;padding:12px 15px;background:linear-gradient(140deg,#ffffffef,#e6daf9f0);color:#9274af;box-shadow:4px 7px 0 #a085c645,0 16px 27px #36234c2b;transform:rotateY(-16deg) rotateZ(-6deg);animation:test-card-float 7s ease-in-out infinite alternate;animation-delay:calc(var(--step)*-2s);cursor:pointer;font:inherit;transition:box-shadow 220ms,background 220ms}.test-flow-card.ongoing{top:30px;z-index:2;transform:translateZ(26px) rotateZ(3deg)}.test-flow-card.ended{transform:rotateY(12deg) rotateZ(7deg)}.flow-step{font:8px Consolas,monospace;opacity:.6}.flow-symbol{display:grid;place-items:center;width:50px;height:54px;font:27px Consolas,monospace;color:#a48ac1;margin:4px 0 6px}.flow-symbol svg{width:53px;height:53px;stroke:currentColor;stroke-width:1.5;stroke-linecap:round;stroke-linejoin:round}.flow-clock-hand{transform-origin:35px 38px;animation:flow-clock 18s linear infinite}.flow-check{stroke-dasharray:1;animation:flow-check 5s ease-in-out infinite}.flow-title{font-size:12px;color:#87669f;white-space:nowrap}.flow-desc{font-size:9px;color:#ad96bf;margin-top:7px;white-space:nowrap}.selected,.test-flow-card:hover,.test-flow-card:focus-visible{background:linear-gradient(140deg,#fff,#e7d4ff);box-shadow:4px 7px 0 #ae8bd670,0 18px 30px #38214e44;z-index:4}.selected .flow-title{color:#774d9a}.flow-footer{position:absolute;bottom:5px;left:8%;right:8%;display:flex;align-items:center;justify-content:space-between;font-size:10px;color:#e9dffbb0}.flow-footer button{border:0;background:none;color:#f2eaff;padding:5px;font:inherit;cursor:pointer}
@keyframes test-card-float{to{translate:0 -9px}}@keyframes test-signal{to{stroke-dashoffset:-160}}@keyframes test-orbit{to{rotate:-3deg;translate:0 -6px}}@keyframes flow-clock{to{rotate:360deg}}@keyframes flow-check{0%,15%{stroke-dashoffset:1}55%,85%{stroke-dashoffset:0}100%{stroke-dashoffset:1}}
@media(max-width:640px){.test-flow-scene{width:350px;height:235px}.test-flow-card{padding:11px;height:145px}.flow-title{font-size:11px}.flow-desc{font-size:8px}.flow-footer{font-size:9px}}
</style>
