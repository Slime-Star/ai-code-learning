<template>
  <section class="learning-analysis" :class="{embedded}" aria-label="学习分析">
    <div class="report-toolbar"><div><h3>{{ audience==='teacher'?'AI 教学建议':'AI 学习分析' }}</h3><p>根据最近 {{ days }} 天的真实提交生成建议</p></div><div class="report-controls"><el-select v-model="days" aria-label="分析时间范围" size="small" :disabled="loading"><el-option v-for="value in [7,30,90]" :key="value" :label="`最近 ${value} 天`" :value="value" /></el-select><el-button type="primary" plain size="small" :loading="loading" @click="generate">{{ result?'更新分析':'生成分析' }}</el-button></div></div>
    <div v-if="phase==='deep'" class="report-progress" role="status"><i></i>本地概览已生成，正在补充 DeepSeek 建议…<button @click="cancel">停止等待</button></div>
    <el-skeleton v-if="phase==='quick' && !result" :rows="4" animated />
    <el-alert v-if="error" class="report-notice" :title="error" type="warning" :closable="false" show-icon><template #default><el-button link type="primary" @click="generate">重试</el-button></template></el-alert>
    <template v-if="result">
      <div class="report-provenance"><span :class="{deep:result.provider==='deepseek'}">{{ result.provider==='deepseek'?'DeepSeek 深度分析':'本地规则分析' }}</span><small>{{ result.cached?'复用本期结果 · ':'' }}{{ generatedTime }}</small></div>
      <p v-if="fallbackText" class="report-fallback">{{ fallbackText }}</p>
      <div class="report-summary">{{ result.report.summary }}</div>
      <div class="report-basis"><span>{{ result.stats.totalRuns }} 次提交</span><span>{{ result.stats.problems }} 道尝试题目</span><span>{{ result.stats.rate==null?'暂无正确率':`正确率 ${result.stats.rate}%` }}</span></div>
      <p v-if="result.stats.errorRuns>result.stats.sampledErrors" class="report-sample">错误主题基于最近 {{ result.stats.sampledErrors }} 条失败提交的样本，非全部历史记录。</p>
      <div v-if="result.report.strengths?.length" class="report-strengths"><h4>已有进展</h4><p v-for="item in result.report.strengths" :key="item">{{ item }}</p></div>
      <div v-if="result.report.focuses?.length" class="report-focuses"><h4>{{ audience==='teacher'?'教学关注点':'优先巩固' }}</h4><article v-for="item in result.report.focuses" :key="item.topic"><div><strong>{{ item.topic }}</strong><span>{{ item.count }} 次</span></div><small>{{ item.evidence }}</small><p>{{ item.advice }}</p><button v-if="audience!=='teacher'" @click="practice(item.topic)">练习相关题目 ↗</button></article></div>
      <div class="report-next"><h4>下一步行动</h4><ol><li v-for="item in result.report.next_steps" :key="item">{{ item }}</li></ol><el-button v-if="audience==='teacher'" size="small" plain @click="router.push('/teacher/create-task')">发布巩固练习 ↗</el-button><el-button v-else-if="result.stats.totalRuns" size="small" plain @click="router.push('/wrong-questions')">打开错题本 ↗</el-button><el-button v-else size="small" plain @click="router.push('/daily-checkin')">开始练习 ↗</el-button></div>
      <p class="report-caveat">{{ result.report.caveat }}</p>
    </template>
    <div v-else-if="!loading && !error" class="report-placeholder">{{ audience==='teacher'?'选择时间范围，生成有数据依据的教学建议。':'从提交记录中发现需要巩固的知识点，并找到下一步练习。' }}</div>
  </section>
</template>
<script setup>
import {computed,onBeforeUnmount,onMounted,ref,watch} from 'vue'
import {useRouter} from 'vue-router'
import {getAuthToken,getCurrentUser} from '@/utils/authStorage'
const props=defineProps({studentId:{type:String,default:''},audience:{type:String,default:'student'},embedded:Boolean})
const emit=defineEmits(['stats','period'])
const router=useRouter(),days=ref(30),phase=ref(''),result=ref(null),error=ref('')
const loading=computed(()=>!!phase.value)
let controller,sequence=0,owner=String(getCurrentUser()?.id || 'guest')
const reasons={not_configured:'深度分析暂未配置，当前显示本地概览。',insufficient_data:'暂无提交记录，积累练习后再生成深度分析。',timeout:'深度分析响应超时，已保留本地结果，可稍后重试。',auth_failed:'深度分析服务暂不可用，已保留本地结果。',balance:'深度分析服务暂不可用，已保留本地结果。',rate_limited:'深度分析请求较多，已保留本地结果，请稍后重试。',busy:'深度分析正在处理其他请求，已保留本地结果。'}
const fallbackText=computed(()=>result.value?.fallback_reason?(reasons[result.value.fallback_reason] || '深度分析暂不可用，当前显示本地结果。'):'')
const generatedTime=computed(()=>result.value?.generated_at?new Date(result.value.generated_at).toLocaleString('zh-CN',{month:'2-digit',day:'2-digit',hour:'2-digit',minute:'2-digit'}):'')
function cancel(){sequence++;controller?.abort();phase.value=''}
function reset(){cancel();result.value=null;error.value=''}
function syncOwner(){const next=String(getCurrentUser()?.id || 'guest');if(next!==owner){owner=next;reset()}}
watch(()=>props.studentId,reset)
watch(days,()=>{const hadResult=!!result.value;reset();emit('period',days.value);if(hadResult)generate()})
async function generate(){
  if(loading.value)return
  syncOwner();controller=new AbortController();const activeController=controller,signal=activeController.signal,current=++sequence
  phase.value='quick';error.value=''
  async function request(mode){
    const response=await fetch('/api/learning-analysis',{method:'POST',signal,headers:{'Content-Type':'application/json',Authorization:`Bearer ${getAuthToken() || ''}`},body:JSON.stringify({student_id:props.studentId,days:days.value,mode})})
    const data=await response.json().catch(()=>({}))
    if(!response.ok || !data.success)throw new Error(data.detail || data.message || '分析暂时不可用，请稍后重试')
    if(!data.report?.summary || !data.stats)throw new Error('分析结果不完整，请重试')
    return data
  }
  let timer=setTimeout(()=>activeController.abort(),10000)
  try{
    const quick=await request('quick');if(current!==sequence)return
    result.value=quick;emit('stats',quick.stats);clearTimeout(timer)
    if(quick.provider==='deepseek' || !quick.stats.totalRuns)return
    phase.value='deep';timer=setTimeout(()=>activeController.abort(),38000)
    const deep=await request('deep');if(current===sequence){result.value=deep;emit('stats',deep.stats)}
  }catch(e){if(current===sequence)error.value=e.name==='AbortError'?(result.value?'深度分析等待超时，已保留现有概览。':'统计加载超时，请重试。'):e.message}
  finally{clearTimeout(timer);if(current===sequence)phase.value=''}
}
function practice(topic){const keywords={'数组/下标与越界':'数组','变量/作用域/未定义':'变量','超时/死循环/复杂度':'循环','输入输出与解析':'输入','缩进与代码块':'条件','语法与标点':'基础'};router.push({path:'/daily-checkin',query:{q:keywords[topic] || topic.split('/')[0]}})}
onMounted(()=>window.addEventListener('user-updated',syncOwner))
onBeforeUnmount(()=>{cancel();window.removeEventListener('user-updated',syncOwner)})
defineExpose({generate,cancel,reset})
</script>
<style scoped>
.learning-analysis{color:#584169;--el-color-primary:#9270b1;--el-color-primary-light-9:#f4edf9}.report-toolbar{display:flex;justify-content:space-between;align-items:flex-start;gap:12px;flex-wrap:wrap;margin-bottom:16px}.report-toolbar h3{font-size:16px;margin:0 0 7px}.report-toolbar p{font-size:11px;color:#a18aac;margin:0;line-height:1.7}.report-controls{display:flex;gap:8px;align-items:center}.report-controls .el-select{width:110px}.report-provenance{display:flex;gap:10px;align-items:center;flex-wrap:wrap;font-size:10px;color:#a58db4;margin:14px 0}.report-provenance>span{border-radius:20px;padding:5px 9px;background:#eee7f5;color:#9573b0}.report-provenance>span.deep{background:#e7f3ed;color:#568473}.report-provenance small{font-size:10px}.report-summary{padding:16px;background:linear-gradient(125deg,#f3edf9,#f7f4fc);border-left:3px solid #b294cf;border-radius:0 12px 12px 0;font-size:13px;line-height:1.9}.report-basis{display:flex;gap:7px;flex-wrap:wrap;padding-top:12px}.report-basis span{font-size:10px;padding:5px 8px;background:#f5f1f8;border-radius:6px;color:#9a83aa}.report-focuses,.report-strengths,.report-next{margin-top:22px}.learning-analysis h4{font-size:13px;margin:0 0 12px;color:#6e4f85}.report-focuses article{border:1px solid #ece4f3;border-radius:12px;padding:14px;margin-top:10px}.report-focuses article>div{display:flex;justify-content:space-between;font-size:12px}.report-focuses article>div>span{font-size:11px;color:#a48ab5}.report-focuses small{display:block;margin-top:7px;font-size:10px;color:#b19cc0}.report-focuses p,.report-strengths p,.report-next li{font-size:12px;line-height:1.9;margin:8px 0;color:#8e759f}.report-focuses button{font:inherit;font-size:11px;border:0;background:none;color:#8b62a8;cursor:pointer;padding:5px 0}.report-next ol{padding-left:19px;margin:0 0 14px}.report-caveat,.report-sample,.report-fallback{font-size:10px;color:#aa94b9;line-height:1.8;margin:14px 0 0}.report-placeholder{padding:23px;background:#f7f2fb;border-radius:12px;color:#a68cb8;font-size:12px;line-height:1.9}.report-notice{margin:12px 0}.report-progress{display:flex;align-items:center;gap:7px;font-size:11px;color:#a184b8;margin:12px 0;line-height:1.8}.report-progress i{width:6px;height:6px;background:#ac8dcc;border-radius:50%;animation:report-pulse 1s ease-in-out infinite;flex-shrink:0}.report-progress button{margin-left:auto;background:none;border:0;font:inherit;font-size:10px;color:#9b80ae;cursor:pointer;white-space:nowrap}.embedded{padding:22px 0;border-top:1px solid #eee6f5}@keyframes report-pulse{50%{opacity:.3;scale:.65}}
</style>
