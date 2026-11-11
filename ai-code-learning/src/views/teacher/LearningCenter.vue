<template>
  <div class="teacher-page">
    <div class="header teacher-hero">
      <div><span class="teacher-eyebrow">CONNECT THE LEARNING DOTS</span>
      <h1>学习中心</h1>
      <p>通过旭日图查看班级与学生正确率；点击学生查看错误占比。</p>
      </div><TeacherScene scene="data" />
    </div>

    <div class="toolbar">
      <el-button plain :loading="loading" :disabled="loading" @click="refreshAll">刷新</el-button>
    </div>

    <nav class="teacher-rail" aria-label="班级图谱层级"><button @click="focusClass('')">全部班级</button><template v-if="focusedClassId"><span>›</span><button @click="focusClass(focusedClassId)">{{ focusedClassName }}</button></template><template v-if="selectedStudent"><span>›</span><strong>{{ selectedStudent.name }}</strong></template><span v-else>· 点击图表逐层查看</span></nav>
    <el-alert v-if="chartError" class="teacher-error" :title="chartError" type="warning" :closable="false" show-icon />

    <div class="grid">
        <el-card class="card sunburst-card" v-loading="loading || detailLoading" element-loading-background="rgba(33,24,48,.82)">
          <template #header><div class="orbit-heading"><div><span class="orbit-eyebrow">LEARNING ORBIT</span><h2>班级学习图谱</h2></div><span class="orbit-badge"><i></i>{{ focusedClassId?'班级视图':'教学总览' }}</span></div></template>
          <div class="orbit-intro"><p>{{ focusedClassId?'沿着外圈，发现每位学生的学习表现。':'从班级到学生，看见知识生长的轨迹。' }}</p><button v-if="focusedClassId" @click="focusClass('')">↖ 返回总览</button></div>
          <div class="sunburst-shell" @mouseleave="hoveredNode=null">
            <div class="orbit-ambient" aria-hidden="true"><i></i><i></i><span></span></div>
            <div ref="sunburstRef" class="chart sunburst-chart" role="img" :aria-label="`${focusedClassId?focusedClassName:'全部班级'}的班级与学生正确率图谱，内圈为班级，外圈为学生`"></div>
            <div ref="clickFlash" class="orbit-click-flash" aria-hidden="true"></div>
            <div v-if="myClasses.length" class="orbit-center">
              <span class="orbit-center-eyebrow">{{ hoveredNode?.nodeType==='student'?'STUDENT INSIGHT':focusedClassId?'CLASS INSIGHT':'TEACHING OVERVIEW' }}</span>
              <Transition name="orbit-insight" mode="out-in"><div :key="centerInsight.key" class="center-insight"><span class="center-name" :title="centerInsight.name">{{ centerInsight.name }}</span><strong>{{ centerInsight.rate===null?'—':centerInsight.rate.toFixed(1) }}<small v-if="centerInsight.rate!==null">%</small></strong><span class="center-caption">{{ centerInsight.rate===null?'暂无提交记录':'整体正确率' }}</span></div></Transition>
              <span class="orbit-center-count">{{ centerInsight.caption }}</span>
            </div>
            <div v-else-if="!loading" class="orbit-no-data"><span>◎</span><strong>{{ chartError?'图谱暂时不可用':'还没有班级' }}</strong><p>{{ chartError?'点击刷新重新加载':'班级和学生加入后，学习图谱将在这里展开。' }}</p></div>
          </div>
          <div class="orbit-legend" aria-label="学生正确率颜色说明"><span v-for="item in learningRateColors" :key="item.label"><i :style="{background:item.color}"></i>{{ item.label }}</span></div>
          <div class="orbit-footer"><div><strong>{{ chartSummary.count }}</strong><span>位学生</span></div><div><strong>{{ chartSummary.active }}</strong><span>已有提交</span></div><div><strong>{{ chartSummary.total }}</strong><span>次练习提交</span></div></div>
          <div class="orbit-explore"><div v-if="!focusedClassId" class="orbit-class-list" aria-label="选择班级"><button v-for="item in myClasses" :key="item.id" @click="focusClass(item.id)">{{ item.name }} <span>↗</span></button></div><el-select v-else :model-value="selectedStudent?.id" placeholder="选择学生，查看错误分布" filterable clearable aria-label="查找图谱中的学生" @change="chooseStudent"><el-option v-for="student in visibleStudents" :key="student.id" :label="student.name || student.username" :value="student.id" /></el-select><p>内圈区分班级 · 外圈每位学生一格 · 颜色表示正确率</p></div>
        </el-card>

        <!-- 第二个卡片：错误占比 -->
        <el-card class="card" v-loading="loading">
            <template #header>
              <div class="card-head">
                <div class="student-error-heading"><div class="card-title">学生错误占比</div><el-button v-if="selectedStudent" class="student-insight-button" type="primary" plain size="small" @click="studentVisible=true">档案与 AI 分析 ↗</el-button></div>
                <div class="card-subtitle" v-if="selectedStudent">
                  {{ selectedStudent.name }}（{{ selectedStudent.className }}）｜正确率 {{ formatRate(selectedStudent?.stats?.success_rate) }}
                </div>
                <div class="card-subtitle" v-else>点击左侧旭日图中的学生节点</div>
              </div>
            </template>

        <!-- 固定 ECharts 容器，永不销毁 -->
        <div ref="errorChartRef" class="chart"></div>

        <!-- 空状态用浮层显示，不破坏 DOM -->
        <el-empty 
          v-show="!selectedStudent" 
          description="暂无选择学生" 
          class="empty-overlay" 
        />
        <el-empty 
          v-show="selectedStudent && !errorBuckets.length" 
          description="暂无错误数据" 
          class="empty-overlay" 
        />
        </el-card>
      
    </div>
    <TopicArt scene="orbit" inverse />
    <TeacherStudentDrawer v-model="studentVisible" :student="selectedStudent" :show-topics="false" />
  </div>
</template>

<script setup>
import TopicArt from '@/components/TopicArt.vue'
import TeacherScene from '@/components/TeacherScene.vue'
import TeacherStudentDrawer from '@/components/TeacherStudentDrawer.vue'
import {useRoute} from 'vue-router'
import { computed, nextTick, onBeforeUnmount, onMounted, ref,watch } from 'vue'
import {readTeacherState,writeTeacherState} from '@/utils/teacherApi'
import * as echarts from 'echarts'
import {buildLearningSunburst,createLearningSunburstOption,learningRateColors,summarizeStudents} from '@/utils/teacherSunburst'
import { ElMessage } from 'element-plus'
import { getAuthToken } from '@/utils/authStorage'

const loading = ref(false)
const detailLoading = ref(false)
const sunburstRef = ref(null)
const errorChartRef = ref(null)
const clickFlash=ref(null)
let clickAnimation
function playClickFeedback(returning=false){
  clickAnimation?.cancel()
  if(typeof clickFlash.value?.animate!=='function')return
  clickAnimation=clickFlash.value.animate([
    {transform:`scale(${returning?1.06:.72})`,opacity:0},
    {opacity:.65,offset:.15},
    {transform:`scale(${returning ? .65 : 1.08})`,opacity:0}
  ],{duration:720,easing:'cubic-bezier(.2,.65,.2,1)'})
}
let sunburstInstance = null
let errorChartInstance = null

const myClasses = ref([])
const classStudents = ref([])
const selectedStudent = ref(null)
const focusedClassId = ref(readTeacherState('chart-class',''))
const chartError=ref('')
let chartSequence=0,initialized=false
watch(focusedClassId,value=>writeTeacherState('chart-class',value))
const route=useRoute(),studentVisible=ref(false)
const focusedClassName=computed(()=>myClasses.value.find(c=>String(c.id)===String(focusedClassId.value))?.name || '班级')
function focusClass(id){playClickFeedback(!id);focusedClassId.value=String(id);selectedStudent.value=null;hoveredNode.value=null;studentVisible.value=false;errorChartInstance?.clear();renderSunburst()}

const token = () => getAuthToken()

const formatRate = (v) => {
  const n = Number(v || 0)
  if (!Number.isFinite(n)) return '0.00%'
  return `${n.toFixed(2)}%`
}

const hoveredNode=ref(null)
const visibleStudents=computed(()=>focusedClassId.value?classStudents.value.filter(student=>String(student.classId)===String(focusedClassId.value)):classStudents.value)
const chartSummary=computed(()=>summarizeStudents(visibleStudents.value))
const buildSunburstData=computed(()=>buildLearningSunburst(myClasses.value,classStudents.value,{focusedClassId:focusedClassId.value,selectedStudentId:selectedStudent.value?.id}))
const centerInsight=computed(()=>{
  const node=hoveredNode.value
  if(node?.nodeType==='student')return {key:node.id,name:node.name,rate:node.successRate,caption:`${node.totalSubmissions} 次提交`}
  if(node?.nodeType==='class' || node?.nodeType==='class_focus')return {key:node.id,name:node.name,rate:node.avgRate,caption:`${node.studentCount} 位学生`}
  return {key:`scope:${focusedClassId.value}`,name:focusedClassId.value?focusedClassName.value:'全部班级',rate:chartSummary.value.rate,caption:focusedClassId.value?`${chartSummary.value.count} 位学生`:`${myClasses.value.length} 个班级`}
})
async function chooseStudent(id){
  if(id==null || id===''){selectedStudent.value=null;studentVisible.value=false;hoveredNode.value=null;errorChartInstance?.clear();renderSunburst();return}
  const found=visibleStudents.value.find(student=>String(student.id)===String(id))
  if(!found)return
  playClickFeedback()
  selectedStudent.value=found;studentVisible.value=false
  renderSunburst()
  await nextTick();renderErrorChart()
}

const errorBuckets = computed(() => {
  const t = selectedStudent.value?.weakTopics
  if (!Array.isArray(t)) return []
  return t
    .map((x) => ({ topic: String(x?.topic || '').trim(), count: Number(x?.count || 0) }))
    .filter((x) => x.topic && Number.isFinite(x.count) && x.count > 0)
})

const loadClasses = async () => {
  const t = token()
  if (!t) return []
  const res = await fetch('/api/classes/mine', { headers: { Authorization: `Bearer ${t}` } }).catch(() => null)
  const data = res ? await res.json().catch(() => ({})) : {}
  if (!res || !res.ok || data?.success === false) {
    throw new Error(data?.detail || data?.message || '加载班级失败')
  }
  return Array.isArray(data?.classes) ? data.classes : []
}

const loadStudentsByClass = async (classId) => {
  const t = token()
  if (!t) return []
  const qs = `?class_id=${encodeURIComponent(String(classId || ''))}&limit=200`
  const res = await fetch(`/api/teacher/classes/students${qs}`, { headers: { Authorization: `Bearer ${t}` } }).catch(() => null)
  const data = res ? await res.json().catch(() => ({})) : {}
  if (!res || !res.ok || data?.success === false) {
    throw new Error(data?.detail || data?.message || '加载学生失败')
  }
  const list = Array.isArray(data?.students) ? data.students : []
  return list.map((s) => ({ ...s, classId, className: String(data?.class?.name || '') }))
}

const renderSunburst = () => {
  if (!sunburstRef.value) return
  if (!sunburstInstance) {
    sunburstInstance = echarts.init(sunburstRef.value)
    sunburstInstance.on('click', params => {
      const node=params?.data || {}
      if(node.back){focusClass('');return}
      if(node.nodeType==='class' && node.classId){focusClass(node.classId);return}
      if(node.nodeType==='student' && node.studentId){
        if(!focusedClassId.value)focusedClassId.value=String(node.classId)
        chooseStudent(node.studentId)
      }
    })
    sunburstInstance.on('mouseover',params=>{const node=params?.data;hoveredNode.value=node?.nodeType==='empty'?null:node || null})
    sunburstInstance.on('globalout',()=>{hoveredNode.value=null})
  }
  const compact=sunburstRef.value.clientWidth>0 && sunburstRef.value.clientWidth<450
  sunburstInstance.setOption(createLearningSunburstOption(buildSunburstData.value,{compact}),{notMerge:false})
}
const renderErrorChart = () => {
  if (!errorChartRef.value || !selectedStudent.value) return
  if (!errorChartInstance) errorChartInstance=echarts.init(errorChartRef.value)
  const items=errorBuckets.value
  const data=items.map(item=>({name:item.topic,value:item.count}))
  const compact=data.length>=7
  const option = {
    color: ['#a98ac7','#baa6d8','#8cb9ac','#b99bae','#d0af9d','#99a5c8','#c4b5cf'],
    animation: true,
    animationDuration: 360,
    animationEasing: 'cubicOut',
    animationDurationUpdate: 360,
    animationEasingUpdate: 'cubicOut',
    tooltip: {
      trigger: 'item',
      backgroundColor: '#faf7fd',
      borderColor: '#d8c8e9',
      borderWidth: 1,
      textStyle: { color: '#0f172a' },
      formatter: '{b}: {c} 次 ({d}%)'
    },
    legend: compact
      ? {
          type: 'scroll',
          orient: 'horizontal',
          bottom: 0,
          left: 0,
          width: '100%',
          pageButtonPosition: 'end',
          itemWidth: 10,
          itemHeight: 10,
          itemGap: 10,
          textStyle: { color: '#111', fontSize: 12 },
          formatter: (name) => (String(name).length > 10 ? `${String(name).slice(0, 10)}…` : String(name))
        }
      : {
          bottom: 0,
          left: 'center',
          itemWidth: 10,
          itemHeight: 10,
          itemGap: 10,
          textStyle: { color: '#111', fontSize: 12 },
          formatter: (name) => (String(name).length > 14 ? `${String(name).slice(0, 14)}…` : String(name))
        },
    series: [
      {
        name: '错误占比',
        type: 'pie',
        universalTransition: true,
        radius: compact ? ['44%', '76%'] : ['44%', '72%'],
        center: compact ? ['50%', '44%'] : ['50%', '45%'],
        avoidLabelOverlap: true,
        itemStyle: { borderRadius: 8, borderColor: '#bfdbfe', borderWidth: 1 },
        blur: { itemStyle: { opacity: 0.92 } },
        emphasis: {
          itemStyle: {
            borderColor: '#93c5fd',
            borderWidth: 2,
            shadowBlur: 0,
            shadowColor: 'rgba(0,0,0,0)'
          }
        },
        label: compact ? { show: false } : { color: '#0f172a', formatter: '{b}: {d}%' },
        labelLine: compact ? { show: false } : { lineStyle: { color: 'rgba(15,23,42,0.35)' }, length: 10, length2: 8 },
        labelLayout: { hideOverlap: true },
        data: data.length ? data : [{ name: '暂无错误', value: 1 }]
      }
    ]
  }
  errorChartInstance.setOption(option, true)
}

const refreshAll = async () => {
  if(loading.value)return
  const sequence=++chartSequence
  const t = token()
  if (!t) {
    ElMessage.warning('请先登录')
    return
  }
  loading.value = true
  chartError.value=''
  detailLoading.value = false
  try {
    hoveredNode.value=null
    const classes = await loadClasses()
    if(sequence!==chartSequence)return
    myClasses.value = classes
    const results = await Promise.allSettled((classes || []).map(c=>loadStudentsByClass(c.id)))
    if(sequence!==chartSequence)return
    const missing=results.flatMap((result,index)=>result.status==='rejected'?[classes[index].name]:[])
    if(missing.length)chartError.value=`以下班级数据暂时无法加载：${missing.join('、')}。请刷新重试。`
    classStudents.value = results.flatMap(result=>result.status==='fulfilled'?result.value:[])
    selectedStudent.value=classStudents.value.find(student=>student.id===selectedStudent.value?.id && student.classId===selectedStudent.value?.classId) || null
    if(!selectedStudent.value)studentVisible.value=false
    const initialClass=String((initialized?focusedClassId.value:route.query.class_id || focusedClassId.value) || '')
    initialized=true
    focusedClassId.value = classes.some(c=>String(c.id)===initialClass)?initialClass:''
    renderSunburst()
    if (errorChartInstance) {
      errorChartInstance.clear()
      errorChartInstance.resize()
    }
    if(selectedStudent.value)renderErrorChart()
  } catch (e) {
    if(sequence===chartSequence)chartError.value=e?.message || '加载失败，请刷新重试'
  } finally {
    loading.value = false
  }
}

const handleResize = () => {
  try {
    if (sunburstInstance) {sunburstInstance.resize();renderSunburst()}
    if (errorChartInstance) errorChartInstance.resize()
  } catch {
  }
}

onMounted(() => {
  refreshAll()
  window.addEventListener('resize', handleResize)
})

onBeforeUnmount(() => {
  clickAnimation?.cancel()
  chartSequence++
  window.removeEventListener('resize', handleResize)
  try {
    if (sunburstInstance) sunburstInstance.dispose()
    if (errorChartInstance) errorChartInstance.dispose()
  } catch {
  }
  sunburstInstance = null
  errorChartInstance = null
})
</script>

<style scoped>
.teacher-page{max-width:1200px;margin:0 auto;padding:24px;min-height:calc(100vh - 60px);background:linear-gradient(135deg,#1f1538,#2b1b4f 60%,#3a1c7a);border-radius:14px}.header h1{margin:0 0 8px;color:#fff}.header p{margin:0 0 18px;color:#ffffffbf}.toolbar{display:flex;gap:12px;align-items:center;margin-bottom:14px}.grid{display:grid;grid-template-columns:minmax(0,1.2fr) minmax(0,.8fr);gap:20px;align-items:start}.card{position:relative;min-width:0;background:#faf8fd;border:1px solid #e7dfee;border-radius:20px;overflow:hidden}.card-head{display:grid;gap:8px}.card-title{font-weight:700;font-size:16px;color:#59426a}.card-subtitle{color:#a18eaf;font-size:12px;line-height:1.8}.chart{width:100%;height:480px}.empty-overlay{position:absolute;inset:85px 0 0;background:#faf8fd;display:flex;align-items:center;justify-content:center;z-index:2;margin:0}
.sunburst-card{background:radial-gradient(ellipse at 52% 43%,#48325e66,transparent 65%),linear-gradient(145deg,#302343,#221a34 60%,#2d2142);border:1px solid #ac89cf33;box-shadow:0 18px 55px #10091e33}.sunburst-card :deep(.el-card__header){border-bottom:1px solid #dbc0f218;padding:23px 25px 20px}.sunburst-card :deep(.el-card__body){padding:0 23px 22px}.orbit-heading{display:flex;justify-content:space-between;align-items:center;gap:12px}.orbit-eyebrow{font:9px Consolas,monospace;letter-spacing:2.5px;color:#c7a6e3a3}.orbit-heading h2{margin:9px 0 0;color:#f0e5fa;font-size:20px;font-weight:600;letter-spacing:1px}.orbit-badge{display:flex;align-items:center;gap:7px;border:1px solid #c7a6df2b;border-radius:20px;background:#d6b4f508;padding:7px 10px;color:#ccb9df;font-size:10px;white-space:nowrap}.orbit-badge i{width:5px;height:5px;border-radius:50%;background:#b8dec9;box-shadow:0 0 8px #b8dec977}.orbit-intro{display:flex;justify-content:space-between;align-items:center;gap:10px;padding:15px 0 0}.orbit-intro p{font-size:11px;color:#b5a2c7;line-height:1.8;margin:0}.orbit-intro button{border:0;background:none;color:#d9c0ef;font-size:11px;white-space:nowrap;cursor:pointer}.sunburst-shell{position:relative;isolation:isolate}.sunburst-chart{height:460px;position:relative;z-index:1}.orbit-ambient{position:absolute;inset:0;overflow:hidden;pointer-events:none;z-index:0;background:radial-gradient(circle at 50% 50%,#c299ee0c 0 19%,transparent 20%),radial-gradient(#dac5ff12 .8px,transparent .9px);background-size:auto,23px 23px;mask-image:radial-gradient(ellipse,#000 45%,transparent 76%)}.orbit-ambient i{position:absolute;left:50%;top:50%;width:min(91%,430px);aspect-ratio:1;border:1px dashed #bd99e72b;border-radius:50%;translate:-50% -50%;animation:orbit-guide-turn 140s linear infinite}.orbit-ambient i+i{width:min(98%,455px);border-style:solid;border-color:#d7b5ed0b;animation-direction:reverse}.orbit-ambient span{position:absolute;inset:0;opacity:.5;background:radial-gradient(ellipse at 20% 30%,#c6a9ff12,transparent 50%);animation:orbit-breathe 8s ease-in-out infinite}.orbit-center{position:absolute;left:50%;top:50%;translate:-50% -50%;z-index:2;width:138px;height:138px;border-radius:50%;display:flex;align-items:center;justify-content:center;flex-direction:column;gap:9px;pointer-events:none;background:radial-gradient(circle at 35% 25%,#6d4f8e32,#241b34 78%);border:1px solid #d7b7f326;box-shadow:0 0 30px #c59ae513,inset 0 0 20px #cbaaf509}.orbit-center-eyebrow{font:6px Consolas,monospace;letter-spacing:1.4px;color:#c0a5d77d}.center-insight{display:grid;justify-items:center;gap:4px;width:100%}.center-name{font-size:11px;max-width:108px;text-overflow:ellipsis;white-space:nowrap;overflow:hidden;color:#e4d3f0}.center-insight strong{font:300 30px/1.2 Consolas,monospace;color:#f4eafa;letter-spacing:-1px}.center-insight strong small{font-size:13px;color:#bea2d3;margin-left:3px}.center-caption{font-size:9px;color:#b8a1ca}.orbit-center-count{font-size:9px;color:#b7d8cb;border-top:1px solid #c49ce51f;padding-top:7px;min-width:65px;text-align:center}.orbit-legend{display:flex;justify-content:center;gap:13px;flex-wrap:wrap;margin-top:-2px;position:relative;z-index:1}.orbit-legend>span{display:flex;align-items:center;gap:5px;font-size:10px;color:#c6b0d6}.orbit-legend i{width:6px;height:6px;border-radius:50%;box-shadow:0 0 8px #ffffff09}.orbit-footer{display:grid;grid-template-columns:repeat(3,1fr);margin-top:22px;padding:18px 0;border-top:1px solid #cba7e91c;border-bottom:1px solid #cba7e91c}.orbit-footer>div{display:grid;justify-items:center;gap:7px;border-right:1px solid #cba7e91c}.orbit-footer>div:last-child{border:0}.orbit-footer strong{font:20px Consolas,monospace;color:#dfceef}.orbit-footer span{font-size:10px;color:#b49ac5}.orbit-explore{padding-top:16px}.orbit-explore>p{font-size:9px;color:#a68bbba8;line-height:1.7;text-align:center;margin:14px 0 0}.orbit-class-list{display:flex;justify-content:center;flex-wrap:wrap;gap:7px;max-height:78px;overflow:auto}.orbit-class-list button{font:inherit;font-size:10px;border:1px solid #caace626;border-radius:8px;background:#ceb1ef08;color:#cbb4df;cursor:pointer;padding:7px 9px;transition:background .2s,translate .2s}.orbit-class-list button span{padding-left:8px;color:#b8dacb}.orbit-class-list button:hover{background:#c8a5e320;translate:0 -2px}.orbit-explore :deep(.el-select__wrapper){background:#d5b4f50a;box-shadow:0 0 0 1px #cba5e52b inset}.orbit-explore :deep(.el-select__placeholder){font-size:11px;color:#c4add7}.orbit-no-data{position:absolute;inset:0;z-index:2;display:flex;flex-direction:column;align-items:center;justify-content:center;gap:14px;color:#cbb2df;background:#271c38a6}.orbit-no-data>span{font:70px Consolas,monospace;color:#aa83c66b}.orbit-no-data strong{font-size:16px;font-weight:500}.orbit-no-data p{font-size:11px;color:#a88abb}.orbit-insight-enter-active,.orbit-insight-leave-active{transition:opacity 110ms,transform 110ms}.orbit-insight-enter-from{opacity:0;transform:translateY(4px)}.orbit-insight-leave-to{opacity:0;transform:translateY(-4px)}
.student-error-heading{display:flex;align-items:center;justify-content:space-between;gap:12px;flex-wrap:wrap}.student-insight-button{--el-color-primary:#9270b1;--el-color-primary-light-9:#f4edf9;--el-color-primary-light-7:#dfcfed}
.orbit-click-flash{position:absolute;inset:8% 10%;border:1px solid #d9b5fa99;border-radius:50%;box-shadow:0 0 22px #d0a3f52b,inset 0 0 22px #b4e2d71f;pointer-events:none;opacity:0;z-index:2}
@keyframes orbit-guide-turn{to{rotate:360deg}}@keyframes orbit-breathe{50%{opacity:1}}
@media(max-width:1100px){.grid{grid-template-columns:1fr}.sunburst-chart{height:480px}.sunburst-card :deep(.el-card__body){padding-right:30px;padding-left:30px}.chart:not(.sunburst-chart){height:420px}.orbit-center{width:145px;height:145px}}
@media(max-width:600px){.sunburst-card :deep(.el-card__body){padding:0 12px 18px}.sunburst-card :deep(.el-card__header){padding:19px 18px}.orbit-heading h2{font-size:18px}.sunburst-chart{height:380px}.orbit-center{width:min(112px,calc((100vw - 80px)*.32));height:min(112px,calc((100vw - 80px)*.32));gap:6px}.orbit-center-eyebrow{font-size:5px;letter-spacing:.7px}.center-name{font-size:10px;max-width:87px}.center-insight strong{font-size:24px}.center-caption,.orbit-center-count{font-size:8px}.orbit-intro{padding-left:5px;padding-right:5px}.orbit-intro p{font-size:10px}.orbit-legend{gap:8px}.orbit-legend>span{font-size:9px}.orbit-footer strong{font-size:18px}}
</style>
