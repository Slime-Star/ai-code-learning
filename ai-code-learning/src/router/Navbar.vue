<template>
  <!-- 纯Flex导航栏，彻底禁用折叠 -->
  <div class="top-nav-container" :class="{ 'teacher-theme': isTeacher }">
    <div class="nav-wrapper">
      <!-- 左侧菜单项 -->
      <div class="nav-left">
        <router-link to="/editor" class="nav-link" :class="{ active: activeMenu === '/editor' }">首页</router-link>
        <router-link v-if="!isTeacher" to="/learning-center" class="nav-link" :class="{ active: activeMenu === '/learning-center' }">学习中心</router-link>
        <router-link v-else to="/teacher/workbench/learning-center" class="nav-link" :class="{ active: activeMenu.startsWith('/teacher/workbench/learning-center') }">学习中心</router-link>
        <router-link v-if="!isTeacher" to="/daily-checkin" class="nav-link" :class="{ active: activeMenu === '/daily-checkin' }">每日打卡</router-link>
        <router-link v-else to="/teacher/checkin-manage" class="nav-link" :class="{ active: activeMenu === '/teacher/checkin-manage' }">打卡管理</router-link>
        <router-link to="/library" class="nav-link" :class="{ active: activeMenu === '/library' }">资源库</router-link>
        <router-link v-if="!isTeacher" to="/competition" class="nav-link" :class="{ active: activeMenu === '/competition' }">测试</router-link>
        <router-link v-else to="/teacher/workbench/competition-manage" class="nav-link" :class="{ active: activeMenu.startsWith('/teacher/workbench/competition-manage') }">测试</router-link>
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
        <div v-if="isTeacher" class="nav-link dropdown" :class="{ active: isWorkbenchActive }">
          <span class="dropdown-trigger">工作台</span>
          <div class="dropdown-menu">
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
          <img :src="userInfo.avatar" alt="用户头像" class="user-avatar" />
          <router-link to="/profile" class="user-name">{{ displayName }}</router-link>
          <button class="logout-btn" @click="handleLogout">退出</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { useRoute, useRouter } from 'vue-router'
import { computed, ref, onMounted, onBeforeUnmount, watch } from 'vue'
import { ElMessage } from 'element-plus'
import { getAuthToken, getCurrentUser, removeAuthToken, removeCurrentUser } from '@/utils/authStorage'

const route = useRoute()
const router = useRouter()

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
const isTeacher = computed(() => String(userInfo.value?.role || '') === 'teacher')
const displayName = computed(() => {
  const name = userInfo.value?.name || ''
  return isTeacher.value ? `教师-${name}` : name
})

const unreadCount = ref(0)
let unreadTimer = null
let unreadInFlight = false
let lastUnreadFetchAt = 0

const refreshUnread = async () => {
  const token = getAuthToken()
  if (!token) {
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
  syncUserFromStorage()
  window.addEventListener('user-updated', syncUserFromStorage)
  refreshUnread()
  unreadTimer = setInterval(refreshUnread, 12000)
})

onBeforeUnmount(() => {
  window.removeEventListener('user-updated', syncUserFromStorage)
  if (unreadTimer) clearInterval(unreadTimer)
  unreadTimer = null
})

watch(
  () => route.path,
  () => {
    refreshUnread()
  }
)
</script>

<style scoped>
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
  gap: 30px; /* 菜单项之间的间距 */
}

/* 导航链接样式 */
.nav-link {
  color: #fff;
  text-decoration: none;
  font-size: 16px;
  padding: 0 5px;
  height: 60px;
  line-height: 60px;
  position: relative;
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
  display: none;
  box-shadow: 0 10px 30px rgba(0,0,0,0.25);
}

.dropdown:hover .dropdown-menu {
  display: block;
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

/* 响应式适配（小屏幕也只换行，不折叠） */
@media (max-width: 768px) {
  .nav-wrapper {
    flex-wrap: wrap;
    height: auto;
    padding: 10px 0;
  }
  .nav-left {
    width: 100%;
    gap: 15px;
    margin-bottom: 10px;
  }
  .nav-link {
    height: 40px;
    line-height: 40px;
    font-size: 14px;
  }
}
</style>
