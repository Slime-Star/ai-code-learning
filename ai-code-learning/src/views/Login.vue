<template>
  <div class="login-page">
    <div ref="loginCard" class="login-container">
      <!-- 左侧装饰区 -->
      <div class="login-banner">
        <div class="banner-content">
          <h1>AI编程学习中心</h1>
          <p>从零基础到编程高手的一站式学习平台</p>
          <div class="banner-features">
            <div class="feature-item">
              <el-icon size="24"><Document /></el-icon>
              <span>系统化学习路径</span>
            </div>
            <div class="feature-item">
              <el-icon size="24"><VideoPlay /></el-icon>
              <span>实战项目驱动</span>
            </div>
            <div class="feature-item">
              <el-icon size="24"><EditPen /></el-icon>
              <span>实时编程练习</span>
            </div>
          </div>
        <TopicArt scene="shield" inverse compact />
        </div>
      </div>

      <!-- 右侧登录表单 -->
      <div class="login-form-wrapper">
        <div class="login-header">
          <h2>欢迎登录</h2>
          <p>登录后即可体验收藏课程等更多功能</p>
        </div>

        <!-- 登录表单 -->
        <el-form
          ref="loginFormRef"
          :model="loginForm"
          :rules="loginRules"
          class="login-form"
          @submit.prevent="handleLogin"
        >
          <el-form-item prop="username">
            <el-input
              v-model="loginForm.username"
              placeholder="请输入注册的用户名"
              prefix-icon="User"
              size="large"
              autocomplete="off"
            />
          </el-form-item>

          <el-form-item prop="password">
            <el-input
              v-model="loginForm.password"
              type="password"
              placeholder="请输入密码"
              prefix-icon="Lock"
              size="large"
              autocomplete="off"
              @keyup.enter="handleLogin"
            />
          </el-form-item>

          <el-form-item class="form-actions">
            <el-checkbox v-model="loginForm.rememberMe">记住我</el-checkbox>
            <el-link type="primary" @click="showForgetPwdDialog = true">忘记密码？</el-link>
          </el-form-item>

          <el-form-item>
            <el-button
              type="primary"
              size="large"
              class="login-btn"
              :loading="loginLoading"
              @click="handleLogin"
            >
              登录
            </el-button>
          </el-form-item>

          <el-form-item class="register-link">
            <span>还没有账号？</span>
            <el-link type="primary" @click="goToRegister">立即注册</el-link>
          </el-form-item>
        </el-form>
      </div>
    </div>

    <!-- 忘记密码弹窗 -->
    <el-dialog
      v-model="showForgetPwdDialog"
      title="找回密码"
      width="400px"
      center
    >
      <el-form
        ref="forgetFormRef"
        :model="forgetForm"
        :rules="forgetRules"
        label-width="80px"
      >
        <el-form-item label="用户名" prop="username">
          <el-input
            v-model="forgetForm.username"
            placeholder="请输入注册的用户名"
            disabled="false"
          />
        </el-form-item>
        <el-form-item label="新密码" prop="newPassword">
          <el-input
            v-model="forgetForm.newPassword"
            type="password"
            placeholder="请输入新密码（6-20位）"
          />
        </el-form-item>
        <el-form-item label="确认密码" prop="confirmPassword">
          <el-input
            v-model="forgetForm.confirmPassword"
            type="password"
            placeholder="请再次输入新密码"
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showForgetPwdDialog = false">取消</el-button>
        <el-button type="primary" @click="handleForgetPwd">确认重置</el-button>
      </template>
    </el-dialog>

    <!-- 页脚 -->
    <footer class="login-footer">
      <p>© 2026 AI编程学习中心 版权所有 | 京ICP备12345678号</p>
    </footer>
  </div>
</template>

<script setup>
import TopicArt from '@/components/TopicArt.vue'
import landingPreview from '@/assets/learning-hero/coding.jpg'
import { ref, reactive, nextTick, onMounted } from 'vue'
import {flyLoginToAvatar} from '@/utils/loginFlight'
import { ElMessage, ElMessageBox } from 'element-plus'
import { useRouter } from 'vue-router'
import { Document, VideoPlay, EditPen } from '@element-plus/icons-vue'
import { getCurrentUser, setCurrentUser, setAuthToken } from '@/utils/authStorage'

// 路由实例
const router = useRouter()

// 表单相关
const loginCard = ref(null)
const loginFormRef = ref(null)
const forgetFormRef = ref(null)
const loginLoading = ref(false)
const showForgetPwdDialog = ref(false) // 忘记密码弹窗

// 登录表单数据
const loginForm = reactive({
  username: '',
  password: '',
  rememberMe: false
})

// 忘记密码表单数据
const forgetForm = reactive({
  username: '',
  newPassword: '',
  confirmPassword: ''
})

// 登录校验规则
const loginRules = reactive({
  username: [
    { required: true, message: '请输入用户名', trigger: 'blur' },
    { min: 3, max: 20, message: '用户名长度在 3 到 20 个字符', trigger: 'blur' }
  ],
  password: [
    { required: true, message: '请输入密码', trigger: 'blur' },
    { min: 6, max: 20, message: '密码长度在 6 到 20 个字符', trigger: 'blur' }
  ]
})

// 忘记密码校验规则
const forgetRules = reactive({
  username: [
    { required: true, message: '请输入用户名', trigger: 'blur' }
  ],
  newPassword: [
    { required: true, message: '请输入新密码', trigger: 'blur' },
    { min: 6, max: 20, message: '密码长度在 6 到 20 个字符', trigger: 'blur' }
  ],
  confirmPassword: [
    { required: true, message: '请确认新密码', trigger: 'blur' },
    { 
      validator: (rule, value, callback) => {
        if (value !== forgetForm.newPassword) {
          callback(new Error('两次输入的密码不一致'))
        } else {
          callback()
        }
      },
      trigger: 'blur'
    }
  ]
})

// 登录处理
const handleLogin = async () => {
  if(loginLoading.value)return
  // 表单校验
  try {
    await loginFormRef.value.validate()
  } catch (error) {
    ElMessage.error('请完善登录信息')
    return
  }

  loginLoading.value = true

  try {
    const res = await fetch('/api/auth/login', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        username: loginForm.username,
        password: loginForm.password
      })
    })
    const data = await res.json().catch(() => ({}))
    if (!res.ok || data?.success === false) {
      throw new Error(data?.detail || data?.message || '登录失败')
    }

    const token = data?.token || ''
    const user = data?.user || {}
    if (!token || !user?.id) {
      throw new Error('登录失败')
    }

    setAuthToken(token)
    let finalUser = user
    try {
      const meRes = await fetch('/api/auth/me', {
        headers: { Authorization: `Bearer ${token}` }
      })
      const meData = await meRes.json().catch(() => ({}))
      if (meRes.ok && meData?.success && meData?.user?.id) {
        finalUser = meData.user
      }
    } catch {}
    setCurrentUser({
      id: finalUser.id,
      role: finalUser.role || 'student',
      name: finalUser.name || finalUser.username || loginForm.username,
      avatar: finalUser.avatar || '',
      collectedCourses: finalUser.collectedCourses || []
    })
    window.dispatchEvent(new Event('user-updated'))
    
    // 记住我功能
    if (loginForm.rememberMe) {
      localStorage.setItem('rememberUser', loginForm.username)
    } else {
      localStorage.removeItem('rememberUser')
    }

    const destination=finalUser.role === 'admin' ? '/admin' : (finalUser.role || 'student') === 'teacher' ? '/teacher/workbench' : '/learning-center'
    const loaders=router.resolve(destination).matched.flatMap(record=>Object.values(record.components || {}).filter(component=>typeof component==='function'))
    await Promise.allSettled(loaders.map(load=>load()))
    ElMessage.success(`欢迎回来，${user.username || loginForm.username}！`)
    await nextTick()
    await flyLoginToAvatar(loginCard.value,()=>router.push(destination))

  } catch (error) {
    ElMessage.error(error?.message || '登录失败，请稍后重试')
  } finally {
    loginLoading.value = false
  }
}

// 忘记密码处理
const handleForgetPwd = async () => {
  try {
    await forgetFormRef.value.validate()
  } catch (error) {
    ElMessage.error('请完善表单信息')
    return
  }

  try {
    const res = await fetch('/api/auth/reset-password', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        username: forgetForm.username,
        new_password: forgetForm.newPassword
      })
    })
    const data = await res.json().catch(() => ({}))
    if (!res.ok || data?.success === false) {
      throw new Error(data?.detail || data?.message || '密码重置失败')
    }

    ElMessage.success('密码重置成功，请使用新密码登录')
    showForgetPwdDialog.value = false
    forgetForm.username = ''
    forgetForm.newPassword = ''
    forgetForm.confirmPassword = ''
  } catch (e) {
    ElMessage.error(e?.message || '密码重置失败')
  }
}

// 跳转到注册页
const goToRegister = () => {
  router.push('/register')
}

// 页面加载时初始化
onMounted(() => {
  const preview=new Image();preview.decoding='async';preview.fetchPriority='low';preview.src=landingPreview
  const u = getCurrentUser()
  if (u) {
    router.push(u?.role === 'admin' ? '/admin' : (u?.role || 'student') === 'teacher' ? '/teacher/workbench' : '/learning-center')
    return
  }
  
  // 填充记住的用户名
  const rememberUser = localStorage.getItem('rememberUser')
  if (rememberUser) {
    loginForm.username = rememberUser
    loginForm.rememberMe = true
  }
})
</script>

<style scoped>
.login-page {
  min-height: 100vh;
  background: linear-gradient(135deg, #f5f7fa 0%, #e4edf5 100%);
  display: flex;
  flex-direction: column;
  font-family: "Microsoft YaHei", sans-serif;
}

.login-container {
  flex: 1;
  display: flex;
  justify-content: center;
  align-items: center;
  max-width: 1200px;
  margin: 0 auto;
  padding: 40px 20px;
  gap: 0;
}

.login-banner {
  flex: 1;
  height: 600px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border-radius: 12px 0 0 12px;
  display: flex;
  justify-content: center;
  align-items: center;
  color: #fff;
  padding: 60px;
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.1);
}

.banner-content h1 {
  font-size: 42px;
  margin-bottom: 20px;
  font-weight: 700;
}

.banner-content p {
  font-size: 18px;
  margin-bottom: 40px;
  color: #e0e0e0;
  line-height: 1.6;
}

.feature-item {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 20px;
  font-size: 16px;
}

.login-form-wrapper {
  flex: 1;
  height: 600px;
  background: #fff;
  border-radius: 0 12px 12px 0;
  padding: 60px;
  display: flex;
  flex-direction: column;
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.1);
}

.login-header {
  margin-bottom: 40px;
  text-align: center;
}

.login-header h2 {
  font-size: 32px;
  color: #2c3e50;
  margin-bottom: 10px;
  font-weight: 600;
}

.login-header p {
  font-size: 14px;
  color: #666;
}

.login-form {
  width: 100%;
  max-width: 400px;
  margin: 0 auto;
}

.form-actions {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.login-btn {
  width: 100%;
  height: 48px;
  font-size: 16px;
}

.register-link {
  text-align: center;
  margin-top: 20px;
  font-size: 14px;
  color: #666;
}

.login-footer {
  text-align: center;
  padding: 20px;
  font-size: 14px;
  color: #999;
  background: #fff;
}

@media (max-width: 768px) {
  .login-container {
    flex-direction: column;
  }

  .login-banner {
    width: 100%;
    height: 200px;
    border-radius: 12px 12px 0 0;
    padding: 20px;
  }

  .banner-content h1 {
    font-size: 24px;
  }

  .banner-content p {
    font-size: 14px;
    margin-bottom: 20px;
  }

  .feature-item {
    font-size: 12px;
    margin-bottom: 10px;
  }

  .login-form-wrapper {
    width: 100%;
    height: auto;
    border-radius: 0 0 12px 12px;
    padding: 30px 20px;
  }

  .login-header h2 {
    font-size: 24px;
  }
}
</style>
