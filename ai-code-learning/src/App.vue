<template>
  <el-config-provider :message="{ duration: 1500 }">
  <div id="app" :class="{ 'teacher-mode': isTeacher }">
    <!-- 全局导航栏：所有页面都会显示，随时可点击跳转 -->
    <Navbar />
    <RouteFeedback :pending="routePending" :initial="!currentRoute.name" :error="routeError" @retry="retryRoute" @dismiss="routeError = ''" />
    <!-- 路由视图：所有页面的内容都在这里渲染 -->
    <div class="route-stage">
    <router-view v-slot="{ Component, route }">
      <Transition name="page" @before-enter="preparePageTurn" @before-leave="preparePageLeave">
        <div :key="route.name === 'AdminPanel' ? 'admin-panel' : route.path" class="page-view" :class="{'motion-enabled': motionEnabled(route.name)}">
          <div class="route-content"><ContentBoundary :reset-key="route.path"><component :is="Component" /></ContentBoundary></div>
          <ContentBoundary v-if="motionEnabled(route.name)" silent :reset-key="route.path"><PageMotion :page="String(route.name || '')" :teacher="isTeacher" /></ContentBoundary>
          <ContentBoundary v-if="motionEnabled(route.name)" silent :reset-key="route.path"><EdgeDecorations :page="String(route.name || '')" /></ContentBoundary>
          <ContentBoundary v-if="motionEnabled(route.name)" silent :reset-key="route.path"><CodeAtmosphere :key="route.path" :page="String(route.name || '')" /></ContentBoundary>
        </div>
      </Transition>
    </router-view>
    </div>
    <ClickSparkles />
    <Transition name="back-top">
      <button v-if="showBackTop" class="back-top-button" aria-label="返回顶部" @click="backToTop">↑</button>
    </Transition>
  </div>
  </el-config-provider>
</template>

<script setup>
import { computed, onBeforeUnmount, onMounted, ref } from 'vue'
import {useRoute,useRouter} from 'vue-router'
import {getPageTransition} from '@/utils/pageTransitions'
import {isSharedNavigation} from '@/utils/sharedMotion'
import ContentBoundary from './components/ContentBoundary.vue'
import RouteFeedback from './components/RouteFeedback.vue'
import {useRouteFeedback} from '@/composables/useRouteFeedback'
import {useAmbientMotion} from '@/composables/useAmbientMotion'
// 引入全局导航栏组件
import Navbar from './components/Navbar.vue'
import CodeAtmosphere from './components/CodeAtmosphere.vue'
import ClickSparkles from './components/ClickSparkles.vue'
import PageMotion from './components/PageMotion.vue'
import EdgeDecorations from './components/EdgeDecorations.vue'
import { getCurrentUser, migrateLegacyAuthToSession } from '@/utils/authStorage'

const currentRoute=useRoute()
const pageTravel=ref({mode:'turn',direction:1})
const stopPageTravel=useRouter().afterEach((to,from,failure)=>{
  if(!failure && to.path!==from.path)pageTravel.value=getPageTransition(to.name,from.name)
})
const {pending:routePending,error:routeError,retry:retryRoute}=useRouteFeedback()
const motionEnabled=name=>!['Learn','CodeJudge','CompetitionPlay','AdminPanel'].includes(name)
useAmbientMotion()

function preparePageTurn(element){
  element.dataset.pageMotion=isSharedNavigation() ? 'shared' : pageTravel.value.mode
  element.dataset.pageDirection=pageTravel.value.direction>0?'right':'left'
  element.style.setProperty('--page-sign',String(pageTravel.value.direction))
  element.style.setProperty('--page-pivot-y',`${window.scrollY+Math.min(window.innerHeight*.36,340)}px`)
}
function preparePageLeave(element){
  preparePageTurn(element)
  element.inert=true
}

const userRaw = ref(JSON.stringify(getCurrentUser() || {}))
const showBackTop = ref(false)
const updateScroll = () => { showBackTop.value = window.scrollY > 500 }
const backToTop = () => window.scrollTo({
  top: 0,
  behavior: 'smooth'
})
const isTeacher = computed(() => {
  try {
    return String(JSON.parse(userRaw.value || '{}')?.role || '') === 'teacher'
  } catch {
    return false
  }
})

const syncRole = () => {
  userRaw.value = JSON.stringify(getCurrentUser() || {})
}

onMounted(() => {
  migrateLegacyAuthToSession()
  syncRole()
  window.addEventListener('user-updated', syncRole)
  window.addEventListener('storage', syncRole)
  window.addEventListener('scroll', updateScroll, { passive: true })
  updateScroll()
})

onBeforeUnmount(() => {
  stopPageTravel()
  window.removeEventListener('user-updated', syncRole)
  window.removeEventListener('storage', syncRole)
  window.removeEventListener('scroll', updateScroll)
})
</script>

<style>
* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}
body {
  font-family: "Microsoft YaHei", sans-serif;
  background-color: #f5f7fa;
}
#app {
  min-height: 100vh;
}

/* 教师端全站统一背景（深紫渐变） */
#app.teacher-mode {
  background:
    radial-gradient(1200px 600px at 20% 0%, rgba(111, 66, 193, 0.26), transparent 60%),
    radial-gradient(900px 500px at 90% 10%, rgba(124, 58, 237, 0.22), transparent 60%),
    linear-gradient(135deg, #170f2f 0%, #241347 45%, #2f185d 100%);
}

/* 常见页面根容器：教师端时统一为深紫系背景，避免页面切换违和 */
#app.teacher-mode .home-page,
#app.teacher-mode .learning-page,
#app.teacher-mode .profile-page,
#app.teacher-mode .daily-page,
#app.teacher-mode .library-page,
#app.teacher-mode .forum-page,
#app.teacher-mode .class-page,
#app.teacher-mode .learn-container,
#app.teacher-mode .learning-center-page,
#app.teacher-mode .learning-center,
#app.teacher-mode .page-root {
  background: transparent !important;
}

/* 教师端常见卡片做轻微暗化透明，和深色背景更融合 */
#app.teacher-mode .content-card,
#app.teacher-mode .editor-section,
#app.teacher-mode .ai-section,
#app.teacher-mode .resource-library-container,
#app.teacher-mode .post-card,
#app.teacher-mode .register-form-wrapper,
#app.teacher-mode .login-form-wrapper {
  background: rgba(255, 255, 255, 0.92);
}
</style>
