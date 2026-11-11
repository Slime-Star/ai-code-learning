<template>
  <div class="teacher-page">
    <div class="header teacher-hero"><div><span class="teacher-eyebrow">A PLACE TO LEARN TOGETHER</span>
      <h1>班级管理</h1>
      <p>查看你创建的班级与当前学生人数。</p>
    </div><TeacherScene scene="pipeline" /></div>

    <div class="toolbar">
      <el-button plain :loading="loading" :disabled="loading" @click="refreshSummary">刷新</el-button>
    </div>

    <el-card class="card" v-loading="loading">
      <el-empty v-if="classes.length === 0" description="暂无班级" />
      <el-table v-else :data="classes" stripe style="width: 100%">
        <el-table-column prop="name" label="班级名称" min-width="220" />
        <el-table-column prop="code" label="班级码" width="140" />
        <el-table-column prop="studentCount" label="学生人数" width="120" />
        <el-table-column prop="createdAt" label="创建时间" min-width="180">
          <template #default="{ row }">
            {{ formatDateTime(row.createdAt) }}
          </template>
        </el-table-column>
        <el-table-column label="班级教学" min-width="180"><template #default="{row}"><el-button link type="primary" @click="router.push({path:'/teacher/workbench/student-data',query:{class_id:row.id}})">学生档案</el-button><el-button link type="primary" @click="router.push({path:'/teacher/checkin-manage',query:{class_id:row.id}})">打卡情况</el-button></template></el-table-column>
      </el-table>
    </el-card>
    <TopicArt scene="team" inverse />
  </div>
</template>

<script setup>
import TopicArt from '@/components/TopicArt.vue'
import TeacherScene from '@/components/TeacherScene.vue'
import {useRouter} from 'vue-router'
import {teacherStorageKey} from '@/utils/teacherApi'
import { onMounted, ref } from 'vue'
import { ElMessage } from 'element-plus'
import { getAuthToken } from '@/utils/authStorage'

const classes = ref([])
const router=useRouter()
const loading = ref(false)

const token = () => getAuthToken()

const cacheKey = () => teacherStorageKey('class-summary')
const now = () => Date.now()
const readCache = () => {
  try {
    const raw = sessionStorage.getItem(cacheKey())
    if (!raw) return null
    return JSON.parse(raw)
  } catch {
    return null
  }
}
const writeCache = (v) => {
  try {
    sessionStorage.setItem(cacheKey(), JSON.stringify(v))
  } catch {}
}

const maxAgeMs = 60_000

const formatDateTime = (raw) => {
  const s = String(raw || '')
  if (!s) return '—'
  const d = new Date(s)
  if (Number.isNaN(d.getTime())) return s
  return d.toLocaleString()
}

const loadSummary = async ({ silent } = { silent: false }) => {
  const t = token()
  if (!t) return
  const cached = readCache()
  if (cached?.data && Array.isArray(cached.data) && now() - Number(cached.at || 0) < maxAgeMs) {
    classes.value = cached.data
    if (!silent) return
  }
  if (loading.value) return
  loading.value = !cached || silent
  try {
    const res = await fetch('/api/teacher/classes/summary', {
      headers: { Authorization: `Bearer ${t}` }
    }).catch(() => null)
    const data = res ? await res.json().catch(() => ({})) : {}
    if (!res || !res.ok || data?.success === false) {
      ElMessage.error(data?.detail || data?.message || '加载班级失败')
      classes.value = []
      return
    }
    classes.value = Array.isArray(data?.classes) ? data.classes : []
    writeCache({ at: now(), data: classes.value })
  } finally {
    loading.value = false
  }
}

const refreshSummary = () => {
  loadSummary({ silent: true })
}

onMounted(() => {
  loadSummary()
})
</script>

<style scoped>
.teacher-page {
  max-width: 1200px;
  margin: 0 auto;
  padding: 24px;
  min-height: calc(100vh - 60px);
  background: linear-gradient(135deg, #1f1538 0%, #2b1b4f 60%, #3a1c7a 100%);
  border-radius: 14px;
}

.header h1 {
  margin: 0 0 8px;
  color: #fff;
}

.header p {
  margin: 0 0 18px;
  color: rgba(255, 255, 255, 0.75);
}

.toolbar {
  display: flex;
  justify-content: flex-end;
  margin-bottom: 14px;
}

.card {
  background: rgba(255, 255, 255, 0.92);
  border-radius: 12px;
}
</style>
