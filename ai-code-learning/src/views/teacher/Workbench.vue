<template>
  <div class="teacher-page workbench-page">
    <header class="teacher-hero"><div><span class="teacher-eyebrow">TEACH · INSPIRE · GROW</span><h1>{{ teacherName }}，开始今天的教学</h1><p>从班级动态到学生反馈，把需要关注的事情放在眼前。</p><div class="teacher-quick-actions"><el-button type="primary" @click="go('/teacher/create-task')">＋ 发布练习</el-button><el-button plain @click="go('/teacher/workbench/competition-manage')">管理班级测试</el-button><el-button text :loading="loading" @click="loadOverview">刷新概览</el-button></div></div><TeacherScene scene="pipeline" /></header>
    <el-alert v-if="errors.length" class="teacher-error" :title="errors.join('；')" type="warning" :closable="false" show-icon />
    <div class="teacher-metrics" :aria-busy="loading">
      <button class="teacher-metric" @click="go('/teacher/workbench/class-manage')"><span>我的班级</span><strong><AnimatedNumber v-if="classes!==null" :value="classes.length" animate /><template v-else>—</template></strong><small>{{ studentCount===null?'等待加载':`${studentCount} 位学生（跨班级去重）` }}</small></button>
      <button class="teacher-metric" @click="go('/teacher/checkin-manage')"><span>今日打卡率</span><strong>{{ checkinRate===null?'—':checkinRate+'%' }}</strong><small>{{ checkedCount===null?'等待加载':`${checkedCount} 位已打卡 · 查看名单 ↗` }}</small></button>
      <button class="teacher-metric" @click="go('/teacher/workbench/competition-manage?review=pending')"><span>待批改提交</span><strong><AnimatedNumber v-if="pendingCount!==null" :value="pendingCount" animate /><template v-else>—</template></strong><small>本人发布测试的已提交答卷</small></button>
      <button class="teacher-metric" @click="go('/teacher/workbench/task-manage?due=soon')"><span>即将截止</span><strong><AnimatedNumber v-if="tasks!==null" :value="upcomingTasks.length" animate /><template v-else>—</template></strong><small>未来 7 天内的练习任务</small></button>
    </div>
    <div class="overview-columns">
      <el-card class="overview-card"><div class="teacher-panel-title"><div><h2>班级打卡动态</h2><p>{{ today }} · 北京时间</p></div><el-button link type="primary" @click="go('/teacher/checkin-manage?status=pending')">查看未打卡 →</el-button></div>
        <el-skeleton v-if="loading && statusRows===null" :rows="3" animated />
        <template v-else-if="statusRows!==null && classProgress.length"><button v-for="item in classProgress" :key="item.id" class="class-progress" @click="go(`/teacher/checkin-manage?class_id=${encodeURIComponent(item.id)}`)"><div><strong>{{ item.name }}</strong><span>{{ item.done }} / {{ item.total }} 人</span></div><el-progress :percentage="item.rate" :stroke-width="7" :show-text="false" color="#a98acb" /></button></template>
        <el-empty v-else :description="statusRows===null?'打卡数据暂时不可用':'暂无班级打卡记录'" :image-size="70" />
      </el-card>
      <el-card class="overview-card"><div class="teacher-panel-title"><div><h2>近期教学安排</h2><p>按截止时间排序</p></div><el-button link type="primary" @click="go('/teacher/workbench/task-manage')">全部任务 →</el-button></div>
        <el-skeleton v-if="loading && tasks===null" :rows="3" animated />
        <button v-for="task in upcomingTasks.slice(0,5)" :key="task.id" class="upcoming-task" @click="go(`/teacher/workbench/task-manage?task_id=${encodeURIComponent(task.id)}`)"><span class="task-date">{{ new Date(task.dueAt).toLocaleDateString('zh-CN',{month:'2-digit',day:'2-digit'}) }}</span><span><strong>{{ task.title }}</strong><small>{{ task.class_name }} · {{ task.language }}</small></span><span class="task-arrow">↗</span></button>
        <el-empty v-if="!loading && !upcomingTasks.length" :description="tasks===null?'任务数据暂时不可用':'未来 7 天没有即将截止的任务'" :image-size="70" />
      </el-card>
    </div>
    <nav class="teaching-entries" aria-label="教师管理入口"><router-link v-for="item in entries" :key="item.path" :to="item.path"><span class="entry-symbol">{{ item.symbol }}</span><div><strong>{{ item.title }}</strong><p>{{ item.desc }}</p></div><span>↗</span></router-link></nav>
    <TopicArt scene="pipeline" inverse />
  </div>
</template>
<script setup>
import { computed, onMounted, onBeforeUnmount, ref } from 'vue'
import { useRouter } from 'vue-router'
import TopicArt from '@/components/TopicArt.vue'
import TeacherScene from '@/components/TeacherScene.vue'
import AnimatedNumber from '@/components/AnimatedNumber.vue'
import { getCurrentUser } from '@/utils/authStorage'
import { getStudyDateKey } from '@/utils/studyDate'
import { teacherGet, isUngraded } from '@/utils/teacherApi'
const router=useRouter(),go=path=>router.push(path),teacherName=getCurrentUser()?.name || '老师'
const classes=ref(null),statusRows=ref(null),tasks=ref(null),pendingCount=ref(null),loading=ref(false),errors=ref([]),clock=ref(new Date())
const today=computed(()=>getStudyDateKey(clock.value)),uniqueStudents=computed(()=>statusRows.value ? [...new Map(statusRows.value.map(row=>[row.student_id,row])).values()] : null)
const studentCount=computed(()=>uniqueStudents.value?.length ?? null),checkedCount=computed(()=>uniqueStudents.value?.filter(row=>row.last===today.value).length ?? null)
const checkinRate=computed(()=>studentCount.value===null?null:studentCount.value?Math.round(checkedCount.value/studentCount.value*100):0)
const upcomingTasks=computed(()=> (tasks.value || []).filter(task=>{const remaining=Date.parse(task.dueAt)-clock.value.getTime();return remaining>0 && remaining<=7*86400000}).sort((a,b)=>Date.parse(a.dueAt)-Date.parse(b.dueAt)))
const classProgress=computed(()=>(classes.value || []).map(c=>{const rows=(statusRows.value || []).filter(row=>String(row.class_id)===String(c.id)),done=rows.filter(row=>row.last===today.value).length;return {...c,total:rows.length,done,rate:rows.length?Math.round(done/rows.length*100):0}}))
const entries=[{path:'/teacher/workbench/class-manage',symbol:'⌘',title:'班级管理',desc:'班级与学生成员'},{path:'/teacher/workbench/student-data',symbol:'↗',title:'学生数据',desc:'学习表现与薄弱知识点'},{path:'/teacher/workbench/learning-center',symbol:'◎',title:'教学分析',desc:'班级图谱与错误分布'},{path:'/teacher/workbench/task-manage',symbol:'</>',title:'题目管理',desc:'已发布任务与参考答案'}]
let controller,timer
async function loadOverview(){
  if(loading.value)return
  loading.value=true;errors.value=[];controller=new AbortController()
  try{
    const results=await Promise.allSettled(['/api/teacher/classes/summary','/api/teacher/checkin-status','/api/teacher/tasks','/api/teacher/competitions'].map(path=>teacherGet(path,{signal:controller.signal})))
    if(controller.signal.aborted)return
    const refs=[classes,statusRows,tasks],fields=['classes','students','tasks'],names=['班级','打卡','任务','测试']
    results.forEach((result,index)=>{if(result.status==='fulfilled'){if(index<3)refs[index].value=result.value[fields[index]] || []}else errors.value.push(`${names[index]}数据加载失败`)})
    if(results[3].status==='fulfilled'){
      const owned=(results[3].value.data || []).filter(comp=>String(comp.teacherId)===String(getCurrentUser()?.id) && comp.problemCount>0)
      let count=0,failed=false,index=0
      await Promise.all(Array.from({length:Math.min(3,owned.length)},async()=>{while(index<owned.length && !controller.signal.aborted){const comp=owned[index++];try{const result=await teacherGet(`/api/teacher/competitions/${comp.id}/submissions`,{signal:controller.signal});count+=(result.submissions || []).filter(isUngraded).length}catch{failed=true}}}))
      if(!controller.signal.aborted){pendingCount.value=failed?null:count;if(failed)errors.value.push('部分待批改数据暂时不可用')}
    }else pendingCount.value=null
  }finally{loading.value=false}
}
onMounted(()=>{loadOverview();timer=setInterval(()=>clock.value=new Date(),60000)})
onBeforeUnmount(()=>{controller?.abort();clearInterval(timer)})
</script>
<style scoped>
.teacher-page{max-width:1200px;margin:0 auto;padding:24px;min-height:calc(100vh - 60px);background:linear-gradient(135deg,#1f1538,#2b1b4f 60%,#3a1c7a);color:#fff;border-radius:14px}.overview-columns{display:grid;grid-template-columns:1fr 1fr;gap:18px}.overview-card{background:#faf8fd;color:#382b4a;border:0}.class-progress{display:block;width:100%;border:0;background:none;text-align:left;padding:12px 0;font:inherit;cursor:pointer}.class-progress>div:first-child{display:flex;justify-content:space-between;margin-bottom:10px;font-size:13px}.class-progress span{font-size:12px;color:#9a89ac}.upcoming-task{display:flex;gap:12px;align-items:center;width:100%;text-align:left;padding:14px 0;border:0;border-bottom:1px solid #ece5f2;background:none;font:inherit;color:#49385e;cursor:pointer}.task-date{font:12px Consolas,monospace;padding:12px 8px;background:#eee6f6;border-radius:10px;color:#8d6bab}.upcoming-task strong{font-size:13px}.upcoming-task small{display:block;font-size:11px;color:#9988aa;margin-top:5px}.task-arrow{margin-left:auto;color:#9d7cba}.teaching-entries{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:14px;margin-top:22px}.teaching-entries a{display:flex;align-items:center;gap:12px;padding:20px 14px;color:#e7d9f9;text-decoration:none;background:#ffffff08;border:1px solid #d9bfff22;border-radius:14px;transition:translate .25s,background .25s}.teaching-entries a:hover{translate:0 -5px;background:#ffffff14}.teaching-entries strong{font-size:14px}.teaching-entries p{font-size:11px;color:#c5afd8;margin:6px 0 0}.entry-symbol{font:20px Consolas,monospace;color:#beebdb}.teaching-entries a>span:last-child{margin-left:auto}@media(max-width:900px){.teaching-entries{grid-template-columns:1fr 1fr}}@media(max-width:700px){.overview-columns{grid-template-columns:1fr}}
</style>
