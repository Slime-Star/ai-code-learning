import { createRouter, createWebHistory } from 'vue-router'
// 导入所有页面组件
const Home = () => import('@/views/Home.vue')
const LearningCenter = () => import('@/views/LearningCenter.vue')
const ResourceLibrary = () => import('@/views/Library.vue')
const Forum = () => import('@/views/Forum.vue')
const Login = () => import('@/views/Login.vue')
const Competition = () => import('@/views/Competition.vue')
const PointsMall = () => import('@/views/PointsMall.vue')
const Leaderboard = () => import('@/views/Leaderboard.vue')
const Messages = () => import('@/views/Messages.vue')
//导入注册页组件
const Register = () => import('@/views/Register.vue')
const DailyCheckIn = () => import('@/views/DailyCheckIn.vue')
const Profile = () => import('@/views/Profile.vue')
const ClassPage = () => import('@/views/Class.vue')
const TeacherCheckinManage = () => import('@/views/teacher/CheckinManage.vue')
const TeacherCreateTask = () => import('@/views/teacher/CreateTask.vue')
const TeacherWorkbench = () => import('@/views/teacher/Workbench.vue')
const TeacherClassManage = () => import('@/views/teacher/ClassManage.vue')
const TeacherStudentData = () => import('@/views/teacher/StudentData.vue')
const TeacherTaskManage = () => import('@/views/teacher/TaskManage.vue')
const TeacherCompetitionManage = () => import('@/views/teacher/CompetitionManage.vue')
const TeacherLearningCenter = () => import('@/views/teacher/LearningCenter.vue')
import { getCurrentUser, getAuthToken, removeCurrentUser, removeAuthToken, setCurrentUser } from '@/utils/authStorage'

const roleHome = role => role === 'admin' ? '/admin' : role === 'teacher' ? '/teacher/workbench' : '/learning-center'
const routes = [
  { path: '/admin/:module?', name: 'AdminPanel', component: () => import('@/views/admin/AdminPanel.vue'), meta: { role: 'admin' } },
  { path: '/', redirect: '/learning-center' },
  // 保留首页编程工作台，学习中心作为默认入口。
  {
    path: '/editor',
    name: 'Home',
    component: Home
  },
  // 学习中心
  {
    path: '/learning-center',
    name: 'LearningCenter',
    component: LearningCenter
  },
  // 每日签到（并入每日打卡，旧路由保留为跳转）
  {
    path: '/daily-signin',
    redirect: '/daily-checkin'
  },
  // 每日打卡
  {
    path: '/daily-checkin',
    name: 'DailyCheckIn',
    component: DailyCheckIn,
    meta: { role: 'student' }
  },
  // 资源库
  {
    path: '/library',
    name: 'Library',
    component: ResourceLibrary
  },
  // 测试
  {
    path: '/competition',
    name: 'Competition',
    component: Competition
  },
  {
    path: '/competition/:id',
    name: 'CompetitionPlay',
    component: () => import('@/views/CompetitionPlay.vue'),
    meta: { role: 'student' }
  },
  // 积分商城
  {
    path: '/points-mall',
    name: 'PointsMall',
    component: PointsMall
  },
  // 排行榜
  {
    path: '/leaderboard',
    name: 'Leaderboard',
    component: Leaderboard
  },
  // 消息
  {
    path: '/messages',
    name: 'Messages',
    component: Messages
  },
  // 论坛
  {
    path: '/forum',
    name: 'Forum',
    component: Forum
  },
  // 登录/注册
  {
    path: '/login',
    name: 'Login',
    component: Login
  },
  // 注册页路由
  {
    path: '/register',
    name: 'Register',
    component: Register
  },
  // 班级
  {
    path: '/class',
    name: 'Class',
    component: ClassPage
  },
  // 个人中心
  {
    path: '/profile',
    name: 'Profile',
    component: Profile
  },
  // 错题本
  {
    path: '/wrong-questions',
    name: 'WrongQuestions',
    component: () => import('@/views/WrongQuestions.vue'),
    meta: { role: 'student' }
  },
  // 教师端
  {
    path: '/teacher/checkin-manage',
    name: 'TeacherCheckinManage',
    component: TeacherCheckinManage,
    meta: { role: 'teacher' }
  },
  {
    path: '/teacher/create-task',
    name: 'TeacherCreateTask',
    component: TeacherCreateTask,
    meta: { role: 'teacher' }
  },
  {
    path: '/teacher/workbench',
    name: 'TeacherWorkbench',
    component: TeacherWorkbench,
    meta: { role: 'teacher' }
  },
  {
    path: '/teacher/workbench/class-manage',
    name: 'TeacherClassManage',
    component: TeacherClassManage,
    meta: { role: 'teacher' }
  },
  {
    path: '/teacher/workbench/student-data',
    name: 'TeacherStudentData',
    component: TeacherStudentData,
    meta: { role: 'teacher' }
  },
  {
    path: '/teacher/workbench/learning-center',
    name: 'TeacherLearningCenter',
    component: TeacherLearningCenter,
    meta: { role: 'teacher' }
  },
  {
    path: '/teacher/workbench/task-manage',
    name: 'TeacherTaskManage',
    component: TeacherTaskManage,
    meta: { role: 'teacher' }
  },
  {
    path: '/teacher/workbench/competition-manage',
    name: 'TeacherCompetitionManage',
    component: TeacherCompetitionManage,
    meta: { role: 'teacher' }
  },
  // 按语言学习的动态路由
  {
    path: '/learn/:language',
    name: 'Learn',
    component: () => import('@/views/Learn.vue'),
    meta: { role: 'student' }
  },
  //判题
  {
  path: '/code-judge',
  name: 'CodeJudge',
  component: () => import('../views/CodeJudge.vue')
}
]

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes
})

router.beforeEach(async (to) => {
  let user = getCurrentUser()
  let role = String(user?.role || '')
  if (to.meta?.role === 'admin') {
    if (!getAuthToken()) { removeCurrentUser(); return '/login' }
    try {
      const res = await fetch('/api/auth/me', { headers: { Authorization: `Bearer ${getAuthToken()}` } })
      if (res.status === 401) { removeCurrentUser(); removeAuthToken(); return '/login' }
      if (!res.ok) return false
      const data = await res.json()
      user = data.user
      role = String(user?.role || '')
      if (user) { setCurrentUser(user); window.dispatchEvent(new Event('user-updated')) }
    } catch { return false }
    if (role !== 'admin') return role ? roleHome(role) : '/login'
  }
  if ((to.path === '/login' || to.path === '/register') && role) return roleHome(role)
  if (to.meta?.role && role !== to.meta.role) return role ? roleHome(role) : '/login'
  return true
})

export default router
