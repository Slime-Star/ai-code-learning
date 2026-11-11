<template>
  <div class="teacher-page">
    <div class="header teacher-hero"><div><span class="teacher-eyebrow">A LIBRARY OF YOUR LESSONS</span>
      <h1>题目管理</h1>
      <p>查看你已发布到各班级的打卡任务。</p>
    </div><TeacherScene scene="draft" /></div>

    <div class="toolbar">
      <el-select v-model="selectedClassId" placeholder="筛选班级（可选）" clearable style="width: 320px" @change="handleClassChange">
        <el-option v-for="c in myClasses" :key="c.id" :label="`${c.name}（${c.code}）`" :value="c.id" />
      </el-select>
      <el-button plain :loading="loading" :disabled="loading" @click="refreshTasks">刷新</el-button>
      <el-button type="primary" @click="goCreate">发布新任务</el-button>
    </div>
    <div class="teacher-toolbar"><el-input v-model="query" placeholder="搜索题目或编程语言" clearable aria-label="搜索题目或编程语言" /><el-checkbox v-model="dueSoon">只看未来 7 天截止的任务</el-checkbox><span class="teacher-status-note">共 {{ filteredTasks.length }} 个任务</span></div>

    <el-card class="card" v-loading="loading">
      <el-empty v-if="filteredTasks.length === 0" :description="query || dueSoon?'没有符合筛选条件的任务':'暂无题目'" />
      <el-table v-else :data="filteredTasks" stripe style="width: 100%" row-key="id">
        <el-table-column prop="class_name" label="班级" min-width="180">
          <template #default="{ row }">
            {{ row.class_name }}（{{ row.class_code }}）
          </template>
        </el-table-column>
        <el-table-column prop="title" label="标题" min-width="220"><template #default="{row}"><span class="task-title-origin">{{ row.title }}</span></template></el-table-column>
        <el-table-column prop="language" label="语言" width="110" />
        <el-table-column prop="dueAt" label="截止" min-width="160">
          <template #default="{ row }">
            {{ formatDateTime(row.dueAt) }}
          </template>
        </el-table-column>
        <el-table-column prop="createdAt" label="创建时间" min-width="170">
          <template #default="{ row }">
            {{ formatDateTime(row.createdAt) }}
          </template>
        </el-table-column>
        <el-table-column label="操作" width="120">
          <template #default="{ row }">
            <el-button size="small" @click="openDetail(row,$event)">查看</el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <el-dialog v-model="detailVisible" title="任务详情" width="min(860px,94vw)" class="teacher-task-dialog" @open="detailMorph.open" @close="detailMorph.close">
      <div v-if="currentTask" class="detail">
        <div ref="detailTarget" class="detail-meta">
          <div class="meta-line"><span class="k">班级：</span>{{ currentTask.class_name }}（{{ currentTask.class_code }}）</div>
          <div class="meta-line"><span class="k">标题：</span>{{ currentTask.title }}</div>
          <div class="meta-line"><span class="k">语言：</span>{{ currentTask.language }}</div>
          <div class="meta-line"><span class="k">截止：</span>{{ formatDateTime(currentTask.dueAt) }}</div>
        </div>
        <div class="detail-section">
          <div class="section-title">题目描述</div>
          <div class="section-body">{{ currentTask.description || '无' }}</div>
        </div>
        <div class="detail-section">
          <div class="section-title">初始代码</div>
          <pre class="code-block">{{ currentTask.starterCode || '' }}</pre>
        </div>
        <div class="detail-section">
          <div class="section-title">预期输出</div>
          <pre class="code-block">{{ currentTask.expectedOutput || '' }}</pre>
        </div>
        <div class="detail-section">
          <div class="section-title">参考答案</div>
          <pre class="code-block">{{ currentTask.solutionCode || '' }}</pre>
        </div>
      </div>
    </el-dialog>
    <TopicArt scene="debug" inverse />
  </div>
</template>

<script setup>
import TopicArt from '@/components/TopicArt.vue'
import TeacherScene from '@/components/TeacherScene.vue'
import { computed, onMounted, onBeforeUnmount, ref, shallowRef, watch } from 'vue'
import { useRouter,useRoute } from 'vue-router'
import {useDialogMorph} from '@/composables/useDialogMorph'
import {teacherGet,teacherStorageKey,readTeacherState,writeTeacherState} from '@/utils/teacherApi'
import { ElMessage } from 'element-plus'
import { getAuthToken } from '@/utils/authStorage'

const router = useRouter()
const route=useRoute(),savedView=readTeacherState('tasks-view',{})
const query=ref(savedView.query || ''),dueSoon=ref(route.query.due==='soon')
const detailOrigin=shallowRef(null),detailTarget=ref(null)
const detailMorph=useDialogMorph({source:()=>detailOrigin.value,target:()=>detailTarget.value,preserveContent:true})

const myClasses = ref([])
const selectedClassId = ref(route.query.task_id?'':savedView.classId || '')
const tasks = ref([])
const filteredTasks=computed(()=>tasks.value.filter(task=>{const remaining=Date.parse(task.dueAt)-Date.now();return `${task.title} ${task.language}`.toLocaleLowerCase().includes(query.value.trim().toLocaleLowerCase()) && (!dueSoon.value || remaining>0 && remaining<=7*86400000)}))
const loading = ref(false)

const detailVisible = ref(false)
const currentTask = ref(null)

const token = () => getAuthToken()

const formatDateTime = (raw) => {
  const s = String(raw || '')
  if (!s) return '—'
  const d = new Date(s)
  if (Number.isNaN(d.getTime())) return s
  return d.toLocaleString()
}

const goCreate = () => {
  router.push('/teacher/create-task')
}

const cacheKey = (suffix) => teacherStorageKey(`task-cache:${suffix}`)
const now = () => Date.now()
const readCache = (k) => {
  try {
    const raw = sessionStorage.getItem(k)
    if (!raw) return null
    return JSON.parse(raw)
  } catch {
    return null
  }
}
const writeCache = (k, v) => {
  try {
    sessionStorage.setItem(k, JSON.stringify(v))
  } catch {}
}

const maxAgeMs = 60_000

const loadClasses = async ({ silent } = { silent: false }) => {
  const t = token()
  if (!t) return
  const cached = readCache(cacheKey('classes'))
  if (cached?.data && Array.isArray(cached.data) && now() - Number(cached.at || 0) < maxAgeMs) {
    myClasses.value = cached.data
    if (!silent) return
  }
  const res = await fetch('/api/classes/mine', {
    headers: { Authorization: `Bearer ${t}` }
  }).catch(() => null)
  const data = res ? await res.json().catch(() => ({})) : {}
  if (!res || !res.ok || data?.success === false) {
    ElMessage.error(data?.detail || data?.message || '加载班级失败')
    return
  }
  myClasses.value = Array.isArray(data?.classes) ? data.classes : []
  writeCache(cacheKey('classes'), { at: now(), data: myClasses.value })
}

let tasksController,disposed=false
const loadTasks = async ({silent=false}={}) => {
  tasksController?.abort();tasksController=new AbortController()
  const current=tasksController,classId=selectedClassId.value,key=cacheKey(`tasks_${classId || 'all'}`),cached=readCache(key)
  if(cached?.data && !silent && now()-Number(cached.at || 0)<maxAgeMs){tasks.value=cached.data;loading.value=false;return}
  loading.value=true
  if(!cached)tasks.value=[]
  try{
    const qs=classId?`?class_id=${encodeURIComponent(classId)}`:''
    const data=await teacherGet(`/api/teacher/tasks${qs}`,{signal:current.signal})
    if(current.signal.aborted || disposed)return
    tasks.value=Array.isArray(data.tasks)?data.tasks:[]
    writeCache(key,{at:now(),data:tasks.value})
  }catch(e){if(!current.signal.aborted && !disposed){ElMessage.error(e.message);tasks.value=[]}}
  finally{if(current===tasksController)loading.value=false}
}
onBeforeUnmount(()=>{disposed=true;tasksController?.abort()})

const openDetail = (row,event) => {
  detailOrigin.value=event?.currentTarget?.closest('tr')?.querySelector('.task-title-origin') || null
  currentTask.value = row || null
  detailVisible.value = true
}

const handleClassChange = () => {
  loadTasks()
}

const refreshTasks = () => {
  loadTasks({ silent: true })
}

watch(selectedClassId, (v) => {
  writeCache(cacheKey('selectedClassId'), { value: String(v || '') })
})
watch([selectedClassId,query],()=>writeTeacherState('tasks-view',{classId:selectedClassId.value,query:query.value}))

onMounted(async () => {
  const selectedCached = readCache(cacheKey('selectedClassId'))
  if (typeof selectedCached?.value === 'string' && !route.query.task_id) selectedClassId.value = selectedCached.value
  await loadClasses()
  if(disposed)return
  if (myClasses.value.length > 0 && selectedClassId.value && !myClasses.value.some((c) => String(c.id) === String(selectedClassId.value))) {
    selectedClassId.value = ''
  }
  await loadTasks()
  if(route.query.task_id){const task=tasks.value.find(t=>String(t.id)===String(route.query.task_id));if(task)openDetail(task)}
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
  gap: 12px;
  align-items: center;
  margin-bottom: 14px;
}

.card {
  background: rgba(255, 255, 255, 0.92);
  border-radius: 12px;
}

.detail {
  display: grid;
  gap: 14px;
}

.detail-meta {
  display: grid;
  gap: 6px;
}

.meta-line .k {
  font-weight: 800;
}

.detail-section {
  display: grid;
  gap: 8px;
}

.section-title {
  font-weight: 800;
}

.section-body {
  white-space: pre-wrap;
  line-height: 1.6;
}

.code-block {
  margin: 0;
  padding: 12px;
  background: #0b1020;
  color: #e5e7eb;
  border-radius: 10px;
  overflow: auto;
  font-family: Consolas, monospace;
  font-size: 13px;
  line-height: 1.55;
}
</style>
