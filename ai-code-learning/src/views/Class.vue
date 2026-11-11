<template>
  <div class="class-page" :class="{ teacher: isTeacher }">
    <div class="class-header">
      <h1>班级</h1>
      <p>学生加入班级后可接收教师发布的打卡任务；教师创建班级后可管理学生与任务。</p>
    </div>

    <div v-if="!isLogin" class="need-login">
      <el-empty description="请先登录后再使用班级功能" />
      <el-button type="primary" @click="goLogin">去登录</el-button>
    </div>

    <div v-else class="class-grid">
      <el-card class="card">
        <template #header>
          <div class="card-title">加入班级</div>
        </template>
        <el-form @submit.prevent>
          <el-form-item>
            <el-input v-model="joinCode" placeholder="输入班级码（老师创建后提供）" />
          </el-form-item>
          <el-button type="primary" :loading="joining" :disabled="isTeacher || joining || !hasToken" @click="joinClass">加入</el-button>
          <div v-if="isTeacher" class="tip">教师账号不可加入班级</div>
          <div v-else-if="!hasToken" class="tip">请先登录后再加入班级</div>
        </el-form>
      </el-card>

      <el-card class="card">
        <template #header>
          <div class="card-title">创建班级</div>
        </template>
        <el-form @submit.prevent>
          <el-form-item>
            <el-input v-model="className" placeholder="输入班级名称（例如：高一(1)班）" />
          </el-form-item>
          <el-button type="primary" :loading="creating" :disabled="!isTeacher || creating || !hasToken" @click="createClass">创建</el-button>
          <div v-if="!isTeacher" class="tip">学生账号不可创建班级</div>
          <div v-else-if="!hasToken" class="tip">请先登录后再创建班级</div>
        </el-form>
      </el-card>
    </div>

    <el-card v-if="isLogin" class="list-card" v-loading="listLoading">
      <template #header>
        <div class="list-header">
          <div class="card-title">{{ isTeacher ? '我创建的班级' : '我加入的班级' }}</div>
          <el-button plain size="small" :loading="listLoading" :disabled="listLoading" @click="loadMine">刷新</el-button>
        </div>
      </template>
      <el-skeleton v-if="listLoading && classes.length === 0" :rows="4" animated />
      <el-empty v-else-if="classes.length === 0" description="暂无班级" />
      <el-table v-else :data="classes" stripe style="width: 100%">
        <el-table-column prop="name" label="班级名称" min-width="200" />
        <el-table-column prop="code" label="班级码" min-width="140" />
        <el-table-column width="140" label="操作">
          <template #default="{ row }">
            <el-button size="small" @click="copyCode(row.code)">复制班级码</el-button>
            <el-button
              v-if="isTeacher"
              size="small"
              type="danger"
              :disabled="operating"
              @click="dissolveClass(row)"
            >解散</el-button>
            <el-button
              v-else
              size="small"
              type="warning"
              :disabled="operating"
              @click="leaveClass(row)"
            >退出</el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <WhitespaceGame scene="team" game="puzzle" />
  </div>
</template>

<script setup>
import WhitespaceGame from '@/components/WhitespaceGame.vue'
import { computed, onBeforeUnmount, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { getAuthToken, getCurrentUser, setCurrentUser } from '@/utils/authStorage'

const router = useRouter()

const joinCode = ref('')
const className = ref('')
const classes = ref([])
const creating = ref(false)
const joining = ref(false)
const operating = ref(false)
const listLoading = ref(false)

const userInfo = ref(getCurrentUser())
const isLogin = computed(() => !!userInfo.value?.id)
const isTeacher = computed(() => String(userInfo.value?.role || '') === 'teacher')
const userId = computed(() => userInfo.value?.id || 'guest')
const tokenValue = ref(getAuthToken())
const hasToken = computed(() => !!tokenValue.value)
const classMineCacheKey = computed(() => `classMineCache_${userId.value}_${String(userInfo.value?.role || 'unknown')}`)

const token = () => getAuthToken()

const goLogin = () => router.push('/login')

const syncMe = async () => {
  const t = token()
  if (!t) return
  const res = await fetch('/api/auth/me', {
    headers: { Authorization: `Bearer ${t}` }
  }).catch(() => null)
  const data = res ? await res.json().catch(() => ({})) : {}
  if (!res || !res.ok || data?.success === false || !data?.user?.id) return
  const u = data.user
  setCurrentUser({
    id: u.id,
    role: u.role || 'student',
    name: u.name || u.username || '',
    avatar: u.avatar || '',
    collectedCourses: u.collectedCourses || []
  })
  userInfo.value = getCurrentUser()
  tokenValue.value = getAuthToken()
}

const loadMine = async () => {
  const t = token()
  if (!t) return
  if (listLoading.value) return
  listLoading.value = true
  try {
    const res = await fetch('/api/classes/mine', {
      headers: { Authorization: `Bearer ${t}` }
    }).catch(() => null)
    const data = res ? await res.json().catch(() => ({})) : {}
    if (!res || !res.ok || data?.success === false) {
      ElMessage.error(data?.detail || data?.message || '加载班级失败')
      return
    }
    classes.value = Array.isArray(data?.classes) ? data.classes : []
    try {
      sessionStorage.setItem(classMineCacheKey.value, JSON.stringify(classes.value))
    } catch {}
  } finally {
    listLoading.value = false
  }
}

const joinClass = async () => {
  if (joining.value) return
  const t = token()
  if (!t) {
    ElMessage.warning('请先登录')
    return
  }
  const code = joinCode.value.trim()
  if (!code) {
    ElMessage.warning('请输入班级码')
    return
  }
  joining.value = true
  try {
    const res = await fetch('/api/classes/join', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        Authorization: `Bearer ${t}`
      },
      body: JSON.stringify({ code })
    })
    const data = await res.json().catch(() => ({}))
    if (!res.ok || data?.success === false) {
      const detail = data?.detail || data?.message || '加入失败'
      if (String(detail).includes('需要学生权限')) {
        ElMessage.error('当前账号不是学生账号，无法加入班级')
      } else {
        ElMessage.error(detail)
      }
      return
    }
    ElMessage.success('加入成功')
    joinCode.value = ''
    await loadMine()
  } catch {
    ElMessage.error('加入失败：网络异常')
  } finally {
    joining.value = false
  }
}

const createClass = async () => {
  if (creating.value) return
  const t = token()
  if (!t) {
    ElMessage.warning('请先登录')
    return
  }
  const name = className.value.trim()
  if (!name) {
    ElMessage.warning('请输入班级名称')
    return
  }
  creating.value = true
  try {
    const res = await fetch('/api/classes/create', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        Authorization: `Bearer ${t}`
      },
      body: JSON.stringify({ name })
    })
    const data = await res.json().catch(() => ({}))
    if (!res.ok || data?.success === false) {
      const detail = data?.detail || data?.message || '创建失败'
      if (String(detail).includes('需要教师权限')) {
        ElMessage.error('当前账号在数据库中仍是学生角色，无法创建班级。请用“我是老师”重新注册/登录教师账号')
      } else {
        ElMessage.error(detail)
      }
      return
    }
    ElMessage.success(`创建成功，班级码：${data?.class?.code || ''}`)
    className.value = ''
    await loadMine()
  } catch {
    ElMessage.error('创建失败：网络异常')
  } finally {
    creating.value = false
  }
}

const copyCode = async (code) => {
  try {
    await navigator.clipboard.writeText(String(code || ''))
    ElMessage.success('已复制')
  } catch {
    ElMessage.warning('复制失败，请手动复制')
  }
}

const leaveClass = async (row) => {
  const t = token()
  if (!t) {
    ElMessage.warning('请先登录')
    return
  }
  if (operating.value) return
  try {
    await ElMessageBox.confirm(
      `确认退出班级「${row?.name || ''}」？退出后将无法收到该班级任务。`,
      '退出班级',
      {
        confirmButtonText: '确认退出',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )
  } catch {
    return
  }
  operating.value = true
  try {
    const res = await fetch('/api/classes/leave', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        Authorization: `Bearer ${t}`
      },
      body: JSON.stringify({ class_id: row?.id })
    })
    if (res.status === 404) {
      ElMessage.error('接口不存在：请确认后端已更新并重启（backend_new.py，端口 3002）')
      return
    }
    const data = await res.json().catch(() => ({}))
    if (!res.ok || data?.success === false) {
      ElMessage.error(data?.detail || data?.message || '退出失败')
      return
    }
    ElMessage.success('已退出班级')
    await loadMine()
  } catch {
    ElMessage.error('退出失败：网络异常')
  } finally {
    operating.value = false
  }
}

const dissolveClass = async (row) => {
  const t = token()
  if (!t) {
    ElMessage.warning('请先登录')
    return
  }
  if (operating.value) return
  try {
    await ElMessageBox.confirm(
      `确认解散班级「${row?.name || ''}」？该班级成员与任务将被清空，且不可恢复。`,
      '解散班级',
      {
        confirmButtonText: '确认解散',
        cancelButtonText: '取消',
        type: 'error'
      }
    )
  } catch {
    return
  }
  operating.value = true
  try {
    const res = await fetch('/api/classes/dissolve', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        Authorization: `Bearer ${t}`
      },
      body: JSON.stringify({ class_id: row?.id })
    })
    if (res.status === 404) {
      ElMessage.error('接口不存在：请确认后端已更新并重启（backend_new.py，端口 3002）')
      return
    }
    const data = await res.json().catch(() => ({}))
    if (!res.ok || data?.success === false) {
      ElMessage.error(data?.detail || data?.message || '解散失败')
      return
    }
    ElMessage.success('班级已解散')
    await loadMine()
  } catch {
    ElMessage.error('解散失败：网络异常')
  } finally {
    operating.value = false
  }
}

const tryLoadCachedMine = () => {
  try {
    const raw = sessionStorage.getItem(classMineCacheKey.value)
    const cached = raw ? JSON.parse(raw) : null
    if (Array.isArray(cached)) classes.value = cached
  } catch {}
}

const onUserUpdated = () => {
  userInfo.value = getCurrentUser()
  tokenValue.value = getAuthToken()
  tryLoadCachedMine()
  syncMe().finally(() => loadMine())
}

onMounted(() => {
  window.addEventListener('user-updated', onUserUpdated)
  tokenValue.value = getAuthToken()
  tryLoadCachedMine()
  syncMe().finally(() => loadMine())
})

onBeforeUnmount(() => {
  window.removeEventListener('user-updated', onUserUpdated)
})
</script>

<style scoped>
.class-page {
  max-width: 1200px;
  margin: 0 auto;
  padding: 24px;
}

.class-page.teacher {
  background: linear-gradient(135deg, rgba(43, 27, 79, 0.08), rgba(58, 28, 122, 0.08));
  border-radius: 14px;
}

.class-header h1 {
  margin: 0 0 8px;
}

.class-header p {
  margin: 0 0 18px;
  color: #555;
}

.class-grid {
  display: grid;
  grid-template-columns: 1fr;
  gap: 16px;
  margin-bottom: 16px;
}

.card-title {
  font-weight: 800;
}

.list-card {
  margin-top: 8px;
}

.list-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
}

.tip {
  margin-top: 10px;
  color: #888;
  font-size: 12px;
}

.need-login {
  margin-top: 16px;
  display: grid;
  gap: 12px;
  justify-items: center;
}

@media (max-width: 900px) {
  .class-page {
    padding: 18px;
  }
}
</style>
