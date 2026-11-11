<template>
  <div class="teacher-page">
    <header class="teacher-hero"><div><span class="teacher-eyebrow">KNOW YOUR STUDENTS</span><h1>学生数据</h1><p>把提交记录变成教学线索。点击学生头像，查看知识点分布与学习建议。</p></div><TeacherScene scene="data" /></header>
    <div class="teacher-metrics"><div class="teacher-metric"><span>班级学生</span><strong><AnimatedNumber :value="students.length" :animate="!loading" /></strong><small>{{ selectedClassName || '请先选择班级' }}</small></div><div class="teacher-metric"><span>总提交次数</span><strong><AnimatedNumber :value="totalRuns" :animate="!loading" /></strong><small>当前班级累计提交</small></div><div class="teacher-metric"><span>整体正确率</span><strong>{{ overallRate }}%</strong><small>通过提交数 / 总提交数</small></div><div class="teacher-metric"><span>有薄弱点记录</span><strong><AnimatedNumber :value="students.filter(s=>s.weakTopics?.length).length" :animate="!loading" /></strong><small>点击学生查看需要巩固的内容</small></div></div>
    <el-alert v-if="error" class="teacher-error" :title="error" type="error" :closable="false" show-icon />
    <div class="teacher-toolbar"><el-select v-model="selectedClassId" placeholder="选择班级" aria-label="选择班级"><el-option v-for="c in myClasses" :key="c.id" :label="`${c.name}（${c.code}）`" :value="String(c.id)" /></el-select><el-input v-model="query" placeholder="搜索学生或薄弱知识点" clearable aria-label="搜索学生或薄弱知识点" /><el-button plain :loading="loading" @click="loadStudents(true)">刷新</el-button><el-button plain @click="goToGraph">查看班级图谱 ↗</el-button></div>
    <el-card class="card" v-loading="loading">
      <el-table v-if="filteredStudents.length" :data="pageStudents" stripe row-key="id">
        <el-table-column label="学生" min-width="220"><template #default="{row}"><button class="student-cell" @click="openStudent(row,$event)"><span class="student-avatar"><img v-if="row.avatar" :src="row.avatar" alt="" /><template v-else>{{ (row.name || row.username || '同').slice(0,1) }}</template></span><span class="student-info"><strong>{{ row.name }}</strong><small>@{{ row.username }}</small></span><span class="student-open">↗</span></button></template></el-table-column>
        <el-table-column label="正确率" width="150"><template #default="{row}"><div class="rate-cell"><span>{{ formatRate(row.stats?.success_rate) }}</span><el-progress :percentage="Math.min(100,Math.max(0,Number(row.stats?.success_rate)||0))" :show-text="false" :stroke-width="5" color="#aa8bc9" /></div></template></el-table-column>
        <el-table-column label="提交次数" width="110"><template #default="{row}">{{ row.stats?.total_submissions || 0 }}</template></el-table-column><el-table-column label="尝试题目" width="110"><template #default="{row}">{{ row.stats?.problems_attempted || 0 }}</template></el-table-column>
        <el-table-column label="薄弱知识点" min-width="240"><template #default="{row}"><div class="weak-tags"><el-tag v-for="item in (row.weakTopics || []).slice(0,3)" :key="item.topic" type="warning" size="small">{{ item.topic }}</el-tag><span v-if="!row.weakTopics?.length">—</span></div></template></el-table-column>
        <el-table-column label="学习档案" width="130"><template #default="{row}"><el-button size="small" @click="openStudent(row,$event,true)">AI 分析</el-button></template></el-table-column>
      </el-table>
      <el-empty v-else :description="loading?'正在加载学生数据':error?'数据暂时不可用':query?'没有匹配的学生':'当前班级暂无学生'" :image-size="85" />
      <div class="teacher-table-footer"><span>共 {{ filteredStudents.length }} 位学生{{ students.length>=300?'（本次最多加载 300 位）':'' }}</span><el-pagination v-if="filteredStudents.length>12" v-model:current-page="page" :page-size="12" :total="filteredStudents.length" layout="prev,pager,next" /></div>
    </el-card>
    <TeacherStudentDrawer v-model="detailVisible" :student="detailStudent" :origin="detailOrigin" :auto-analyze="autoAnalyze" />
    <TopicArt scene="data" inverse />
  </div>
</template>
<script setup>
import {computed,onMounted,onBeforeUnmount,ref,shallowRef,watch} from 'vue'
import {useRouter,useRoute} from 'vue-router'
import TopicArt from '@/components/TopicArt.vue'
import TeacherScene from '@/components/TeacherScene.vue'
import TeacherStudentDrawer from '@/components/TeacherStudentDrawer.vue'
import AnimatedNumber from '@/components/AnimatedNumber.vue'
import {teacherGet,readTeacherState,writeTeacherState} from '@/utils/teacherApi'
const router=useRouter(),route=useRoute(),saved=readTeacherState('students-view',{})
const myClasses=ref([]),selectedClassId=ref(String(route.query.class_id || saved.classId || '')),students=ref([]),loading=ref(false),error=ref(''),query=ref(saved.query || ''),page=ref(saved.page || 1)
const detailVisible=ref(false),detailStudent=ref(null),detailOrigin=shallowRef(null),autoAnalyze=ref(false)
const selectedClassName=computed(()=>myClasses.value.find(c=>String(c.id)===selectedClassId.value)?.name || '')
const totalRuns=computed(()=>students.value.reduce((sum,s)=>sum+Number(s.stats?.total_submissions || 0),0)),overallRate=computed(()=>totalRuns.value?(students.value.reduce((sum,s)=>sum+Number(s.stats?.success_count || 0),0)/totalRuns.value*100).toFixed(1):'0.0')
const filteredStudents=computed(()=>students.value.filter(s=>`${s.name} ${s.username} ${(s.weakTopics || []).map(t=>t.topic).join(' ')}`.toLocaleLowerCase().includes(query.value.trim().toLocaleLowerCase()))),pageStudents=computed(()=>filteredStudents.value.slice((page.value-1)*12,page.value*12))
const formatRate=value=>`${(Number(value)||0).toFixed(1)}%`
let controller,disposed=false,ready=false
async function loadStudents(force=false){
  controller?.abort();if(!selectedClassId.value){students.value=[];return}
  controller=new AbortController();const current=controller,classId=selectedClassId.value,cached=readTeacherState(`students-${classId}`)
  error.value='';detailVisible.value=false
  if(!force && cached?.at>Date.now()-60000){students.value=cached.data;loading.value=false;return}
  loading.value=true;students.value=[]
  try{const data=await teacherGet(`/api/teacher/classes/students?class_id=${encodeURIComponent(classId)}&limit=300`,{signal:current.signal});if(current.signal.aborted || disposed)return;students.value=data.students || [];writeTeacherState(`students-${classId}`,{at:Date.now(),data:students.value})}catch(e){if(!current.signal.aborted)error.value=e.message}finally{if(current===controller)loading.value=false}
}
function openStudent(row,event,analyze=false){detailOrigin.value=event.currentTarget.closest('tr')?.querySelector('.student-avatar');detailStudent.value={...row,className:selectedClassName.value};autoAnalyze.value=analyze;detailVisible.value=true}
function goToGraph(){router.push({path:'/teacher/workbench/learning-center',query:{class_id:selectedClassId.value}})}
watch(selectedClassId,()=>{if(ready){page.value=1;loadStudents()}})
watch(query,()=>page.value=1)
watch([selectedClassId,query,page],()=>writeTeacherState('students-view',{classId:selectedClassId.value,query:query.value,page:page.value}))
watch(()=>filteredStudents.value.length,length=>{if(!loading.value)page.value=Math.min(page.value,Math.max(1,Math.ceil(length/12)))})
onMounted(async()=>{try{const data=await teacherGet('/api/classes/mine');if(disposed)return;myClasses.value=data.classes || [];if(!myClasses.value.some(c=>String(c.id)===selectedClassId.value))selectedClassId.value=String(myClasses.value[0]?.id || '');ready=true;await loadStudents()}catch(e){if(!disposed)error.value=e.message}})
onBeforeUnmount(()=>{disposed=true;controller?.abort()})
</script>
<style scoped>
.teacher-page{max-width:1200px;margin:0 auto;padding:24px;min-height:calc(100vh - 60px);background:linear-gradient(135deg,#1f1538,#2b1b4f 60%,#3a1c7a);border-radius:14px}.card{background:#faf8fd}.student-cell{display:flex;align-items:center;gap:10px;width:100%;border:0;background:none;font:inherit;text-align:left;cursor:pointer;padding:4px;color:#49345e}.student-avatar{width:36px;height:36px;display:grid;place-items:center;flex-shrink:0;border-radius:50%;overflow:hidden;color:#84649d;background:linear-gradient(130deg,#e5d6f7,#d3e6e2)}.student-avatar img{width:100%;height:100%;object-fit:cover}.student-info{display:grid;gap:4px}.student-info strong{font-size:13px}.student-info small{font-size:11px;color:#a38daf}.student-open{margin-left:auto;opacity:0;translate:-6px 0;transition:opacity .2s,translate .2s}.student-cell:hover .student-open,.student-cell:focus-visible .student-open{opacity:1;translate:0 0}.weak-tags{display:flex;flex-wrap:wrap;gap:5px}.rate-cell{display:grid;gap:7px;font-size:12px;max-width:100px}
</style>
