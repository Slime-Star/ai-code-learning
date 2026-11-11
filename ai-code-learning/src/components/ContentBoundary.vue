<template>
  <slot v-if="!failed" :key="attempt" />
  <section v-else-if="!silent" class="content-error" role="alert">
    <span class="error-symbol" aria-hidden="true">&lt;/&gt;</span>
    <h2>这一页暂时没有打开</h2>
    <p>请重试一次，你也可以先去其他页面继续浏览。</p>
    <div><el-button type="primary" @click="retry">重新尝试</el-button><el-button @click="reload">刷新页面</el-button></div>
  </section>
</template>
<script setup>
import {onErrorCaptured,ref,watch} from 'vue'
const props=defineProps({silent:Boolean,resetKey:{type:String,default:''}})
const failed=ref(false),attempt=ref(0)
function retry(){attempt.value++;failed.value=false}
function reload(){window.location.reload()}
// A new route only resets a failed boundary. Remounting a healthy slot here
// destroys stateful layouts such as the admin sidebar on every module click.
watch(()=>props.resetKey,()=>{if(failed.value)retry()})
onErrorCaptured((error,instance,info)=>{
  console.error(props.silent?'装饰组件加载失败':'页面内容加载失败',error,info)
  failed.value=true
  return false
})
</script>
<style scoped>
.content-error { max-width: 720px; margin: 48px auto; padding: 48px 24px; text-align: center; color: #64577b; border: 1px solid #e4daef; border-radius: 20px; background: #fff; }
.error-symbol { font: 44px Consolas,monospace; color: #b19bcf; }h2 { margin: 18px 0 12px; font-size: 23px; }p { line-height: 1.8; margin-bottom: 24px; color: #81778f; }
@media(max-width:640px){.content-error{margin:24px 16px;padding:32px 18px}h2{font-size:20px}}
</style>
