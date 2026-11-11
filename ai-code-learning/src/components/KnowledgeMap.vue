<template>
  <section ref="map" class="knowledge-map" aria-label="学习方向知识星图" @pointerleave="preview = ''">
    <div class="map-intro"><span class="map-eyebrow">CONNECT YOUR KNOWLEDGE</span><h3>把知识，连成你的路线</h3><p>{{ activeTitle ? '已点亮「' + activeTitle + '」路线，下方课程已同步筛选。' : '点亮一个方向，看看知识如何一步步相连。' }}</p><button v-if="activeTitle" class="map-browse" @click="$emit('browse')">查看对应课程 <span aria-hidden="true">→</span></button><span v-else class="map-hint">点击节点选择 · 悬停预览</span></div>
    <div class="map-network">
      <svg viewBox="0 0 900 240" preserveAspectRatio="none" fill="none" aria-hidden="true"><g v-for="(path,index) in paths" :key="path.id" :class="{'branch-lit': litTitle === path.title}" class="map-branch"><path :d="connection(index)" class="branch-base" /><path :d="connection(index)" class="branch-flow" pathLength="1" /><circle :cx="685" :cy="row(index)" r="3" /><circle :cx="816" :cy="row(index)" r="2.5" /></g></svg>
      <div class="map-origin" aria-hidden="true"><span>&lt;/&gt;</span><small>编程基础</small><i></i></div>
      <div v-for="(path,index) in paths" :key="path.id" class="map-route" :class="{lit:litTitle === path.title,selected:activeTitle === path.title}" :style="{'--row':`${row(index)/240*100}%`}">
        <button class="map-node" :aria-pressed="activeTitle === path.title" @pointerenter="preview = path.title" @focus="preview = path.title" @blur="preview = ''" @click="$emit('select',path)"><span class="node-dot" aria-hidden="true"></span><span>{{ path.title }}</span><span class="node-arrow" aria-hidden="true">↗</span></button>
        <div class="map-skills" aria-hidden="true"><span>{{ skills[index]?.[0] || path.category }}</span><i></i><span>{{ skills[index]?.[1] || '实战项目' }}</span></div>
      </div>
    </div>
  </section>
</template>
<script setup>
import {computed,ref} from 'vue'
import {usePersistentMotion} from '@/composables/usePersistentMotion'
const props=defineProps({paths:{type:Array,default:()=>[]},activeTitle:{type:String,default:''}})
defineEmits(['select','browse'])
const map=ref(null),preview=ref('')
const litTitle=computed(()=>preview.value || props.activeTitle)
const skills=[['HTML / JavaScript','Vue / React'],['Python / Web','数据 / AI'],['Java / Spring','服务 / 实战'],['数据结构','算法 / 实战']]
const row=index=>30+index*60
const connection=index=>`M80 120 C175 120 180 ${row(index)} 300 ${row(index)} H816`
usePersistentMotion(map,()=> 'learning:knowledge-map')
</script>
<style scoped>
.knowledge-map{display:grid;grid-template-columns:230px minmax(0,1fr);align-items:center;gap:24px;margin:0 0 30px;padding:22px 24px;border:1px solid #e8def0;border-radius:18px;background:linear-gradient(115deg,#f7f3fc,#fafbfe);color:#8c77ab;text-align:left;isolation:isolate}.map-intro{min-width:0}.map-eyebrow{font:8px Consolas,monospace;letter-spacing:1.7px;color:#ae9cbe}.map-intro h3{font-size:18px;font-weight:500;color:#78628f;margin:12px 0 10px}.map-intro p{font-size:12px;line-height:1.9;min-height:46px;color:#a08faf;margin:0 0 12px}.map-hint{font-size:10px;color:#b3a5be}.map-browse{display:inline-flex;align-items:center;gap:12px;border:0;background:none;padding:5px 0;color:#9373b3;font:inherit;font-size:12px;cursor:pointer}.map-browse:hover span{translate:4px 0}.map-browse span{transition:translate 180ms}
.map-network{position:relative;height:228px;min-width:0}.map-network>svg{position:absolute;inset:0;width:100%;height:100%;overflow:visible}.branch-base{stroke:#d9cce5;stroke-width:1.2;transition:stroke 220ms}.branch-flow{stroke:#ac8acb;stroke-width:2;stroke-dasharray:.035 .14;opacity:.2;animation:knowledge-flow 7s linear infinite;transition:opacity 220ms}.map-branch circle{fill:#dfd0ed;transition:fill 220ms}.branch-lit .branch-base{stroke:#af8bca}.branch-lit .branch-flow{opacity:1;stroke:#9267b6;animation-duration:3.8s}.branch-lit circle{fill:#a479c6}
.map-origin{position:absolute;left:8.9%;top:50%;width:52px;translate:-50% -50%;text-align:center}.map-origin>span{position:relative;z-index:1;display:grid;place-items:center;width:50px;height:50px;border:1px solid #d4c2e5;border-radius:16px;background:#f2eaf8;box-shadow:0 6px 15px #a086bc13;font:19px Consolas,monospace;rotate:-8deg;animation:knowledge-core 6s ease-in-out infinite alternate}.map-origin small{position:absolute;top:62px;left:-12px;width:76px;white-space:nowrap;font-size:10px;color:#b09bc0}.map-origin>i{position:absolute;inset:-12px;border:1px dashed #d3c2e46b;border-radius:50%;animation:knowledge-orbit 28s linear infinite}
.map-route{position:absolute;inset:var(--row) 0 auto;height:0}.map-node{position:absolute;top:0;left:33.33%;translate:-10px -50%;display:flex;align-items:center;gap:9px;min-width:153px;min-height:35px;padding:7px 10px;border:1px solid #e3d9ed;border-radius:10px;background:#faf8fd;color:#9a85ad;font:inherit;font-size:11px;cursor:pointer;transition:background 220ms,border-color 220ms,box-shadow 220ms,transform 220ms}.node-dot{width:5px;height:5px;border-radius:50%;background:#c3add6;box-shadow:0 0 0 4px #e7dbf055;flex-shrink:0}.node-arrow{margin-left:auto;font-size:12px;opacity:.4}.lit .map-node{border-color:#bb9ed2;background:#f0e7f8;color:#855fa5;box-shadow:0 5px 15px #9a77ba18;transform:translateY(-2px)}.lit .node-dot{background:#9c76bd;animation:knowledge-node 2.6s ease-in-out infinite}.selected .map-node{border-color:#ad8bc8}.selected .node-arrow{opacity:1}.map-skills{position:absolute;left:65%;right:4%;top:0;translate:0 -50%;display:flex;align-items:center;justify-content:space-between;gap:8px;color:#b6a4c5;font:9px Consolas,monospace;white-space:nowrap;pointer-events:none}.map-skills>span{padding:5px 7px;background:#f8f4fc;border-radius:6px}.map-skills>i{width:3px;height:3px;background:#d7c6e4;border-radius:50%;flex-shrink:0}.lit .map-skills{color:#9a78b7}
@keyframes knowledge-flow{to{stroke-dashoffset:-1}}@keyframes knowledge-core{to{translate:0 -5px;rotate:-2deg}}@keyframes knowledge-orbit{to{rotate:360deg}}@keyframes knowledge-node{50%{box-shadow:0 0 0 6px #cfb7e32b}}
@media(max-width:1100px){.knowledge-map{grid-template-columns:190px minmax(0,1fr);gap:12px;padding:20px}.map-node{min-width:140px;left:30%}.map-skills{left:70%;right:0;font-size:8px}.map-skills span:last-child,.map-skills>i{display:none}.map-intro h3{font-size:16px}}
@media(max-width:700px){.knowledge-map{grid-template-columns:minmax(0,1fr);gap:8px;padding:20px 14px;margin-bottom:24px}.map-intro{padding:0 6px}.map-intro p{min-height:0;margin-bottom:5px}.map-intro h3{margin:8px 0}.map-network{height:220px}.map-node{left:32%;min-width:145px;font-size:11px}.map-skills{left:78%;font-size:8px}.map-skills>span{padding:4px}.map-origin{left:9%;scale:.85}}
@media(max-width:390px){.map-skills{display:none}.map-node{left:40%;min-width:150px}}
</style>
