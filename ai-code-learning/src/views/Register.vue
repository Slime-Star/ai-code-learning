<template>
  <div class="register-page">
    <div class="register-container">
      <!-- 左侧装饰区 -->
      <div class="register-banner">
        <div class="banner-content">
          <h1>欢迎注册</h1>
          <p>注册后即可享受所有学习资源和个性化服务</p>
          <div class="banner-features">
            <div class="feature-item">
              <el-icon size="24"><User /></el-icon>
              <span>个性化学习推荐</span>
            </div>
            <div class="feature-item">
              <el-icon size="24"><Star /></el-icon>
              <span>收藏喜欢的课程</span>
            </div>
            <div class="feature-item">
              <el-icon size="24"><Reading /></el-icon>
              <span>学习进度自动保存</span>
            </div>
          </div>
        <TopicArt scene="launch" inverse compact />
        </div>
      </div>

      <!-- 右侧注册表单 -->
      <div class="register-form-wrapper">
        <div class="register-header">
          <h2>创建账号</h2>
          <p>只需几步，开启你的编程学习之旅</p>
        </div>

        <!-- 注册表单 -->
        <el-form
          ref="registerFormRef"
          :model="registerForm"
          :rules="registerRules"
          class="register-form"
          @submit.prevent="handleRegister"
        >
          <el-form-item prop="username">
            <el-input
              v-model="registerForm.username"
              placeholder="请设置用户名（3-20位）"
              prefix-icon="User"
              size="large"
              autocomplete="off"
            />
          </el-form-item>

          <el-form-item prop="password">
            <el-input
              v-model="registerForm.password"
              type="password"
              placeholder="请设置密码（6-20位）"
              prefix-icon="Lock"
              size="large"
              autocomplete="off"
            />
          </el-form-item>

          <el-form-item prop="confirmPassword">
            <el-input
              v-model="registerForm.confirmPassword"
              type="password"
              placeholder="请确认密码"
              prefix-icon="Lock"
              size="large"
              autocomplete="off"
            />
          </el-form-item>

          <el-form-item prop="email">
            <el-input
              v-model="registerForm.email"
              placeholder="请输入邮箱（选填）"
              prefix-icon="Message"
              size="large"
              autocomplete="off"
            />
          </el-form-item>

          <el-form-item prop="role">
            <el-radio-group v-model="registerForm.role" class="role-group">
              <el-radio-button label="student">我是学生</el-radio-button>
              <el-radio-button label="teacher">我是老师</el-radio-button>
            </el-radio-group>
          </el-form-item>

          <el-form-item class="form-actions">
            <el-checkbox v-model="registerForm.agree" checked>
              我已阅读并同意<a href="#" class="agreement-link">《用户协议》</a>和<a href="#" class="agreement-link">《隐私政策》</a>
            </el-checkbox>
          </el-form-item>

          <el-form-item>
            <el-button
              type="primary"
              size="large"
              class="register-btn"
              :loading="registerLoading"
              @click="handleRegister"
            >
              注册
            </el-button>
          </el-form-item>

          <el-form-item class="login-link">
            <span>已有账号？</span>
            <el-link type="primary" @click="goToLogin">立即登录</el-link>
          </el-form-item>
        </el-form>
      </div>
    </div>

    <!-- 页脚 -->
    <footer class="register-footer">
      <p>© 2026 AI编程学习中心 版权所有 | 京ICP备12345678号</p>
    </footer>
  </div>
</template>

<script setup>
import TopicArt from '@/components/TopicArt.vue'
import { ref, reactive, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { useRouter } from 'vue-router'
import { User, Star, Reading, Message } from '@element-plus/icons-vue'
import { getCurrentUser, setAuthToken, setCurrentUser } from '@/utils/authStorage'

// 路由实例
const router = useRouter()

// 表单相关
const registerFormRef = ref(null)
const registerLoading = ref(false)

// 注册表单数据
const registerForm = reactive({
  username: '',
  password: '',
  confirmPassword: '',
  email: '',
  role: 'student',
  agree: true
})

// 注册校验规则
const registerRules = reactive({
  username: [
    { required: true, message: '请输入用户名', trigger: 'blur' },
    { min: 3, max: 20, message: '用户名长度在 3 到 20 个字符', trigger: 'blur' }
  ],
  password: [
    { required: true, message: '请输入密码', trigger: 'blur' },
    { min: 6, max: 20, message: '密码长度在 6 到 20 个字符', trigger: 'blur' }
  ],
  confirmPassword: [
    { required: true, message: '请确认密码', trigger: 'blur' },
    { 
      validator: (rule, value, callback) => {
        if (value !== registerForm.password) {
          callback(new Error('两次输入的密码不一致'))
        } else {
          callback()
        }
      },
      trigger: 'blur'
    }
  ],
  role: [
    { required: true, message: '请选择角色', trigger: 'change' }
  ],
  agree: [
    { 
      validator: (rule, value, callback) => {
        if (!value) {
          callback(new Error('请同意用户协议和隐私政策'))
        } else {
          callback()
        }
      },
      trigger: 'change'
    }
  ]
})

// 注册处理
const handleRegister = async () => {
  // 表单校验
  try {
    await registerFormRef.value.validate()
  } catch (error) {
    ElMessage.error('请完善注册信息')
    return
  }

  registerLoading.value = true

  try {
    const res = await fetch('/api/auth/register', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        username: registerForm.username,
        password: registerForm.password,
        email: registerForm.email,
        role: registerForm.role
      })
    })
    const data = await res.json().catch(() => ({}))
    if (!res.ok || data?.success === false) {
      throw new Error(data?.detail || data?.message || '注册失败')
    }

    const loginRes = await fetch('/api/auth/login', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        username: registerForm.username,
        password: registerForm.password
      })
    })
    const loginData = await loginRes.json().catch(() => ({}))
    if (!loginRes.ok || loginData?.success === false) {
      // 自动登录失败，引导用户手动登录
      ElMessage.warning('注册成功，请手动登录')
      router.push('/login')
      return
    }

    // 自动登录成功，保存 token 和用户信息
    const token = loginData.token
    const user = loginData.user
    if (!token || !user?.id) {
      ElMessage.warning('登录信息不完整，请手动登录')
      router.push('/login')
      return
    }

    setAuthToken(token)
    setCurrentUser({
      id: user.id,
      role: user.role || registerForm.role,
      name: user.name || user.username || registerForm.username,
      avatar: user.avatar || '',
      collectedCourses: user.collectedCourses || []
    })
    window.dispatchEvent(new Event('user-updated'))

    ElMessage.success('注册并登录成功')
    const targetRoute = (user.role || registerForm.role) === 'teacher' 
      ? '/teacher/checkin-manage' 
      : '/learning-center'
    router.push(targetRoute)

  } catch (error) {
    ElMessage.error(error?.message || '注册失败，请稍后重试')
  } finally {
    registerLoading.value = false
  }
}

// 跳转到登录页
const goToLogin = () => {
  router.push('/login')
}

// 页面加载时初始化
onMounted(() => {
  const u = getCurrentUser()
  if (!u) return
  router.push(u?.role === 'teacher' ? '/teacher/checkin-manage' : '/learning-center')
})
</script>

<style scoped>
.register-page {
  min-height: 100vh;
  background: linear-gradient(135deg, #f5f7fa 0%, #e4edf5 100%);
  display: flex;
  flex-direction: column;
  font-family: "Microsoft YaHei", sans-serif;
}

.register-container {
  flex: 1;
  display: flex;
  justify-content: center;
  align-items: center;
  max-width: 1200px;
  margin: 0 auto;
  padding: 40px 20px;
  gap: 0;
}

.register-banner {
  flex: 1;
  height: 600px;
  background: linear-gradient(135deg, #764ba2 0%, #667eea 100%);
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

.register-form-wrapper {
  flex: 1;
  height: 600px;
  background: #fff;
  border-radius: 0 12px 12px 0;
  padding: 60px;
  display: flex;
  flex-direction: column;
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.1);
}

.register-header {
  margin-bottom: 40px;
  text-align: center;
}

.register-header h2 {
  font-size: 32px;
  color: #2c3e50;
  margin-bottom: 10px;
  font-weight: 600;
}

.register-header p {
  font-size: 14px;
  color: #666;
}

.register-form {
  width: 100%;
  max-width: 400px;
  margin: 0 auto;
}

.role-group {
  width: 100%;
  display: flex;
  justify-content: space-between;
}

.form-actions {
  margin-bottom: 20px;
}

.agreement-link {
  color: #4096ff;
  text-decoration: none;
  margin: 0 5px;
}

.register-btn {
  width: 100%;
  height: 48px;
  font-size: 16px;
}

.login-link {
  text-align: center;
  margin-top: 20px;
  font-size: 14px;
  color: #666;
}

.register-footer {
  text-align: center;
  padding: 20px;
  font-size: 14px;
  color: #999;
  background: #fff;
}

@media (max-width: 768px) {
  .register-container {
    flex-direction: column;
  }

  .register-banner {
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

  .register-form-wrapper {
    width: 100%;
    height: auto;
    border-radius: 0 0 12px 12px;
    padding: 30px 20px;
  }

  .register-header h2 {
    font-size: 24px;
  }
}
</style>
