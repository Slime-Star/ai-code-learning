<template>
  <div ref="shelf" class="resource-shelf" aria-label="立体资源分类架">
    <div class="shelf-grid" aria-hidden="true"></div><div class="shelf-base" aria-hidden="true"></div>
    <button v-for="(file,index) in files" :key="file.id" class="shelf-file" :class="{chosen:Number(category)===file.id}" :style="{'--file-index':index}" :aria-pressed="Number(category)===file.id" :aria-label="`筛选${file.label}`" @click="$emit('select',file.id)">
      <span class="file-tab" aria-hidden="true"></span><span class="file-format">{{ file.format }}</span><span class="file-icon" aria-hidden="true">{{ file.symbol }}</span><span class="file-lines" aria-hidden="true"><i></i><i></i><i></i></span><span class="file-label">{{ file.label }} <b aria-hidden="true">↗</b></span>
    </button>
    <span class="shelf-note" aria-hidden="true">DOCS · TOOLS · SOURCE</span>
  </div>
</template>
<script setup>
import {ref} from 'vue'
import {usePersistentMotion} from '@/composables/usePersistentMotion'
defineProps({category:{type:[String,Number],default:''}})
defineEmits(['select'])
const shelf=ref(null)
const files=[{id:2,label:'学习资料',format:'.md',symbol:'≡'},{id:1,label:'开发工具',format:'.exe',symbol:'⌘'},{id:3,label:'源码案例',format:'.js',symbol:'</>'}]
usePersistentMotion(shelf,()=> 'library:resource-shelf')
</script>
<style scoped>
.resource-shelf{position:relative;width:410px;max-width:100%;height:236px;perspective:950px;color:#f1e8ff;isolation:isolate}.shelf-grid{position:absolute;inset:28px 0 30px;background-image:radial-gradient(#e6d4fc55 1px,transparent 1px);background-size:19px 19px;mask-image:radial-gradient(ellipse,#000,transparent 70%);animation:shelf-grid 16s linear infinite}.shelf-base{position:absolute;bottom:29px;left:10px;right:4px;height:83px;border:1px solid #e5d4fb66;border-radius:14px;transform:rotateX(58deg) rotateZ(-5deg);background:linear-gradient(135deg,#f2e8ff26,#d5baff09);box-shadow:0 7px 0 #e0c9f722,0 20px 35px #30234b22}
.shelf-file{position:absolute;left:calc(12px + var(--file-index)*27%);top:calc(36px - var(--file-index)*10px);width:35%;height:158px;display:flex;flex-direction:column;text-align:left;padding:13px 14px 10px;border:1px solid #fffc;border-radius:11px;background:linear-gradient(140deg,#fff,#e6dcf9);color:#8a70aa;box-shadow:6px 7px 0 #9e80c455,0 15px 24px #33244726;transform:rotateY(-18deg) rotateZ(-8deg);animation:shelf-bob 6s ease-in-out infinite alternate;animation-delay:calc(var(--file-index)*-1.6s);cursor:pointer;transition:background 220ms,box-shadow 220ms;transform-style:preserve-3d;font:inherit}.file-tab{position:absolute;top:-8px;left:11px;width:38px;height:9px;border:1px solid #eee3ff;border-bottom:0;border-radius:5px 5px 0 0;background:#dfd0f2}.file-format{font:9px Consolas,monospace;letter-spacing:1px;opacity:.65}.file-icon{display:block;margin:12px 0 10px;font:27px Consolas,monospace;color:#a088bf;transition:color 220ms}.file-lines{display:grid;gap:5px}.file-lines i{display:block;height:3px;width:85%;background:#cab8df66;border-radius:4px}.file-lines i:nth-child(2){width:65%}.file-lines i:last-child{width:43%}.file-label{margin-top:auto;display:flex;justify-content:space-between;gap:5px;font-size:11px;white-space:nowrap}.file-label b{font-weight:400;color:#ad94c5}.shelf-file:hover,.shelf-file:focus-visible,.shelf-file.chosen{background:linear-gradient(140deg,#fff,#ead9ff);box-shadow:6px 7px 0 #ab8ad56b,0 18px 35px #2a1b5240;z-index:3}.shelf-file:hover .file-icon,.chosen .file-icon{color:#8860b4}.chosen .file-label{color:#8253aa}.shelf-note{position:absolute;bottom:7px;left:45px;font:8px Consolas,monospace;letter-spacing:2.4px;color:#e3d2f7a6}
@keyframes shelf-bob{to{translate:0 -11px;rotate:3deg}}@keyframes shelf-grid{to{background-position:19px -19px}}
@media(max-width:640px){.resource-shelf{width:350px;height:220px;margin:auto}.shelf-file{height:149px;padding:12px 10px}.file-label{font-size:10px}.shelf-note{left:27px;font-size:7px}}
</style>
