<template>
  <div class="home-page">
    <!-- 顶部导航栏 -->
    <el-header class="main-header">
      <div class="header-content">
        <div><h1 class="title-text">慧编云</h1><p class="home-intro">从一行代码开始，让想法慢慢成形。</p></div>
        <div class="code-decoration" aria-hidden="true">
          <div class="code-decoration-top"><span></span><span></span><span></span><small>hello, {{ currentLang }}</small></div>
          <div class="code-decoration-line"><em>01</em><span class="code-keyword">learn</span><span>(<b>'保持好奇'</b>);</span></div>
          <div class="code-decoration-line"><em>02</em><span class="code-keyword">practice</span><span>(<b>'勇于尝试'</b>);</span></div>
          <div class="code-decoration-line"><em>03</em><span class="code-comment">// 每一次尝试，都是进步</span><span class="code-caret">▍</span></div>
        </div>
      </div>
    </el-header>
    
    <!-- 主内容区 -->
    <el-container>
      <!-- 左侧侧边栏 -->
      <el-aside width="220px" class="lang-aside">
        <div class="aside-header">
          <span>选择编程语言</span>
        </div>
        <el-menu
          :default-active="currentLang"
          class="lang-menu"
          @select="handleLangSelect"
          background-color="rgba(255, 255, 255, 0.9)"
          text-color="#333"
          active-text-color="#4096ff"
        >
          <el-menu-item index="javascript">
            <span>JavaScript</span>
          </el-menu-item>
          <el-menu-item index="python">
            <span>Python</span>
          </el-menu-item>
          <el-menu-item index="java">
            <span>Java</span>
          </el-menu-item>
          <el-menu-item index="c">
            <span>C</span>
          </el-menu-item>
        </el-menu>
        <Transition name="language-tip" mode="out-in">
          <div :key="currentLang" class="language-tip">
            <span class="tip-label">{{ languageGuide.label }} · 小提示</span>
            <p>{{ languageGuide.tip }}</p>
            <code>{{ languageGuide.example }}</code>
            <button @click="focusEditor">动手试试 <span aria-hidden="true">→</span></button>
          </div>
        </Transition>
        <CodeIllustration class="sidebar-code-art" variant="network" />
      </el-aside>

      <!-- 右侧主内容 -->
      <el-main class="main-content">
        <el-row :gutter="24">
          <!-- 代码编辑器卡片 -->
          <el-col :span="12">
            <div class="content-card editor-card">
              <div class="card-header">
                <h3 class="card-title">代码编辑器 ({{ currentLang }})</h3>
                <el-button plain class="card-action" @click="clearCode">清空代码</el-button>
              </div>
              <div class="card-body">
                <div ref="editorRef" class="monaco-editor-box"></div>
                <CodeConsole
                  class="code-result-area"
                  :text="runResult"
                  :running="running"
                  :accepting-input="acceptingInput"
                  :status="consoleStatus"
                  @input="sendInput"
                  @eof="endInput"
                  @stop="stopConsole"
                  @clear="clearConsole"
                />
              </div>
              <div class="card-footer">
                <el-button size="small" type="primary" @click="formatCode">格式化代码</el-button>
                <el-button size="small" type="success" :disabled="running" @click="runCode">{{ running ? '运行中...' : '运行代码' }}</el-button>
                <el-button size="small" type="info" @click="exportCode">导出代码</el-button>
              </div>
            </div>
          </el-col>

          <!-- AI问答卡片 -->
          <el-col :span="12">
            <div class="content-card">
              <div class="card-header">
                <h3 class="card-title">AI编程助手</h3>
                <el-button plain class="card-action" @click="clearChat">清空对话</el-button>
              </div>
              <div class="card-body">
                <AiChat :error-context="recentAiError" />
              </div>
              <div class="card-footer ai-tips">
                <el-tag size="small" type="info">支持：代码解释、Bug修复、逻辑优化、语法讲解</el-tag>
              </div>
            </div>
          </el-col>
        </el-row>
      </el-main>
    </el-container>
    <StudyToolkit on-purple />

    <!-- 底部信息 -->
    <el-footer class="main-footer">
      <p>© 2026 慧编云 - 让编程学习更简单</p>
    </el-footer>
  </div>
</template>

<script setup>
import { computed, ref, onMounted, onUnmounted, watch } from 'vue'
import { useAiStore } from '@/store/aiStore'
import AiChat from '@/components/AIChat.vue'
import StudyToolkit from '@/components/StudyToolkit.vue'
import CodeIllustration from '@/components/CodeIllustration.vue'
import CodeConsole from '@/components/CodeConsole.vue'
import { useCodeConsole } from '@/composables/useCodeConsole'
import { ElMessage, ElMessageBox } from 'element-plus'
import ace from 'ace-builds'
import 'ace-builds/src-noconflict/mode-javascript'
import 'ace-builds/src-noconflict/mode-python'
import 'ace-builds/src-noconflict/mode-java'
import 'ace-builds/src-noconflict/mode-c_cpp'
import 'ace-builds/src-noconflict/theme-tomorrow_night'
import 'ace-builds/src-noconflict/ext-language_tools'
import { getCurrentUser } from '@/utils/authStorage'

const aiStore = useAiStore()
const currentLang = computed(() => aiStore.currentLang)
const {
  transcript: runResult, input: runInput, running, acceptingInput, status: consoleStatus,lastRun,
  run: runConsole, sendInput, endInput, stop: stopConsole, clear: clearConsole
} = useCodeConsole()
const recentAiError=computed(()=>String(lastRun.value?.request?.student_id || 'guest')===aiStore.ownerId && lastRun.value?.request?.lang===currentLang.value?String(lastRun.value?.result?.error || ''):'')
const editorRef = ref(null)
let aceEditor = null
const languageGuide = computed(() => ({
  javascript: { label: 'JavaScript', tip: '用 console.log() 观察变量的值，把运行过程变得看得见。', example: 'console.log("Hello!")' },
  python: { label: 'Python', tip: '缩进也是语法的一部分，同一个代码块请保持一致的缩进。', example: 'print("Hello!")' },
  java: { label: 'Java', tip: '注意类名、方法名的大小写，语句结束时别忘了分号。', example: 'System.out.println("Hello!");' },
  c: { label: 'C', tip: '先核对变量类型，再检查输入与输出的格式是否匹配。', example: 'printf("Hello!\\n");' }
}[currentLang.value] || { label: currentLang.value, tip: '先写一个最小示例，看看运行结果。', example: '// Hello, world!' }))
function focusEditor() {
  editorRef.value?.scrollIntoView({ block: 'center', behavior: 'smooth' })
  aceEditor?.focus()
}

const buildCodeContext = (raw) => {
  const code = String(raw || '')
  const max = 20000
  if (code.length <= max) return code
  const headLen = Math.floor(max * 0.6)
  const tailLen = max - headLen
  const head = code.slice(0, headLen)
  const tail = code.slice(code.length - tailLen)
  return `${head}\n\n...（代码过长，已省略中间部分）...\n\n${tail}`
}

const autoReviewing = ref(false)
const lastAutoReviewKey = ref('')
const lastAutoReviewAt = ref(0)
let homeActive=true,homeReviewController
onUnmounted(()=>{homeActive=false;homeReviewController?.abort()})

const triggerAutoReview = async ({ lang, code, errorText }) => {
  const err = String(errorText || '').trim()
  if (!err) return

  const now = Date.now()
  const key = `${String(lang || '')}|${err.slice(0, 180)}`
  if (autoReviewing.value) return
  if (key === lastAutoReviewKey.value && now - Number(lastAutoReviewAt.value || 0) < 12000) return
  lastAutoReviewKey.value = key
  lastAutoReviewAt.value = now

  autoReviewing.value = true
  aiStore.ensureOwner(getCurrentUser()?.id)
  const reviewOwner=String(getCurrentUser()?.id || 'guest')
  const idx = aiStore.chatHistory.push({ role: 'assistant', content: '' }) - 1
  const reviewTarget=aiStore.chatHistory[idx]
  const controller = new AbortController()
  homeReviewController=controller
  const timeoutId = setTimeout(() => controller.abort(), 3800)
  try {
    const res = await fetch('/api/ai/auto-review', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        language: lang,
        code: buildCodeContext(code),
        error: err,
        input: runInput.value || '',
        expected_output: ''
      }),
      signal: controller.signal
    })
    const data = await res.json().catch(() => ({}))
    if(!homeActive || reviewOwner!==String(getCurrentUser()?.id || 'guest') || aiStore.chatHistory[idx]!==reviewTarget)return
    reviewTarget.provider=data.provider==='local'?'本地规则':data.provider || '本地规则'
    if (!res.ok) {
      const detail = String(data?.detail || data?.message || data?.error || `${res.status} ${res.statusText}`)
      aiStore.chatHistory[idx].content = `自动排查暂不可用：${detail}。可以把错误信息发送给编程助手重试。`
      return
    }
    const quick = String(data?.quick || '').trim()
    const ai = String(data?.ai || '').trim()
    const combined = [quick, ai].filter(Boolean).join('\n\n').trim()
    aiStore.chatHistory[idx].content = combined || '我已收到错误信息，但AI暂时无法生成分析。'
  } catch {
    if(!homeActive || reviewOwner!==String(getCurrentUser()?.id || 'guest') || aiStore.chatHistory[idx]!==reviewTarget)return
    aiStore.chatHistory[idx].content = '我检测到运行失败，但AI分析请求超时/失败。你可以把报错信息发给我，我来帮你定位。'
  } finally {
    clearTimeout(timeoutId)
    autoReviewing.value = false
  }
}

const getAceMode = (lang) => {
  if (lang === 'javascript') return 'javascript'
  if (lang === 'python') return 'python'
  if (lang === 'java') return 'java'
  if (lang === 'c') return 'c_cpp'
  return 'text'
}

const initEditor = () => {
  if (!editorRef.value || aceEditor) return

  const langTools = ace.require('ace/ext/language_tools')

  const pythonSuggestions = [
    'print', 'def', 'class', 'return', 'import', 'from', 'as', 'if', 'elif', 'else',
    'for', 'while', 'break', 'continue', 'try', 'except', 'finally', 'with',
    'True', 'False', 'None', 'and', 'or', 'not', 'is', 'in',
    'range', 'len', 'input', 'int', 'str', 'float', 'list', 'dict', 'set', 'tuple'
  ]
  const jsSuggestions = [
    'console.log', 'function', 'const', 'let', 'var', 'if', 'else', 'for', 'while', 'return',
    'document', 'window', 'Math', 'JSON', 'Array', 'String', 'Number', 'Boolean'
  ]
  const javaSuggestions = [
    'public', 'class', 'static', 'void', 'main', 'System.out.println', 'if', 'else',
    'for', 'while', 'return', 'new', 'import', 'package', 'private', 'protected'
  ]
  const cSuggestions = [
    '#include', 'int', 'char', 'float', 'double', 'void', 'return', 'if', 'else',
    'for', 'while', 'printf', 'scanf', 'strlen', 'malloc', 'free', 'struct'
  ]

  const customCompleter = {
    getCompletions: (editor, session, pos, prefix, callback) => {
      if (!prefix) return callback(null, [])
      const lang = currentLang.value
      const list =
        lang === 'python'
          ? pythonSuggestions
          : lang === 'java'
            ? javaSuggestions
            : lang === 'c'
              ? cSuggestions
              : jsSuggestions
      callback(null, list.map((value) => ({ caption: value, value, meta: lang, score: 2000 })))
    }
  }

  const completers = [
    customCompleter,
    langTools?.textCompleter,
    langTools?.keyWordCompleter
  ].filter(Boolean)

  aceEditor = ace.edit(editorRef.value, {
    fontSize: 14,
    theme: 'ace/theme/tomorrow_night',
    mode: `ace/mode/${getAceMode(currentLang.value)}`,
    showPrintMargin: false,
    useWorker: false,
    wrap: true
  })

  aceEditor.completers = completers
  aceEditor.setOptions({
    enableBasicAutocompletion: completers,
    enableLiveAutocompletion: completers,
    enableSnippets: false
  })

  aceEditor.setValue(aiStore.currentCode || '', -1)
  aceEditor.on('change', () => {
    aiStore.updateCurrentCode(aceEditor.getValue())
  })
}

// 监听语言变化更新编辑器
watch(currentLang, (newLang) => {
  if (aceEditor && newLang) {
    aceEditor.session.setMode(`ace/mode/${getAceMode(newLang)}`)
  }
})

// 监听store代码变化同步到编辑器
watch(() => aiStore.currentCode, (newCode) => {
  if (aceEditor) {
    const currentValue = aceEditor.getValue()
    if (newCode !== currentValue) {
      aceEditor.setValue(newCode || '', -1)
    }
  }
}, { immediate: true })

// 生命周期
onMounted(() => {
  initEditor()
})

onUnmounted(() => {
  if (aceEditor) {
    aceEditor.destroy()
    aceEditor = null
  }
})

// 切换编程语言
const handleLangSelect = (lang) => {
  aiStore.updateCurrentLang(lang)
}

// 清空代码
const clearCode = () => {
  aiStore.updateCurrentCode('')
  if (aceEditor) {
    aceEditor.setValue('', -1)
  }
  ElMessage.info('代码已清空')
}

// 清空聊天记录
const clearChat = () => {
  aiStore.clearChatHistory()
  ElMessage.info('聊天记录已清空')
}

// 格式化代码
const formatCode = () => {
  const code = aiStore.currentCode
  if (!code) return ElMessage.warning('请先输入代码')

  try {
    const lines = code.split('\n')
    const formattedLines = lines.map(line => {
      return line.trim() ? `  ${line}` : line
    })
    const formattedCode = formattedLines.join('\n')
    
    aiStore.updateCurrentCode(formattedCode)
    if (aceEditor) {
      aceEditor.setValue(formattedCode, -1)
    }
    ElMessage.success('代码格式化成功')
  } catch (err) {
    ElMessage.error('格式化失败，请检查代码')
  }
}

// 运行代码
const runCode = async () => {
  const code = aiStore.currentCode
  const lang = currentLang.value
  if (running.value) return
  if (!code) {
    ElMessage.warning('请先输入代码')
    return
  }

  try {
    let studentId = 'guest'
    let studentName = '游客'

    const user = getCurrentUser()
    if (user?.id) studentId = user.id
    if (user?.name) studentName = user.name

    if (studentId === 'guest') {
      studentId = localStorage.getItem('currentUserId') || 'guest'
      studentName = localStorage.getItem('currentUserName') || '游客'
    }

    const data = await runConsole({
        student_id: studentId,
        student_name: studentName,
        problem_id: 'sandbox',
        lang,
        code
    })

    if (!data || data.cancelled) return
    
    if (data.success) {
      ElMessage.success(`${lang}代码运行成功`)
      recordRun({ lang, success: true, error: null })
    } else {
      ElMessage.error(`${lang}代码运行失败`)
      triggerAutoReview({ lang, code, errorText: data.error })
      showRunErrorDialog({ lang, errorText: data.error })
      recordRun({ lang, success: false, error: data.error })
    }
  } catch (err) {
    runResult.value = `❌ 请求失败：\n\n${err.message}\n\n提示：请先启动后端代码运行服务`
    ElMessage.error('代码运行请求失败')
    triggerAutoReview({ lang, code, errorText: err.message })
    showRunErrorDialog({ lang, errorText: err.message })
    recordRun({ lang, success: false, error: err.message })
  }
}

const escapeHtml = (str) => {
  return String(str || '')
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#39;')
}

const errorTypeLabel = (type) => {
  const map = {
    SyntaxError: '语法错误',
    IndentationError: '缩进错误',
    NameError: '名称未定义',
    ReferenceError: '引用未定义',
    TypeError: '类型错误',
    IndexError: '越界错误',
    NullPointerException: '空指针异常',
    CompilationError: '编译错误',
    ModuleNotFoundError: '模块未找到',
    Timeout: '超时',
    RuntimeError: '运行错误',
    Unknown: '未知错误'
  }
  return map[type] || String(type || '未知错误')
}

const classifyErrorType = (lang, errorText) => {
  const text = String(errorText || '')
  if (!text) return 'Unknown'

  const rules = [
    { type: 'Timeout', re: /(timeout|超时)/i },
    { type: 'IndentationError', re: /(IndentationError|unexpected indent)/i },
    { type: 'SyntaxError', re: /(SyntaxError|invalid syntax)/i },
    { type: 'NameError', re: /(NameError|ReferenceError|is not defined)/i },
    { type: 'TypeError', re: /TypeError/i },
    { type: 'IndexError', re: /(IndexError|out of range)/i },
    { type: 'NullPointerException', re: /NullPointerException/i },
    { type: 'CompilationError', re: /(error:|javac|gcc|compilation|编译失败)/i }
  ]

  for (const r of rules) {
    if (r.re.test(text)) return r.type
  }
  if (lang === 'python' && /ModuleNotFoundError/i.test(text)) return 'ModuleNotFoundError'
  return 'RuntimeError'
}

const getStatsStorageKey = () => {
  const user = getCurrentUser()
  const userId = user?.id || 'guest'
  return `codeRunStats_${userId}`
}

const loadRunStats = () => {
  const raw = localStorage.getItem(getStatsStorageKey())
  if (!raw) {
    return { totalRuns: 0, successRuns: 0, errorRuns: 0, errors: {}, byLang: {}, lastRun: null }
  }
  try {
    const parsed = JSON.parse(raw)
    return {
      totalRuns: parsed.totalRuns || 0,
      successRuns: parsed.successRuns || 0,
      errorRuns: parsed.errorRuns || 0,
      errors: parsed.errors || {},
      byLang: parsed.byLang || {},
      lastRun: parsed.lastRun || null
    }
  } catch {
    return { totalRuns: 0, successRuns: 0, errorRuns: 0, errors: {}, byLang: {}, lastRun: null }
  }
}

const recordRun = ({ lang, success, error }) => {
  const stats = loadRunStats()
  const now = new Date().toISOString()

  stats.totalRuns += 1
  if (!stats.byLang[lang]) {
    stats.byLang[lang] = { totalRuns: 0, successRuns: 0, errorRuns: 0, errors: {} }
  }
  stats.byLang[lang].totalRuns += 1

  if (success) {
    stats.successRuns += 1
    stats.byLang[lang].successRuns += 1
    stats.lastRun = { lang, success: true, time: now }
  } else {
    stats.errorRuns += 1
    stats.byLang[lang].errorRuns += 1
    const errorType = classifyErrorType(lang, error)
    stats.errors[errorType] = (stats.errors[errorType] || 0) + 1
    stats.byLang[lang].errors[errorType] = (stats.byLang[lang].errors[errorType] || 0) + 1
    stats.lastRun = { lang, success: false, errorType, time: now }
  }

  localStorage.setItem(getStatsStorageKey(), JSON.stringify(stats))
  window.dispatchEvent(new Event('code-run-stats-updated'))
}

const extractLineNumber = (errorText) => {
  const text = String(errorText || '')
  const patterns = [
    /line\s+(\d+)/i,
    /第\s*(\d+)\s*行/,
    /:(\d+):(\d+)/,
    /<anonymous>:(\d+):(\d+)/
  ]
  for (const re of patterns) {
    const m = text.match(re)
    if (m && m[1]) return Number(m[1])
  }
  return null
}

const buildErrorHelp = (lang, errorType, errorText) => {
  const line = extractLineNumber(errorText)
  const title = `${errorTypeLabel(errorType)}（${lang}）`

  const suggestionsMap = {
    SyntaxError: ['检查括号/引号是否成对', '检查关键字拼写与语句结尾（如分号）', '逐行注释定位出错行'],
    IndentationError: ['检查缩进是否一致（不要混用 Tab 和空格）', '检查 if/for/def/class 后是否有缩进块', '把出错行及其上下各两行一起检查'],
    NameError: ['变量/函数是否先定义再使用', '检查大小写和拼写是否一致', '注意作用域（函数内外的变量）'],
    ReferenceError: ['变量/函数是否先定义再使用', '检查大小写和拼写是否一致', '确认对象属性名是否存在'],
    TypeError: ['打印变量类型确认是否符合预期', '检查函数参数数量/类型是否正确', '检查是否对 null/undefined 调用了方法'],
    IndexError: ['检查下标是否越界', '循环条件是否写成 < length', '访问前先判断数组/列表长度'],
    NullPointerException: ['先判断对象是否为 null', '确认对象已初始化再调用方法', '检查链式调用中间是否为空'],
    CompilationError: ['先解决第一条编译错误再继续', '检查缺少分号/括号/头文件', 'Java 确保类名与文件名要求一致（或使用 Main）'],
    ModuleNotFoundError: ['检查模块名是否拼写正确', '确认依赖是否已安装（pip install ...）', '确认运行环境与安装环境一致'],
    Timeout: ['检查是否出现死循环', '优化算法复杂度（减少嵌套循环）', '给循环增加合理的终止条件'],
    RuntimeError: ['查看报错堆栈的第一处出错位置', '先用最小输入复现问题', '逐步打印关键变量定位异常点'],
    Unknown: ['查看完整错误信息', '从第一条报错开始排查', '提供代码与报错信息以便进一步分析']
  }
  const suggestions = suggestionsMap[errorType] || suggestionsMap.Unknown
  const errorBlock = escapeHtml(errorText || '无错误信息')
  const lineText = line ? `（大概率在第 ${line} 行附近）` : ''

  const html = `
    <div style="line-height:1.7">
      <div style="font-weight:600;margin-bottom:6px">检测到的问题：${escapeHtml(errorTypeLabel(errorType))}${escapeHtml(lineText)}</div>
      <div style="margin:8px 0 6px;font-weight:600">建议排查：</div>
      <ul style="margin:0;padding-left:18px">
        ${suggestions.map(s => `<li>${escapeHtml(s)}</li>`).join('')}
      </ul>
      <div style="margin:10px 0 6px;font-weight:600">原始错误：</div>
      <pre style="margin:0;white-space:pre-wrap;background:#0f172a;color:#e5e7eb;padding:10px;border-radius:8px;max-height:220px;overflow:auto">${errorBlock}</pre>
    </div>
  `
  return { title, html }
}

const showRunErrorDialog = async ({ lang, errorText }) => {
  const errorType = classifyErrorType(lang, errorText)
  const { title, html } = buildErrorHelp(lang, errorType, errorText)
  await ElMessageBox.alert(html, title, {
    confirmButtonText: '知道了',
    dangerouslyUseHTMLString: true,
    customClass: 'run-error-dialog'
  })
}

// 导出代码
const exportCode = () => {
  const code = aiStore.currentCode
  if (!code) return ElMessage.warning('请先输入代码')

  const blob = new Blob([code], { type: 'text/plain;charset=utf-8' })
  const downloadLink = document.createElement('a')
  downloadLink.href = URL.createObjectURL(blob)
  const fileName = `编程代码_${currentLang.value}_${new Date().getTime()}.txt`
  downloadLink.download = fileName
  downloadLink.click()
  URL.revokeObjectURL(downloadLink.href)
  
  ElMessage.success(`代码已导出：${fileName}`)
}
</script>

<style scoped>
.sidebar-code-art { color: #e6d9ff; opacity: .65; width: 100%; max-width: 210px; margin: 32px auto 0; }
@media (max-width: 768px) { .sidebar-code-art { display: none; } }
.main-header { height: auto; }
.header-content { display: flex; align-items: center; justify-content: space-between; gap: 24px; padding-right: 24px; }
.home-intro { color: #f0edff; font-size: 14px; line-height: 1.7; }
.code-decoration { flex-shrink: 0; width: 300px; padding: 14px 18px; border: 1px solid #ffffff40; background: #23174c24; border-radius: 13px; box-shadow: 0 10px 24px #211b5512; transform: rotate(-2deg); transition: transform 220ms; }
.code-decoration-top { display: flex; align-items: center; gap: 5px; margin-bottom: 12px; }
.code-decoration-top > span { width: 6px; height: 6px; border-radius: 50%; background: #f3c9df; }
.code-decoration-top > span:nth-child(2) { background: #e8dbad; }
.code-decoration-top > span:nth-child(3) { background: #b5e8d3; }
.code-decoration-top small { margin-left: auto; color: #e2d9ff; font: 10px Consolas, monospace; }
.code-decoration-line { display: flex; align-items: center; gap: 2px; font: 12px/1.9 Consolas, 'Microsoft YaHei', monospace; color: #f5eeff; }
.code-decoration-line em { color: #ccc1eb; margin-right: 14px; font-style: normal; font-size: 10px; }
.code-decoration-line b { font-weight: normal; color: #f6d1ac; }
.code-keyword { color: #c6e5ff; }
.code-comment { color: #ded3f4; }
.code-caret { animation: code-cursor 800ms step-end 3; color: #e4d3ff; }
@keyframes code-cursor { 50% { opacity: 0; } }
.language-tip { margin-top: 24px; border: 1px solid #ffffff36; border-radius: 12px; background: #ffffff0c; padding: 16px; color: #fff; }
.tip-label { display: block; font-size: 12px; font-weight: 600; }
.language-tip p { font-size: 12px; line-height: 1.9; color: #f0edff; margin: 12px 0; }
.language-tip code { display: block; font: 10px/1.8 Consolas, monospace; overflow-wrap: anywhere; color: #f5dbbe; }
.language-tip button { margin-top: 14px; padding: 6px 0; background: transparent; border: 0; color: #fff; font: inherit; font-size: 12px; cursor: pointer; }
.language-tip button span { display: inline-block; transition: transform 180ms; }
.language-tip button:hover span { transform: translateX(4px); }
.language-tip-enter-active, .language-tip-leave-active { transition: opacity 130ms, transform 130ms; }
.language-tip-enter-from, .language-tip-leave-to { opacity: 0; transform: translateY(5px); }
.content-card:focus-within { box-shadow: 0 0 0 2px #b6a0ec, 0 8px 24px #30216522; }
.lang-menu :deep(.el-menu-item) { transition: background-color 180ms, padding-left 180ms; }
@media (hover: hover) { .code-decoration:hover { transform: rotate(0); } .lang-menu :deep(.el-menu-item:hover) { padding-left: 26px !important; } }
@media (max-width: 768px) {
  .code-decoration { display: none; }
  .header-content { padding-right: 20px; }
  .home-page > .el-container { flex-direction: column; }
  .home-page .lang-aside { width: 100% !important; padding: 12px 20px; }
  .lang-menu { display: flex; flex-wrap: wrap; }
  .lang-menu :deep(.el-menu-item) { padding: 0 14px !important; }
  .language-tip { margin-top: 12px; }
  .language-tip code { display: inline-block; margin-right: 16px; }
  .home-page .main-content :deep(.el-col-12) { max-width: 100%; flex: 0 0 100%; margin-bottom: 20px; }
  .card-footer { flex-wrap: wrap; }
  .ai-tips :deep(.el-tag) { white-space: normal; height: auto; line-height: 1.8; }
}
.home-page {
  height: 100%;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
}

.main-header {
  background-color: transparent;
  border-bottom: none;
  padding: 20px 0;
  box-shadow: none;
  text-align: left;
  position: relative;
  z-index: 998;
}

.header-content {
  text-align: left;
  padding-left: 20px;
}

.title-text {
  font-size: 42px;
  font-weight: 700;
  color: #ffffff;
  margin: 0 0 8px 0;
  letter-spacing: 1px;
}

.lang-aside {
  background-color: transparent;
  padding: 20px 10px;
  display: flex;
  flex-direction: column;
}

.aside-header {
  color: white;
  font-size: 16px;
  font-weight: 500;
  margin-bottom: 16px;
  padding: 0 12px;
}

.lang-menu {
  border-radius: 12px;
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.1);
}

.main-content {
  padding: 24px;
  background-color: transparent;
  margin-top: 0;
}

.content-card {
  background: rgba(255, 255, 255, 0.95);
  border-radius: 16px;
  box-shadow: 0 6px 20px rgba(0, 0, 0, 0.1);
  overflow: hidden;
  height: 700px;
  display: flex;
  flex-direction: column;
  transition: all 0.3s ease;
}

.content-card:hover {
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.15);
  transform: translateY(-2px);
}

.card-header {
  padding: 16px 20px;
  border-bottom: 1px solid #f0f2f5;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.card-title {
  margin: 0;
  font-size: 18px;
  font-weight: 600;
  color: #2c3e50;
}

.card-action {
  color: #909399;
  transition: color 0.2s;
}

.card-action:hover {
  color: #4096ff;
}

.card-body {
  flex: 1;
  padding: 20px;
  overflow: hidden;
  display: flex;
  flex-direction: column;
  gap: 16px;
}

/* 恢复原来高度：上面 350px */
.monaco-editor-box {
  width: 100%;
  height: 350px;
  border-radius: 8px;
  overflow: hidden;
}

.code-result-area { flex: 1; min-height: 180px; }
.monaco-editor-box { flex-shrink: 0; }

.card-footer {
  padding: 12px 20px;
  border-top: 1px solid #f0f2f5;
  display: flex;
  gap: 8px;
  align-items: center;
}

.ai-tips {
  justify-content: center;
}

.main-footer {
  text-align: center;
  padding: 16px;
  background-color: rgba(255, 255, 255, 0.9);
  color: #666;
  font-size: 14px;
  border-top: 1px solid #e8f4ff;
}

/* 响应式恢复原样 */
@media (max-width: 1200px) {
  .title-text {
    font-size: 36px;
  }
  .content-card {
    height: 600px;
  }
  .monaco-editor-box {
    height: 250px;
  }
}

@media (max-width: 768px) {
  .lang-aside {
    width: 180px !important;
  }
  .title-text {
    font-size: 28px;
  }
  .content-card {
    height: 500px;
  }
  .monaco-editor-box {
    height: 200px;
  }
}
</style>

<style>
.run-error-dialog .el-message-box__message {
  width: 100%;
}
</style>
