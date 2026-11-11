<template>
  <!-- 桌面导航与移动端抽屉共用角色和登录状态 -->
  <div class="top-nav-container" :class="{ 'teacher-theme': isTeacher, 'admin-theme': isAdmin }">
    <div class="nav-decoration-layer" aria-hidden="true">
      <span class="nav-code-glyph glyph-one">{ }</span><span class="nav-code-glyph glyph-two">&lt;/&gt;</span><span class="nav-code-glyph glyph-three">01</span><span class="nav-code-glyph glyph-four">[ ]</span>
      <svg class="nav-data-track" viewBox="0 0 1200 16" preserveAspectRatio="none" fill="none" focusable="false"><path d="M0 9h180l12-5h140l12 5h250l12-5h190l12 5h392" stroke="currentColor" stroke-opacity=".18" stroke-width="1" /><circle r="2" fill="currentColor" opacity=".65"><animateMotion path="M0 9h180l12-5h140l12 5h250l12-5h190l12 5h392" dur="20s" repeatCount="indefinite" /></circle><circle r="1.5" fill="currentColor" opacity=".4"><animateMotion path="M0 9h180l12-5h140l12 5h250l12-5h190l12 5h392" dur="26s" begin="-13s" repeatCount="indefinite" /></circle></svg>
      <span class="nav-orbit"><i></i></span>
    </div>
    <div ref="navWrapper" class="nav-wrapper">
      <span v-show="selectionVisible" class="nav-selection" :style="selectionStyle" aria-hidden="true"></span>
      <button ref="menuToggle" class="mobile-menu-toggle" aria-label="打开导航菜单" :aria-expanded="mobileMenuOpen" aria-controls="mobile-navigation" @click="mobileMenuOpen = true">
        <span aria-hidden="true">☰</span><span>学习平台</span>
      </button>
      <!-- 左侧菜单项 -->
      <div v-if="isAdmin" class="nav-left"><router-link to="/admin" class="nav-link">平台管理中心</router-link><router-link to="/admin/users" class="nav-link">用户管理</router-link><router-link to="/admin/runs" class="nav-link">运行数据</router-link><router-link to="/admin/courses" class="nav-link">内容管理</router-link><router-link to="/admin/audit" class="nav-link">操作记录</router-link></div>
      <div v-else class="nav-left">
        <router-link to="/editor" class="nav-link" :class="{ active: activeMenu === '/editor' }">首页</router-link>
        <router-link v-if="!isTeacher" to="/learning-center" class="nav-link" :class="{ active: activeMenu === '/learning-center' }">学习中心</router-link>
        <router-link v-else to="/teacher/workbench/learning-center" class="nav-link" :class="{ active: activeMenu.startsWith('/teacher/workbench/learning-center') }">学习中心</router-link>
        <router-link v-if="!isTeacher" to="/daily-checkin" class="nav-link" :class="{ active: activeMenu === '/daily-checkin' }">每日打卡</router-link>
        <router-link v-else to="/teacher/checkin-manage" class="nav-link" :class="{ active: activeMenu === '/teacher/checkin-manage' }">打卡管理</router-link>
        <router-link to="/library" class="nav-link" :class="{ active: activeMenu === '/library' }">资源库</router-link>
        <router-link v-if="!isTeacher" to="/competition" class="nav-link" :class="{ active: activeMenu === '/competition' }">班级测试</router-link>
        <router-link v-else to="/teacher/workbench/competition-manage" class="nav-link" :class="{ active: activeMenu.startsWith('/teacher/workbench/competition-manage') }">班级测试</router-link>
        <router-link to="/forum" class="nav-link" :class="{ active: activeMenu === '/forum' }">论坛</router-link>
        <router-link to="/leaderboard" class="nav-link" :class="{ active: activeMenu === '/leaderboard' }">排行榜</router-link>
        <router-link to="/messages" class="nav-link" :class="{ active: activeMenu === '/messages' }">
          <span class="nav-badge-wrap">
            消息
            <span v-if="unreadCount > 0" class="nav-badge">{{ unreadCount > 99 ? '99+' : unreadCount }}</span>
          </span>
        </router-link>
        <router-link to="/class" class="nav-link" :class="{ active: activeMenu === '/class' }">班级</router-link>
        <router-link to="/points-mall" class="nav-link" :class="{ active: activeMenu === '/points-mall' }">积分商城</router-link>
        <div v-if="isTeacher" class="nav-link dropdown" :class="{ active: isWorkbenchActive, 'is-open': workbenchOpen }" @keydown.esc="workbenchOpen = false">
          <button class="dropdown-trigger" :aria-expanded="workbenchOpen" aria-controls="workbench-menu" @click="workbenchOpen = !workbenchOpen">工作台</button>
          <div id="workbench-menu" class="dropdown-menu">
            <router-link to="/teacher/workbench" class="dropdown-item">教学概览</router-link>
            <router-link to="/teacher/workbench/class-manage" class="dropdown-item">班级管理</router-link>
            <router-link to="/teacher/workbench/student-data" class="dropdown-item">学生数据</router-link>
            <router-link to="/teacher/workbench/task-manage" class="dropdown-item">题目管理</router-link>
          </div>
        </div>
      </div>

      <!-- 右侧登录/用户信息（固定靠右） -->
      <div class="nav-right">
        <!-- 未登录：显示登录/注册 -->
        <router-link to="/login" class="nav-login-btn" v-if="!isLogin">登录/注册</router-link>
        
        <!-- 已登录：显示头像+用户名+退出 -->
        <div class="nav-user-info" v-else>
          <button v-if="isTeacher" class="publish-btn" @click="goPublish">发布打卡任务</button>
          <a :href="router.resolve('/profile').href" class="user-avatar-link" data-user-avatar data-motion-key="nav-avatar" aria-label="打开个人中心" @click="openProfile"><img v-if="userInfo.avatar" :src="userInfo.avatar" alt="" class="user-avatar" /><span v-else class="user-avatar avatar-fallback" aria-hidden="true">{{ (userInfo.name || '管').slice(0, 1) }}</span></a>
          <router-link :to="isAdmin ? '/admin' : '/profile'" class="user-name">{{ displayName }}</router-link>
          <button class="logout-btn" @click="handleLogout">退出</button>
        </div>
      </div>
    </div>
    <el-drawer v-model="mobileMenuOpen" title="导航菜单" direction="ltr" size="min(360px, 90vw)" append-to-body @closed="restoreMenuFocus">
      <nav id="mobile-navigation" class="mobile-navigation" aria-label="移动端主导航">
        <router-link v-for="item in mobileLinks" :key="item.to" :to="item.to" class="mobile-nav-item"
          :class="{ selected: activeMenu === item.to }" @click="mobileMenuOpen = false">
          {{ item.label }}<span v-if="item.to === '/messages' && unreadCount" class="nav-badge">{{ unreadCount > 99 ? '99+' : unreadCount }}</span>
        </router-link>
        <template v-if="isTeacher">
          <p class="mobile-nav-heading">教师工作台</p>
          <router-link v-for="item in teacherLinks" :key="item.to" :to="item.to" class="mobile-nav-item"
            :class="{ selected: activeMenu === item.to }" @click="mobileMenuOpen = false">{{ item.label }}</router-link>
        </template>
      </nav>
    </el-drawer>
  </div>
</template>

<script setup>
import { useRoute, useRouter } from 'vue-router'
import { computed, ref, nextTick, onMounted, onBeforeUnmount, watch } from 'vue'
import { ElMessage } from 'element-plus'
import {morphNavigation,routeDestination} from '@/utils/sharedMotion'
import { getAuthToken, getCurrentUser, removeAuthToken, removeCurrentUser } from '@/utils/authStorage'

const route = useRoute()
const router = useRouter()
function openProfile(event){
  if(event.button!==0 || event.metaKey || event.ctrlKey || event.shiftKey || event.altKey)return
  event.preventDefault()
  if(route.path==='/profile')return
  return morphNavigation(event.currentTarget,()=>router.push('/profile'),routeDestination('[data-profile-avatar]'),{round:true,remember:'profile',from:route.fullPath})
}
const navWrapper=ref(null),selectionVisible=ref(false),selectionStyle=ref({})
let selectionObserver,selectionFrame=0
function updateSelection(){
  selectionFrame=0
  const wrapper=navWrapper.value
  const active=wrapper?.querySelector('.nav-left .nav-link.active, .nav-left .nav-link.router-link-exact-active')
  if(!active || !active.getClientRects().length){selectionVisible.value=false;return}
  const link=active.getBoundingClientRect(),container=wrapper.getBoundingClientRect()
  selectionStyle.value={width:`${link.width+14}px`,transform:`translate3d(${link.left-container.left-7}px,0,0)`}
  selectionVisible.value=true
}
function scheduleSelection(){cancelAnimationFrame(selectionFrame);selectionFrame=requestAnimationFrame(updateSelection)}
const mobileMenuOpen = ref(false)
const workbenchOpen = ref(false)
const menuToggle = ref(null)
const restoreMenuFocus = () => { if (menuToggle.value?.getClientRects().length) menuToggle.value.focus() }
const teacherLinks = [
  { to: '/teacher/workbench', label: '教学概览' },
  { to: '/teacher/workbench/class-manage', label: '班级管理' },
  { to: '/teacher/workbench/student-data', label: '学生数据' },
  { to: '/teacher/workbench/task-manage', label: '题目管理' },
  { to: '/teacher/create-task', label: '发布打卡任务' }
]
const mobileLinks = computed(() => isAdmin.value ? [{to:'/admin',label:'平台管理中心'}, {to:'/admin/users',label:'用户管理'}, {to:'/admin/runs',label:'运行数据'}, {to:'/admin/courses',label:'内容管理'}, {to:'/admin/audit',label:'操作记录'}] : [
  { to: '/editor', label: '首页' },
  { to: isTeacher.value ? '/teacher/workbench/learning-center' : '/learning-center', label: '学习中心' },
  { to: isTeacher.value ? '/teacher/checkin-manage' : '/daily-checkin', label: isTeacher.value ? '打卡管理' : '每日打卡' },
  { to: '/library', label: '资源库' },
  { to: isTeacher.value ? '/teacher/workbench/competition-manage' : '/competition', label: '班级测试' },
  { to: '/forum', label: '论坛' }, { to: '/leaderboard', label: '排行榜' },
  { to: '/messages', label: '消息' }, { to: '/class', label: '班级' },
  { to: '/points-mall', label: '积分商城' },
  ...(isLogin.value ? [{ to: '/profile', label: '个人中心' }] : [{ to: '/login', label: '登录 / 注册' }])
])

// 高亮当前路由
const activeMenu = computed(() => route.path)
const isWorkbenchActive = computed(() => {
  const p = String(route.path || '')
  if (p === '/teacher/workbench') return true
  if (p.startsWith('/teacher/workbench/class-manage')) return true
  if (p.startsWith('/teacher/workbench/student-data')) return true
  if (p.startsWith('/teacher/workbench/task-manage')) return true
  return false
})

// 登录状态管理（和之前逻辑一致）
const userInfo = ref(getCurrentUser())
const isLogin = computed(() => !!userInfo.value)
const isAdmin = computed(() => String(userInfo.value?.role || '') === 'admin')
const isTeacher = computed(() => String(userInfo.value?.role || '') === 'teacher')
const displayName = computed(() => {
  const name = userInfo.value?.name || ''
  return isAdmin.value ? `管理员 · ${name}` : isTeacher.value ? `教师-${name}` : name
})

const unreadCount = ref(0)
let unreadTimer = null
let unreadInFlight = false
let lastUnreadFetchAt = 0

const refreshUnread = async () => {
  const token = getAuthToken()
  if (!token || isAdmin.value) {
    unreadCount.value = 0
    return
  }
  if (typeof document !== 'undefined' && document.hidden) return
  if (String(route.path || '') === '/messages') return
  if (unreadInFlight) return
  const now = Date.now()
  if (now - lastUnreadFetchAt < 8000) return
  lastUnreadFetchAt = now
  try {
    unreadInFlight = true
    const res = await fetch(`/api/messages/unread-count?t=${Date.now()}`, {
      headers: { Authorization: `Bearer ${token}` },
      cache: 'no-store'
    })
    const data = await res.json().catch(() => ({}))
    if (!res.ok || data?.success === false) return
    unreadCount.value = Number(data?.unread || 0)
  } catch {}
  finally {
    unreadInFlight = false
  }
}

const syncUserFromStorage = () => {
  userInfo.value = getCurrentUser()
  refreshUnread()
}

// 退出登录
const handleLogout = () => {
  userInfo.value = null
  removeCurrentUser()
  removeAuthToken()
  window.dispatchEvent(new Event('user-updated'))
  ElMessage.info('已退出登录')
  unreadCount.value = 0
  router.push('/')
}

const goPublish = () => {
  router.push('/teacher/create-task')
}

// 页面加载恢复登录状态
onMounted(() => {
  nextTick(scheduleSelection)
  window.addEventListener('resize',scheduleSelection,{passive:true})
  if(typeof ResizeObserver!=='undefined'){selectionObserver=new ResizeObserver(scheduleSelection);selectionObserver.observe(navWrapper.value)}
  syncUserFromStorage()
  window.addEventListener('user-updated', syncUserFromStorage)
  refreshUnread()
  unreadTimer = setInterval(refreshUnread, 12000)
})

onBeforeUnmount(() => {
  selectionObserver?.disconnect();cancelAnimationFrame(selectionFrame)
  window.removeEventListener('resize',scheduleSelection)
  window.removeEventListener('user-updated', syncUserFromStorage)
  if (unreadTimer) clearInterval(unreadTimer)
  unreadTimer = null
})

watch(
  () => route.path,
  () => {
    mobileMenuOpen.value = false
    workbenchOpen.value = false
    refreshUnread()
    nextTick(scheduleSelection)
  }
)
watch([isTeacher,isAdmin,unreadCount],()=>nextTick(scheduleSelection))
</script>

<style scoped>
.top-nav-container { isolation: isolate; }
.nav-decoration-layer { position: absolute; inset: 0; overflow: hidden; pointer-events: none; user-select: none; color: #e8dafa; z-index: 0; }
.nav-wrapper { position: relative; z-index: 1; }
.nav-code-glyph { position: absolute; top: 4px; opacity: .33; font: 9px/1 Consolas,monospace; letter-spacing: 2px; animation: nav-glyph-drift 6s ease-in-out infinite alternate; }
.glyph-one { left: 2%; }.glyph-two { left: 31%; animation-delay: -2s; }.glyph-three { left: 64%; animation-delay: -4s; }.glyph-four { right: 2%; animation-delay: -1s; }
.nav-data-track { position: absolute; left: 0; right: 0; bottom: 1px; width: 100%; height: 16px; }
.nav-orbit { position: absolute; right: 5px; top: 15px; width: 29px; height: 29px; border: 1px dashed #e5d4fa33; border-radius: 50%; animation: nav-orbit 14s linear infinite; }
.nav-orbit i { position: absolute; left: 11px; top: -2px; width: 4px; height: 4px; background: #e1cdf5; opacity: .5; border-radius: 50%; }
.nav-login-btn { position: relative; overflow: hidden; }
.nav-login-btn::after { content: ''; position: absolute; inset: -30% -80%; background: linear-gradient(110deg,transparent 35%,#ffffff38 50%,transparent 65%); animation: nav-button-glint 10s ease-in-out infinite; pointer-events: none; }
.nav-link { transition: color 180ms, background-color 180ms; }.nav-link:hover { background-color: #ffffff0b; }
@keyframes nav-glyph-drift { from { transform: translateX(-4px); opacity: .2; } to { transform: translateX(7px); opacity: .4; } }
@keyframes nav-orbit { to { transform: rotate(360deg); } }
@keyframes nav-button-glint { 0%,65% { transform: translateX(-55%); opacity: 0; } 72% { opacity: .8; } 88%,100% { transform: translateX(55%); opacity: 0; } }
@media (max-width: 768px) { .glyph-two,.glyph-three,.nav-orbit { display: none; }.nav-code-glyph { opacity: .22; }.nav-data-track { opacity: .7; } }
/* 导航栏容器 */
.top-nav-container {
  width: 100%;
  padding: 0 20px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  box-shadow: 0 2px 10px rgba(0,0,0,0.1);
  position: sticky;
  top: 0;
  z-index: 999;
}
.top-nav-container.admin-theme { background: linear-gradient(110deg, #30223f, #443052); border-bottom: 1px solid #bda1d52b; }
.avatar-fallback { display: inline-flex; align-items: center; justify-content: center; background: #427b89; color: #fff; font-size: 14px; }

.top-nav-container.teacher-theme {
  background: linear-gradient(135deg, #2b1b4f 0%, #3a1c7a 100%);
}

/* 导航栏内容容器（控制宽度+居中） */
.nav-wrapper {
  max-width: 1200px;
  margin: 0 auto;
  height: 60px;
  display: flex;
  justify-content: space-between; /* 左右分栏，彻底杜绝折叠 */
  align-items: center;
}

/* 左侧菜单项 */
.nav-left {
  display: flex;
  gap: 20px; /* 从30px改小 */
  
}

/* 导航链接样式 */
.nav-link {
  color: #fff;
  text-decoration: none;
  font-size: 15px;
  padding: 0 5px;
  height: 60px;
  line-height: 60px;
  position: relative;
  white-space: nowrap; /* 强制不换行 */
}

.nav-badge-wrap {
  position: relative;
  display: inline-flex;
  align-items: center;
  gap: 6px;
}

.nav-badge {
  min-width: 18px;
  height: 18px;
  padding: 0 6px;
  border-radius: 999px;
  background: #ef4444;
  color: #fff;
  font-size: 12px;
  font-weight: 900;
  line-height: 18px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
}

/* 高亮当前页面的链接 */
.nav-link.active {
  color: #ffd700;
  font-weight: 500;
}
.nav-link.active::after {
  content: '';
  position: absolute;
  bottom: 0;
  left: 0;
  width: 100%;
  height: 3px;
  background: #ffd700;
}

/* Keep the glow and corner marks on the same expanded selection surface. */
.top-nav-container .nav-left .nav-link.active,
.top-nav-container .nav-left .nav-link.router-link-exact-active {
  color: #ffd700;
  text-shadow: 0 0 12px #e6c4ff55;
  background: transparent;
}

.nav-selection {
  position: absolute; left: 0; top: 5px; height: 50px; border-radius: 11px; pointer-events: none;
  transition: transform 380ms cubic-bezier(.2,.75,.25,1), width 300ms cubic-bezier(.2,.75,.25,1);
  will-change: transform;
  background-color: transparent;
  background-image:
    linear-gradient(#dfcafa99,#dfcafa99),linear-gradient(#dfcafa99,#dfcafa99),
    linear-gradient(#dfcafa99,#dfcafa99),linear-gradient(#dfcafa99,#dfcafa99),
    linear-gradient(#dfcafa99,#dfcafa99),linear-gradient(#dfcafa99,#dfcafa99),
    linear-gradient(#dfcafa99,#dfcafa99),linear-gradient(#dfcafa99,#dfcafa99),
    radial-gradient(ellipse at center,#e0c6ff30,transparent 76%);
  background-size: 10px 1px,1px 10px,10px 1px,1px 10px,10px 1px,1px 10px,10px 1px,1px 10px,100% 100%;
  background-position: left top,left top,right top,right top,left bottom,left bottom,right bottom,right bottom,center;
  background-repeat: no-repeat;
  animation: nav-selection-breathe 3.8s ease-in-out infinite;
}
.nav-selection::after { content: ''; position: absolute; left: 7px; right: 7px; bottom: -5px; height: 3px; background: #ffd700; }
.top-nav-container .nav-left .nav-link.active::after, .top-nav-container .nav-left .nav-link.router-link-exact-active::after { display: none; }
@keyframes nav-selection-enter { from { opacity: .55; transform: translateY(2px) scale(.94); } to { opacity: 1; transform: translateY(0) scale(1); } }
@keyframes nav-selection-breathe { 0%,100% { box-shadow: inset 0 0 12px #d3b3f20a; } 50% { box-shadow: inset 0 0 18px #d3b3f226; } }

/* 右侧登录/用户信息 */
.nav-right {
  display: flex;
  align-items: center;
  gap: 15px;
}

.publish-btn {
  color: #fff;
  background: rgba(255,255,255,0.2);
  border: 1px solid rgba(255,255,255,0.55);
  border-radius: 8px;
  padding: 6px 12px;
  font-size: 13px;
  cursor: pointer;
  transition: all 0.2s;
  font-weight: 700;
}
.publish-btn:hover {
  background: rgba(255,255,255,0.28);
  transform: translateY(-1px);
}

/* 登录/注册按钮 */
.nav-login-btn {
  color: #fff;
  background: rgba(255,255,255,0.2);
  border: 1px solid #fff;
  border-radius: 4px;
  padding: 6px 15px;
  text-decoration: none;
  font-size: 14px;
  transition: all 0.3s;
}
.nav-login-btn:hover {
  background: rgba(255,255,255,0.3);
}

/* 登录后用户信息 */
.nav-user-info {
  display: flex;
  align-items: center;
  gap: 10px;
  color: #fff;
}

.user-avatar {
  width: 32px;
  height: 32px;
  border-radius: 50%;
  border: 2px solid #fff;
}

.user-name {
  font-size: 14px;
  font-weight: 500;
  color: #fff;
  text-decoration: none;
}

/* 退出按钮 */
.logout-btn {
  background: transparent;
  border: 1px solid #fff;
  color: #fff;
  border-radius: 4px;
  padding: 4px 10px;
  font-size: 12px;
  cursor: pointer;
  transition: all 0.3s;
}
.logout-btn:hover {
  background: rgba(255,255,255,0.2);
}

.dropdown {
  position: relative;
  cursor: default;
}

.dropdown-trigger {
  display: inline-block;
  background: transparent; border: 0; color: inherit; font: inherit; cursor: pointer;
}

.dropdown-menu {
  position: absolute;
  top: 52px;
  left: 0;
  background: rgba(20, 20, 24, 0.92);
  border: 1px solid rgba(255,255,255,0.16);
  border-radius: 10px;
  min-width: 160px;
  padding: 8px;
  visibility: hidden;
  opacity: 0;
  pointer-events: none;
  transform: translateY(-6px) scale(.98);
  transform-origin: top left;
  transition: opacity 160ms ease, transform 200ms cubic-bezier(.2,.75,.25,1), visibility 200ms;
  box-shadow: 0 10px 30px rgba(0,0,0,0.25);
}

.dropdown:hover .dropdown-menu, .dropdown:focus-within .dropdown-menu, .dropdown.is-open .dropdown-menu {
  visibility: visible;
  opacity: 1;
  pointer-events: auto;
  transform: translateY(0) scale(1);
}

.dropdown-item {
  display: block;
  color: #fff;
  text-decoration: none;
  padding: 8px 10px;
  border-radius: 8px;
  font-weight: 600;
  line-height: 1.2;
}

.dropdown-item:hover {
  background: rgba(255,255,255,0.14);
}

.mobile-menu-toggle { display: none; }
.mobile-navigation { display: grid; gap: 6px; }
.mobile-nav-item { display: flex; justify-content: space-between; align-items: center; padding: 12px 16px; min-height: 44px; border-radius: 10px; color: #334155; text-decoration: none; }
.mobile-nav-item:hover, .mobile-nav-item.selected { color: #4f46e5; background: #eef2ff; }
.mobile-nav-item.selected { position: relative; box-shadow: inset 3px 0 #b59ad4; padding-right: 42px; animation: nav-selection-enter 320ms cubic-bezier(.16,1,.3,1); }
.mobile-nav-item.selected::after { content: '</>'; position: absolute; right: 12px; top: 50%; transform: translateY(-50%); font: 11px Consolas,monospace; color: #ab8bcb; pointer-events: none; }
.mobile-nav-heading { padding: 18px 16px 8px; color: #64748b; font-size: 13px; border-top: 1px solid #e2e8f0; margin-top: 12px; }
.nav-right { min-width: 0; flex-shrink: 0; }
.nav-user-info { min-width: 0; }
.user-name { max-width: 130px; overflow: hidden; white-space: nowrap; text-overflow: ellipsis; }
@media (max-width: 1200px) {
  .nav-wrapper {
    height: 60px; gap: 12px;
  }
  .nav-left, .nav-selection { display: none; }
  .mobile-menu-toggle { display: inline-flex; align-items: center; gap: 10px; min-height: 44px; flex-shrink: 0; background: transparent; border: 0; color: #fff; font-size: 16px; cursor: pointer; }
  .mobile-menu-toggle span:first-child { font-size: 23px; }
  .publish-btn { display: none; }
}
@media (max-width: 480px) {
  .top-nav-container { padding: 0 14px; }
  .nav-user-info { gap: 8px; }
  .user-name { max-width: 72px; font-size: 12px; }
  .user-avatar { width: 28px; height: 28px; }
  .nav-login-btn { padding: 7px 10px; white-space: nowrap; }
}
.user-avatar-link { display: inline-flex; flex-shrink: 0; border-radius: 50%; text-decoration: none; transition: transform 180ms, box-shadow 180ms; }.user-avatar-link:hover { transform: translateY(-2px) scale(1.04); box-shadow: 0 0 0 4px #dfc7fa33; }
</style>
