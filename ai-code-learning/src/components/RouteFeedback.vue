<template>
  <div v-if="pending" class="route-loading" role="status" aria-live="polite"><span class="route-loading-track"></span><span class="route-loading-label">正在打开页面…</span></div>
  <section v-if="pending && initial" class="route-skeleton" aria-label="页面正在加载" aria-busy="true"><div class="skeleton-hero"></div><div class="skeleton-cards"><i v-for="n in 3" :key="n"></i></div></section>
  <div v-if="error" class="route-error" role="alert"><span>{{ error }}</span><el-button size="small" type="primary" @click="$emit('retry')">重新打开</el-button><el-button size="small" text @click="$emit('dismiss')">关闭</el-button></div>
</template>
<script setup>
defineProps({pending:Boolean,initial:Boolean,error:{type:String,default:''}})
defineEmits(['retry','dismiss'])
</script>
<style scoped>
.route-loading{position:fixed;inset:60px 0 auto;z-index:1002;pointer-events:none}.route-loading-track{display:block;height:3px;background:linear-gradient(90deg,#a5a8ff,#d0b0f1,#a1d7ec);animation:route-loading 1.4s ease-in-out infinite;transform-origin:left}.route-loading-label{position:absolute;top:14px;left:50%;transform:translateX(-50%);padding:9px 18px;border:1px solid #e5daf2;border-radius:24px;background:#ffffffed;color:#76638e;font-size:12px;box-shadow:0 5px 20px #73528d15}
.route-error{position:fixed;top:78px;left:50%;transform:translateX(-50%);z-index:1010;display:flex;align-items:center;gap:12px;width:max-content;max-width:calc(100vw - 32px);padding:14px 18px;background:#fff;border:1px solid #e1d3ed;border-radius:12px;box-shadow:0 8px 36px #65507825;color:#6a587e;font-size:13px}
.route-skeleton{padding:36px 24px;max-width:1280px;margin:auto}.skeleton-hero,.skeleton-cards i{display:block;border-radius:18px;background:linear-gradient(110deg,#eae5f1 25%,#f8f5fc 45%,#eae5f1 65%);background-size:250% 100%;animation:skeleton-shimmer 1.8s linear infinite}.skeleton-hero{height:220px}.skeleton-cards{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:24px;margin-top:24px}.skeleton-cards i{height:180px}
@keyframes route-loading{0%{transform:translateX(-30%) scaleX(.2)}75%{transform:translateX(35%) scaleX(.65)}100%{transform:translateX(100%) scaleX(.2)}}@keyframes skeleton-shimmer{to{background-position:-150% 0}}
@media(max-width:640px){.route-error{flex-wrap:wrap}.route-error>span{width:100%}.skeleton-cards{grid-template-columns:1fr}.skeleton-cards i:not(:first-child){display:none}}
</style>
