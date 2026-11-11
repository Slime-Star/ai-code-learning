<template>
  <div class="teacher-page">
    <div class="header teacher-hero"><div><span class="teacher-eyebrow">FROM AN IDEA TO A LESSON</span>
      <h1>发布打卡任务</h1>
      <p>编写练习、预览学生看到的内容，再发布到指定班级。</p>
    </div><TeacherScene scene="draft" /></div>

    <Transition name="publish-result"><div v-if="publishedTitle" class="task-publish-success" role="status"><span>✓</span><div><strong>「{{ publishedTitle }}」已发布</strong><p>学生可以在对应班级的每日练习中查看。</p></div><el-button type="success" plain @click="router.push('/teacher/workbench/task-manage')">查看任务 →</el-button></div></Transition>
    <div class="draft-toolbar"><span role="status">{{ draftError || (hasContent ? savedAt ? `草稿已保存 · ${new Date(savedAt).toLocaleTimeString('zh-CN',{hour:'2-digit',minute:'2-digit'})}` : '正在保存草稿…' : '输入内容后自动保存为本地草稿') }}<small v-if="restoredDraft">已恢复上次编辑内容</small></span><el-button text :disabled="!hasContent" @click="saveDraft">保存草稿</el-button></div>

    <div class="task-compose-layout">
    <el-card class="card">
      <el-form :model="form" label-width="110px">
        <el-form-item label="选择班级">
          <el-select v-model="form.class_id" placeholder="选择班级" style="width: min(320px,100%)">
            <el-option v-for="c in myClasses" :key="c.id" :label="`${c.name}（${c.code}）`" :value="c.id" />
          </el-select>
        </el-form-item>

        <el-form-item label="题目标题">
          <el-input v-model="form.title" placeholder="例如：求素数判断" maxlength="60" show-word-limit />
        </el-form-item>

        <el-form-item label="题目描述">
          <el-input v-model="form.description" type="textarea" :rows="3" placeholder="描述要求、输入输出示例等" />
        </el-form-item>

        <el-form-item label="语言">
          <el-select v-model="form.language" style="width: 180px">
            <el-option label="JavaScript" value="javascript" />
            <el-option label="Python" value="python" />
            <el-option label="Java" value="java" />
            <el-option label="C" value="c" />
          </el-select>
        </el-form-item>

        <el-form-item label="初始代码">
          <div class="code-editor" ref="starterRef"></div>
        </el-form-item>

        <el-form-item label="预期输出">
          <el-input v-model="form.expected_output" placeholder="用于学生端自动判题（可选）" />
        </el-form-item>

        <el-form-item label="参考答案">
          <div class="code-editor" ref="solutionRef"></div>
        </el-form-item>

        <el-form-item label="截止时间">
          <el-date-picker
            v-model="dueAt"
            type="datetime"
            placeholder="选择截止时间（可选）"
            format="YYYY-MM-DD HH:mm"
            value-format="YYYY-MM-DDTHH:mm:ss"
          />
        </el-form-item>

        <el-form-item>
          <el-button type="primary" :loading="loading" :disabled="loading" @click="submit">发布到班级</el-button>
          <el-button plain :disabled="loading" @click="confirmReset">重置</el-button>
        </el-form-item>
      </el-form>
    </el-card>
    <aside class="task-preview"><div class="preview-heading"><span>STUDENT VIEW</span><el-tag size="small" type="info">实时预览</el-tag></div><div class="preview-body"><div class="preview-meta"><el-tag size="small">{{ languageLabels[form.language] }}</el-tag><span>{{ myClasses.find(c=>String(c.id)===String(form.class_id))?.name || '待选择班级' }}</span></div><h2>{{ form.title || '在这里看到题目标题' }}</h2><p>{{ form.description || '填写题目描述后，这里会展示学生阅读到的要求和示例。' }}</p><div v-if="form.starter_code" class="preview-code"><span>初始代码</span><pre>{{ form.starter_code }}</pre></div><div v-if="dueAt" class="preview-deadline">截止时间 · {{ dueAt.replace('T',' ') }}</div><div class="preview-footer"><span>教师任务</span><span class="preview-start">开始练习 ↗</span></div></div><div class="preview-tip">预览不会运行代码或发布题目。参考答案保留在教师编辑区。</div></aside>
    </div>
    <TopicArt scene="books" inverse />
  </div>
</template>

<script setup>
import TopicArt from '@/components/TopicArt.vue'
import TeacherScene from '@/components/TeacherScene.vue'
import { computed, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import {useRouter,onBeforeRouteLeave} from 'vue-router'
import { ElMessage,ElMessageBox } from 'element-plus'
import {teacherStorageKey,invalidateTeacherState} from '@/utils/teacherApi'
import { getAuthToken } from '@/utils/authStorage'
import ace from 'ace-builds'
import 'ace-builds/src-noconflict/mode-javascript'
import 'ace-builds/src-noconflict/mode-python'
import 'ace-builds/src-noconflict/mode-java'
import 'ace-builds/src-noconflict/mode-c_cpp'
import 'ace-builds/src-noconflict/theme-tomorrow_night'
import 'ace-builds/src-noconflict/ext-language_tools'

const myClasses = ref([])
const loading = ref(false)
const dueAt = ref('')
const starterRef = ref(null)
const solutionRef = ref(null)
let starterEditor = null
let solutionEditor = null
const router=useRouter(),draftKey=teacherStorageKey('task-draft:v1'),savedAt=ref(0),draftError=ref(''),restoredDraft=ref(false),publishedTitle=ref('')
const languageLabels={javascript:'JavaScript',python:'Python',java:'Java',c:'C'}
let draftTimer,disposed=false

const form = ref({
  class_id: '',
  title: '',
  description: '',
  language: 'javascript',
  starter_code: '',
  expected_output: '',
  solution_code: '',
  due_at: ''
})

try{
  const draft=JSON.parse(localStorage.getItem(draftKey) || 'null')
  if(draft?.form){for(const key of Object.keys(form.value)){if(typeof draft.form[key]==='string')form.value[key]=draft.form[key]};if(!languageLabels[form.value.language])form.value.language='javascript';dueAt.value=typeof draft.dueAt==='string'?draft.dueAt:'';savedAt.value=Number(draft.at)||0;restoredDraft.value=true}
}catch{}
const hasContent=computed(()=>!!(form.value.title || form.value.description || form.value.starter_code || form.value.solution_code || form.value.expected_output || dueAt.value))
function saveDraft(){
  clearTimeout(draftTimer)
  try{if(hasContent.value){const at=Date.now();localStorage.setItem(draftKey,JSON.stringify({form:form.value,dueAt:dueAt.value,at}));savedAt.value=at}else{localStorage.removeItem(draftKey);savedAt.value=0};draftError.value='';return true}catch{draftError.value='草稿保存失败，请保持页面打开或复制内容';return false}
}
watch([form,dueAt],()=>{clearTimeout(draftTimer);savedAt.value=0;draftTimer=setTimeout(saveDraft,500)},{deep:true})
function beforeUnload(event){if(!hasContent.value)return;saveDraft();event.preventDefault();event.returnValue=''}
onBeforeRouteLeave(async()=>{if(loading.value){ElMessage.info('正在发布任务，请稍候');return false}if(!hasContent.value)return true;const saved=saveDraft();try{await ElMessageBox.confirm(saved?'当前内容已保存为本地草稿，下次进入可以继续编辑。':'草稿保存失败，离开可能丢失当前内容。','离开任务编辑？',{confirmButtonText:saved?'保留草稿并离开':'仍然离开',cancelButtonText:'继续编辑',type:'warning'});return true}catch{return false}})
async function confirmReset(){if(!hasContent.value)return;try{await ElMessageBox.confirm('将清空当前编辑内容和本地草稿。','重置任务？',{confirmButtonText:'重置',cancelButtonText:'继续编辑',type:'warning'});reset();saveDraft();restoredDraft.value=false}catch{}}

const token = () => getAuthToken()

const getAceMode = (lang) => {
  if (lang === 'javascript') return 'javascript'
  if (lang === 'python') return 'python'
  if (lang === 'java') return 'java'
  if (lang === 'c') return 'c_cpp'
  return 'text'
}

const initEditor = (container, initialValue, onChange) => {
  if (!container) return null
  const langTools = ace.require('ace/ext/language_tools')
  const editor = ace.edit(container, {
    fontSize: 14,
    theme: 'ace/theme/tomorrow_night',
    mode: `ace/mode/${getAceMode(form.value.language)}`,
    showPrintMargin: false,
    useWorker: false,
    wrap: true
  })
  editor.setOptions({
    enableBasicAutocompletion: true,
    enableLiveAutocompletion: true,
    enableSnippets: false
  })
  editor.completers = [
    langTools?.snippetCompleter,
    langTools?.textCompleter,
    langTools?.keyWordCompleter
  ].filter(Boolean)
  editor.setValue(String(initialValue || ''), -1)
  editor.on('change', () => onChange(editor.getValue()))
  return editor
}

const loadClasses = async () => {
  const t = token()
  if (!t) return
  const res = await fetch('/api/classes/mine', {
    headers: { Authorization: `Bearer ${t}` }
  }).catch(() => null)
  const data = res ? await res.json().catch(() => ({})) : {}
  if (!res || !res.ok || data?.success === false) {
    ElMessage.error(data?.detail || data?.message || '加载班级失败')
    return
  }
  myClasses.value = Array.isArray(data?.classes) ? data.classes : []
  if(disposed)return
  if(form.value.class_id && !myClasses.value.some(c=>String(c.id)===String(form.value.class_id)))form.value.class_id=''
  if (!form.value.class_id && myClasses.value.length > 0) {
    form.value.class_id = myClasses.value[0].id
  }
}

const reset = () => {
  form.value = {
    class_id: myClasses.value[0]?.id || '',
    title: '',
    description: '',
    language: 'javascript',
    starter_code: '',
    expected_output: '',
    solution_code: '',
    due_at: ''
  }
  dueAt.value = ''
  if (starterEditor) starterEditor.setValue('', -1)
  if (solutionEditor) solutionEditor.setValue('', -1)
}

const submit = async () => {
  if(loading.value)return
  const t = token()
  if (!t) return
  if (!form.value.class_id) {
    ElMessage.warning('请选择班级')
    return
  }
  if (!form.value.title.trim()) {
    ElMessage.warning('请输入题目标题')
    return
  }

  loading.value = true
  try {
    if (starterEditor) form.value.starter_code = starterEditor.getValue()
    if (solutionEditor) form.value.solution_code = solutionEditor.getValue()
    const payload = {
      ...form.value,
      due_at: dueAt.value || ''
    }
    const res = await fetch('/api/teacher/tasks', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        Authorization: `Bearer ${t}`
      },
      body: JSON.stringify(payload)
    })
    const data = await res.json().catch(() => ({}))
    if (!res.ok || data?.success === false) {
      throw new Error(data?.detail || data?.message || '发布失败')
    }
    publishedTitle.value=form.value.title
    invalidateTeacherState('task-cache:')
    ElMessage.success('发布成功')
    reset()
    saveDraft()
    restoredDraft.value=false
  } catch (e) {
    ElMessage.error(e?.message || '发布失败')
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  window.addEventListener('beforeunload',beforeUnload)
  loadClasses()
  starterEditor = initEditor(starterRef.value, form.value.starter_code, (v) => {
    form.value.starter_code = v
  })
  solutionEditor = initEditor(solutionRef.value, form.value.solution_code, (v) => {
    form.value.solution_code = v
  })
})

watch(() => form.value.language, (lang) => {
  if (starterEditor) starterEditor.session.setMode(`ace/mode/${getAceMode(lang)}`)
  if (solutionEditor) solutionEditor.session.setMode(`ace/mode/${getAceMode(lang)}`)
})

watch(() => form.value.starter_code, (v) => {
  if (!starterEditor) return
  const cur = starterEditor.getValue()
  if (v !== cur) starterEditor.setValue(String(v || ''), -1)
})

watch(() => form.value.solution_code, (v) => {
  if (!solutionEditor) return
  const cur = solutionEditor.getValue()
  if (v !== cur) solutionEditor.setValue(String(v || ''), -1)
})

onBeforeUnmount(() => {
  disposed=true
  clearTimeout(draftTimer)
  if(hasContent.value)saveDraft()
  window.removeEventListener('beforeunload',beforeUnload)
  if (starterEditor) {
    starterEditor.destroy()
    starterEditor = null
  }
  if (solutionEditor) {
    solutionEditor.destroy()
    solutionEditor = null
  }
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

.card {
  border-radius: 12px;
}

.code-editor {
  width: 100%;
  height: 220px;
  border: 1px solid #dcdfe6;
  border-radius: 8px;
  overflow: hidden;
}
.task-compose-layout{display:grid;grid-template-columns:minmax(0,1fr) minmax(260px,340px);gap:20px;align-items:start}.draft-toolbar{display:flex;justify-content:space-between;align-items:center;gap:12px;color:#d2bddf;font-size:12px;padding:0 4px 14px}.draft-toolbar small{display:block;margin-top:5px;color:#b9e0cb;font-size:11px}.task-preview{position:sticky;top:90px;background:#faf7fd;border-radius:16px;overflow:hidden;border:1px solid #d8c4e9;color:#4e3b61;box-shadow:0 14px 40px #100a2522}.preview-heading{display:flex;justify-content:space-between;align-items:center;padding:16px 20px;border-bottom:1px solid #eee5f5}.preview-heading>span{font:10px Consolas,monospace;letter-spacing:1.5px;color:#9678b2}.preview-body{padding:22px}.preview-meta{display:flex;gap:10px;align-items:center;font-size:11px;color:#a28eae}.preview-body h2{font-size:21px;line-height:1.5;overflow-wrap:anywhere}.preview-body>p{white-space:pre-wrap;font-size:13px;line-height:1.9;overflow-wrap:anywhere;color:#8f7b9f;min-height:70px}.preview-code{border:1px solid #e7deef;border-radius:10px;overflow:hidden}.preview-code>span{display:block;font-size:11px;background:#eee7f5;padding:8px 12px}.preview-code pre{margin:0;background:#211a34;color:#d9d2e8;padding:15px;max-height:230px;overflow:auto;white-space:pre-wrap;overflow-wrap:anywhere;font:12px/1.7 Consolas,monospace}.preview-deadline{font-size:11px;color:#a086b5;margin-top:18px}.preview-footer{display:flex;justify-content:space-between;align-items:center;border-top:1px solid #eee5f5;padding-top:18px;margin-top:24px;font-size:11px;color:#aa95b9}.preview-start{padding:8px 12px;background:#9a79b9;color:#fff;border-radius:8px}.preview-tip{font-size:11px;color:#a08daf;line-height:1.8;padding:0 22px 20px}.task-publish-success{display:flex;gap:16px;align-items:center;padding:20px;margin-bottom:18px;background:#eaf6ee;color:#40785a;border-radius:14px}.task-publish-success>span{width:38px;height:38px;display:grid;place-items:center;background:#d4eddf;border-radius:50%;font-size:20px}.task-publish-success strong{font-size:14px}.task-publish-success p{font-size:12px;margin:5px 0 0}.task-publish-success .el-button{margin-left:auto}.publish-result-enter-active,.publish-result-leave-active{transition:opacity .3s,transform .3s}.publish-result-enter-from,.publish-result-leave-to{opacity:0;transform:translateY(-12px) scale(.98)}
@media(max-width:1000px){.task-compose-layout{grid-template-columns:minmax(0,1fr) 280px}}@media(max-width:800px){.task-compose-layout{grid-template-columns:1fr}.task-preview{position:static}.task-publish-success{flex-wrap:wrap}.task-compose-layout :deep(.el-form-item){display:block}.task-compose-layout :deep(.el-form-item__content){margin-left:0!important}.task-compose-layout :deep(.el-form-item__label){float:none;justify-content:flex-start}}
</style>
