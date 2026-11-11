<template>
  <el-drawer :model-value="modelValue" @update:model-value="$emit('update:modelValue',$event)" title="学生学习档案" size="min(540px, 94vw)" append-to-body class="teacher-drawer student-drawer" @open="morph.open" @opened="onOpened" @close="closePanel">
    <template v-if="student">
      <div class="student-profile"><span ref="avatar" class="profile-avatar"><img v-if="student.avatar" :src="student.avatar" alt="" /><template v-else>{{ (student.name || student.username || '同').slice(0,1) }}</template></span><div><h2>{{ student.name || student.username }}</h2><p>{{ student.className || '班级学生' }} <span v-if="student.username">· @{{ student.username }}</span></p></div></div>
      <p class="student-history-label">累计学习记录</p><div class="student-stat-grid"><div><span>正确率</span><strong>{{ rate }}%</strong></div><div><span>提交次数</span><strong>{{ student.stats?.total_submissions || 0 }}</strong></div><div><span>尝试题目</span><strong>{{ student.stats?.problems_attempted || 0 }}</strong></div></div>
      <section v-if="showTopics" class="student-section"><h3>需要巩固的知识点</h3><div v-if="student.weakTopics?.length" class="topic-distribution"><div v-for="item in student.weakTopics" :key="item.topic"><div><span>{{ item.topic }}</span><small>{{ item.count }} 次</small></div><el-progress :percentage="topicRate(item.count)" :show-text="false" :stroke-width="6" color="#a989c8" /></div></div><el-empty v-else description="暂无薄弱知识点记录" :image-size="65" /></section>
      <LearningAnalysis ref="analysisPanel" :student-id="String(student.id)" audience="teacher" embedded />
    </template>
  </el-drawer>
</template>
<script setup>
import {computed,ref} from 'vue'
import {useDialogMorph} from '@/composables/useDialogMorph'
import LearningAnalysis from '@/components/LearningAnalysis.vue'
const props=defineProps({modelValue:Boolean,student:Object,origin:Object,autoAnalyze:Boolean,showTopics:{type:Boolean,default:true}})
defineEmits(['update:modelValue'])
const avatar=ref(null),analysisPanel=ref(null)
const morph=useDialogMorph({source:()=>props.origin,target:()=>avatar.value,round:true})
const rate=computed(()=>Math.min(100,Math.max(0,Number(props.student?.stats?.success_rate) || 0)).toFixed(1))
const topicRate=count=>Math.round((Number(count) || 0)/Math.max(1,...(props.student?.weakTopics || []).map(item=>Number(item.count) || 0))*100)
function onOpened(){if(props.autoAnalyze)analysisPanel.value?.generate()}
function closePanel(){analysisPanel.value?.cancel();morph.close()}
</script>
<style scoped>
.student-profile{display:flex;align-items:center;gap:16px;padding:8px 0 22px}.profile-avatar{display:grid;place-items:center;width:66px;height:66px;flex-shrink:0;background:linear-gradient(140deg,#e9dafa,#d8eae8);color:#8461a9;border-radius:50%;font-size:25px;overflow:hidden}.profile-avatar img{width:100%;height:100%;object-fit:cover}.student-profile h2{font-size:22px;color:#3e2e51;margin:0 0 8px}.student-profile p{font-size:12px;color:#9c8bad;margin:0}.student-stat-grid{display:grid;grid-template-columns:repeat(3,1fr);gap:10px;padding-bottom:24px}.student-stat-grid>div{padding:17px 12px;border-radius:12px;background:#f6f1fa;display:grid;gap:12px}.student-stat-grid span{font-size:12px;color:#9581a8}.student-stat-grid strong{font-size:23px;color:#79539b}.student-section{padding:22px 0;border-top:1px solid #eee6f5}.student-section h3{font-size:15px;color:#49325c;margin:0 0 16px}.topic-distribution{display:grid;gap:16px}.topic-distribution>div>div:first-child{display:flex;justify-content:space-between;font-size:12px;color:#80688e;margin-bottom:8px}.topic-distribution small{color:#a290b0}.analysis-heading{display:flex;justify-content:space-between;align-items:flex-start;gap:12px}.analysis-heading h3{margin-bottom:7px}.analysis-heading p{font-size:11px;color:#a392ae;margin:0 0 18px}.student-analysis{font-size:13px;line-height:1.9;color:#574364;white-space:pre-wrap;background:#faf7fd;border-radius:12px;padding:18px}.analysis-placeholder{font-size:12px;color:#a08caf;background:#f8f4fc;border-radius:12px;padding:22px;line-height:1.8}
</style>

<style scoped>
.student-history-label{font-size:10px;color:#a28cb1;margin:0 0 12px}
</style>
