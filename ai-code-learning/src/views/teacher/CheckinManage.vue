<template>
  <div class="teacher-page">
    <header class="teacher-hero"><div><span class="teacher-eyebrow">SMALL STEPS · EVERY DAY</span><h1>打卡管理</h1><p>看见每一份坚持，也及时发现需要关注的学生。{{ todayKey }} · 北京时间</p></div><TeacherScene scene="calendar" /></header>
    <div class="checkin-overview">
      <div class="checkin-ring"><svg viewBox="0 0 120 120" aria-hidden="true"><circle cx="60" cy="60" r="50" /><circle class="ring-value" cx="60" cy="60" r="50" :style="{strokeDashoffset:314.16*(1-rate/100)}" /></svg><strong>{{ loaded?rate+'%':'—' }}<small>今日打卡率</small></strong></div>
      <div class="teacher-metrics"><button class="teacher-metric" @click="status='all'"><span>学生人数</span><strong><AnimatedNumber v-if="loaded" :value="uniqueRows.length" animate /><template v-else>—</template></strong><small>当前班级范围 · 去重人数</small></button><button class="teacher-metric" @click="status='done'"><span>已打卡</span><strong><AnimatedNumber v-if="loaded" :value="checkedCount" animate /><template v-else>—</template></strong><small>查看今天已打卡的学生</small></button><button class="teacher-metric" @click="status='pending'"><span>未打卡</span><strong><AnimatedNumber v-if="loaded" :value="uniqueRows.length-checkedCount" animate /><template v-else>—</template></strong><small>查看需要关注的学生</small></button></div>
    </div>
    <el-alert v-if="error" class="teacher-error" :title="error" type="error" :closable="false" show-icon />
    <div class="teacher-toolbar"><el-select v-model="selectedClassId" placeholder="全部班级" clearable aria-label="筛选班级" @change="loadStatus"><el-option v-for="c in myClasses" :key="c.id" :label="`${c.name}（${c.code}）`" :value="c.id" /></el-select><el-input v-model="query" placeholder="搜索学生姓名或账号" clearable aria-label="搜索学生" /><el-select v-model="status" aria-label="打卡状态"><el-option label="全部状态" value="all" /><el-option label="已打卡" value="done" /><el-option label="未打卡" value="pending" /></el-select><el-button plain :loading="loading" @click="loadStatus">刷新</el-button></div>
    <el-card class="card" v-loading="loading">
      <el-table v-if="filteredRows.length" :data="pageRows" stripe row-key="_key"><el-table-column prop="class_name" label="班级" min-width="160" /><el-table-column prop="student_name" label="学生" min-width="140" /><el-table-column prop="streak" label="连续打卡" width="110" sortable><template #default="{row}">{{ row.streak }} 天</template></el-table-column><el-table-column prop="last" label="最后打卡日期" min-width="140"><template #default="{row}">{{ row.last || '尚未打卡' }}</template></el-table-column><el-table-column label="今日状态" width="120"><template #default="{row}"><el-tag :type="isCheckedToday(row.last)?'success':'info'">{{ isCheckedToday(row.last)?'已打卡':'未打卡' }}</el-tag></template></el-table-column></el-table>
      <el-empty v-else :description="error?'数据加载失败，请点击刷新':loaded?(rows.length?'没有匹配的学生':'当前班级还没有学生'):'正在加载学生数据'" :image-size="90"><el-button v-if="query || status!=='all'" plain @click="query='';status='all'">清除筛选</el-button></el-empty>
      <div class="teacher-table-footer"><span>共 {{ filteredRows.length }} 条班级记录 · 每页 12 条</span><el-pagination v-if="filteredRows.length>12" v-model:current-page="page" :page-size="12" :total="filteredRows.length" layout="prev,pager,next" /></div>
    </el-card>
    <TopicArt scene="calendar" inverse />
  </div>
</template>
<script setup>
import {computed,onMounted,onBeforeUnmount,ref,watch} from 'vue'
import {useRoute} from 'vue-router'
import TopicArt from '@/components/TopicArt.vue'
import TeacherScene from '@/components/TeacherScene.vue'
import AnimatedNumber from '@/components/AnimatedNumber.vue'
import {getStudyDateKey} from '@/utils/studyDate'
import {teacherGet,readTeacherState,writeTeacherState} from '@/utils/teacherApi'
const route=useRoute(),saved=readTeacherState('checkin',{})
const myClasses=ref([]),selectedClassId=ref(String(route.query.class_id || saved.classId || '')),rows=ref([]),query=ref(saved.query || ''),status=ref(['done','pending'].includes(route.query.status)?route.query.status:saved.status || 'all'),page=ref(1),loading=ref(false),loaded=ref(false),error=ref(''),clock=ref(new Date())
const todayKey=computed(()=>getStudyDateKey(clock.value)),isCheckedToday=last=>String(last || '')===todayKey.value
const uniqueRows=computed(()=>[...new Map(rows.value.map(row=>[row.student_id,row])).values()]),checkedCount=computed(()=>uniqueRows.value.filter(row=>isCheckedToday(row.last)).length),rate=computed(()=>uniqueRows.value.length?Math.round(checkedCount.value/uniqueRows.value.length*100):0)
const filteredRows=computed(()=>rows.value.filter(row=>{const matches=`${row.student_name} ${row.username || ''}`.toLocaleLowerCase().includes(query.value.trim().toLocaleLowerCase());return matches && (status.value==='all' || (status.value==='done')===isCheckedToday(row.last))})),pageRows=computed(()=>filteredRows.value.slice((page.value-1)*12,page.value*12))
let controller,timer,disposed=false
async function loadStatus(){controller?.abort();controller=new AbortController();const current=controller;loading.value=true;error.value='';try{const qs=selectedClassId.value?`?class_id=${encodeURIComponent(selectedClassId.value)}`:'';const data=await teacherGet(`/api/teacher/checkin-status${qs}`,{signal:current.signal});if(current.signal.aborted)return;rows.value=(data.students || []).map(row=>({...row,_key:`${row.class_id}:${row.student_id}`}));loaded.value=true}catch(e){if(!current.signal.aborted){error.value=e.message;rows.value=[];loaded.value=false}}finally{if(current===controller)loading.value=false}}
watch([query,status,selectedClassId],()=>{page.value=1;writeTeacherState('checkin',{query:query.value,status:status.value,classId:selectedClassId.value})})
watch(()=>filteredRows.value.length,length=>page.value=Math.min(page.value,Math.max(1,Math.ceil(length/12))))
onMounted(async()=>{timer=setInterval(()=>{const before=todayKey.value;clock.value=new Date();if(before!==todayKey.value)loadStatus()},30000);try{const data=await teacherGet('/api/classes/mine');if(disposed)return;myClasses.value=data.classes || [];if(!myClasses.value.some(c=>String(c.id)===selectedClassId.value))selectedClassId.value='';await loadStatus()}catch(e){if(!disposed)error.value=e.message}})
onBeforeUnmount(()=>{disposed=true;controller?.abort();clearInterval(timer)})
</script>
<style scoped>
.teacher-page{max-width:1200px;margin:0 auto;padding:24px;min-height:calc(100vh - 60px);background:linear-gradient(135deg,#1f1538,#2b1b4f 60%,#3a1c7a);border-radius:14px}.card{background:#faf8fd}.checkin-overview{display:flex;gap:25px;align-items:center;margin-bottom:22px}.checkin-overview .teacher-metrics{grid-template-columns:repeat(3,minmax(0,1fr));flex:1;margin:0}.checkin-ring{position:relative;width:142px;height:142px;flex-shrink:0}.checkin-ring svg{width:100%;height:100%;rotate:-90deg;fill:none;stroke:#d0bbf21c;stroke-width:7}.checkin-ring .ring-value{stroke:#c0e8d9;stroke-dasharray:314.16;stroke-linecap:round;transition:stroke-dashoffset 900ms cubic-bezier(.2,.7,.2,1)}.checkin-ring strong{position:absolute;inset:0;display:flex;flex-direction:column;align-items:center;justify-content:center;color:#efffeb;font-size:29px}.checkin-ring small{font-size:10px;color:#c7b7df;margin-top:6px;font-weight:400}@media(max-width:700px){.checkin-overview{flex-direction:column}.checkin-overview .teacher-metrics{width:100%}.teacher-metric{padding:12px}.teacher-metric small{font-size:10px}}
</style>
