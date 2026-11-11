<template>
  <div class="learn-container" :class="{'practice-focused':focusMode}">
    <div class="learn-header"><div class="practice-topline"><span class="practice-eyebrow">{{ isCompetitionMode ? 'CODE CHALLENGE' : currentExercise.fromWrongQuestions ? 'DEBUG & UNDERSTAND' : 'DAILY CODING PRACTICE' }}</span><button v-if="!isCompetitionMode" class="practice-back" @click="returnToPractice">← {{ currentExercise.fromWrongQuestions ? '返回错题本' : '返回每日打卡' }}</button></div>
      <h1>{{ isCompetitionMode ? '班级测试答题' : 'AI 辅助编程学习平台' }}</h1>
      <button v-if="!isCompetitionMode" class="progress-bar" @click="goToLearningCenter" title="点击查看学习中心">
        <span>今日练习进度：{{ progress }}% （点击前往学习中心）</span>
        <span class="progress">
          <span class="progress-fill" :style="{ width: `${progress}%` }"></span>
        </span>
      </button>
      <div class="practice-flow" aria-label="练习步骤"><span>01 理解题意</span><i aria-hidden="true">→</i><span :class="{active:userCode.trim()}">02 编写代码</span><i aria-hidden="true">→</i><span :class="{active:hasTried || running}">03 运行验证</span><i aria-hidden="true">→</i><span :class="{active:progress>=100}">04 {{ progress>=100 ? '已完成' : '提交巩固' }}</span></div>
    </div>

    <div class="learn-content" :class="{ 'single-col': isCompetitionMode || focusMode }">
      <div class="editor-section">
        <div class="exercise-brief"><h2>{{ isCompetitionMode ? '题目：' : '今日练习：' }}{{ currentExercise.title }}</h2>
        <p class="exercise-desc">{{ currentExercise.description }}</p></div>
        <div class="practice-editor-toolbar"><span><i></i>{{ language.toUpperCase() }} <small>练习工作区</small></span><div><button aria-label="减小代码字号" :disabled="editorFont<=12" @click="resizeFont(-1)">A−</button><span>{{ editorFont }}px</span><button aria-label="增大代码字号" :disabled="editorFont>=22" @click="resizeFont(1)">A+</button><button v-if="!isCompetitionMode" :aria-pressed="focusMode" @click="toggleFocus">{{ focusMode ? '退出专注' : '专注模式' }}</button></div></div>
        <!-- Ace Editor 挂载点 -->
        <div class="code-editor-wrapper">
          <div id="ace-editor" ref="editorRef" style="height: 450px; width: 100%; border-radius: 8px;"></div>
        </div>
        <div class="editor-actions">
          <button @click="runCode" class="run-btn" :disabled="submitting || running">{{ running ? '运行中...' : '运行代码' }}</button>
          <button v-if="isCompetitionMode" @click="saveCompetitionDraft" class="submit-btn" :disabled="submitting">暂存</button>
          <button
            v-if="canSubmit"
            @click="submitCode"
            class="submit-btn"
            :class="{ loading: submitting }"
            :disabled="submitting || running"
          >{{ submitting ? '提交中...' : (isCompetitionMode ? '提交答案' : '提交打卡') }}</button>
          <button v-if="!isCompetitionMode" @click="askAI" class="ai-btn">问 AI</button>
        </div>
        <div class="helper-links" v-if="canShowSolutionLink">
          <button class="solution-link" :disabled="solutionUnlocking" @click="openSolution">
            {{ solutionUnlocking ? '解锁中...' : (isSolutionUnlocked ? '查看参考答案' : `查看参考答案（${solutionCost}积分）`) }}
          </button>
        </div>
        <CodeConsole
          :text="output"
          :running="running"
          :accepting-input="acceptingInput"
          :status="consoleStatus"
          @input="sendInput"
          @eof="endInput"
          @stop="stopConsole"
          @clear="clearConsole"
        />
        <el-dialog v-model="solutionVisible" title="参考答案" width="min(920px,96vw)" append-to-body destroy-on-close>
            <pre class="solution-code">{{ unlockedSolutionCode }}</pre>
            <div class="solution-actions">
              <button class="solution-action" @click="fillSolution">一键填入</button>
              <button class="solution-action primary" @click="copySolution">复制代码</button>
            </div>
        </el-dialog>
      </div>

      <div v-if="!isCompetitionMode" v-show="!focusMode" class="ai-section">
        <h2>AI 编程助手</h2>
        <div class="chat-history">
          <div
            class="chat-message"
            :class="{ 'ai-message': msg.from === 'ai', 'user-message': msg.from === 'user' }"
            v-for="(msg, index) in chatHistory"
            :key="index"
          >
            <template v-if="msg.from === 'ai' && !msg.content && aiLoading && index === chatHistory.length - 1">
              <span class="typing-text">AI 正在思考</span>
              <span class="typing-dots"><span></span><span></span><span></span></span>
            </template>
            <div v-else-if="msg.from === 'ai' && isChatTyping && index === chatTypingIndex" class="message-content" v-text="msg.content"></div>
            <div v-else-if="msg.from === 'ai'" class="message-content ai-markdown"><div v-html="renderAiMarkdown(msg.content)"></div><small v-if="msg.provider" class="assistant-provider">来源：{{ msg.provider }}{{ msg.fallback?' · 备用服务':'' }}</small><button v-if="msg.error" class="chat-retry" :disabled="aiLoading" @click="retryChat(msg)">重试本次问题</button></div>
            <div v-else class="message-content user-text" v-text="msg.content"></div>
          </div>
        </div>
        <div v-if="aiLoading" class="assistant-status"><span>正在等待助手回复…</span><button @click="cancelChat">停止等待</button></div>
        <div class="input-area">
          <textarea
            v-model="aiInput"
            placeholder="请输入你的问题..."
            maxlength="4000"
            @keydown.ctrl.enter.prevent="sendMessage"
            :disabled="aiLoading"
            rows="3"
          ></textarea>
          <button @click="sendMessage" :disabled="aiLoading">{{ aiLoading ? '发送中' : '发送' }}</button>
        </div>
      </div>
    </div>
    <TopicArt v-if="!isCompetitionMode" scene="orbit" />
  </div>
</template>

<script setup>
import TopicArt from '@/components/TopicArt.vue'
import {morphNavigation,takeMotionReturn,findMotionElement} from '@/utils/sharedMotion'
import { ref, nextTick, onMounted, computed, onBeforeUnmount, watch } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import ace from 'ace-builds';
import 'ace-builds/src-noconflict/mode-javascript';
import 'ace-builds/src-noconflict/mode-python';
import 'ace-builds/src-noconflict/mode-java';
import 'ace-builds/src-noconflict/mode-c_cpp';
import 'ace-builds/src-noconflict/theme-tomorrow_night';
import 'ace-builds/src-noconflict/ext-language_tools';
import { ElMessage } from 'element-plus'
import { getAuthToken, getCurrentUser } from '@/utils/authStorage'
import {assistantMarkdown as renderAiMarkdown} from '@/utils/assistantMarkdown'
import {requestAssistant,conversationHistory} from '@/utils/assistantClient'
import 'highlight.js/styles/github-dark.css'
import CodeConsole from '@/components/CodeConsole.vue'
import { useCodeConsole } from '@/composables/useCodeConsole'
import { getStudyDateKey } from '@/utils/studyDate'

const route = useRoute();
const router = useRouter();
const editorRef = ref(null);
let aceEditor = null;
const focusMode=ref(false),editorFont=ref(16)
function resizeFont(delta){editorFont.value=Math.min(22,Math.max(12,editorFont.value+delta));aceEditor?.setFontSize(editorFont.value)}
async function toggleFocus(){focusMode.value=!focusMode.value;await nextTick();aceEditor?.resize()}

const language = computed(() => route.params.language || 'javascript');
const progress = ref(0);
const currentExercise = ref({
  id: '',
  taskId: '',
  title: "实现一个编程题目",
  description: "请在左侧编辑器中编写代码，点击运行查看结果。",
  expectedOutput: '',
  solutionCode: '',
  isTeacherTask: false,
  isCompetition: false,
  competitionId: '',
  competitionName: ''
});
const userCode = ref('');
const {
  transcript: output, input: stdin, running, acceptingInput, status: consoleStatus, lastRun,
  run: runConsole, sendInput, endInput, stop: stopConsole, clear: clearConsole
} = useCodeConsole();
const aiInput = ref('');
const chatHistory = ref([
  { from: 'ai', content: '你好！我是你的AI编程助手，准备好开始今天的学习了吗？' }
]);
const aiLoading = ref(false);
const isChatTyping = ref(false)
const chatTypingIndex = ref(-1)
const solutionVisible = ref(false);
const hasTried = ref(false);
const remotePracticeDone = ref({});
const submitting = ref(false)
let chatTypeTimer = null,chatController=null,chatRequestSequence=0,chatOwner=String(getCurrentUser()?.id || 'guest'),chatActive=true,activeChatReply=null,autoReviewController=null;

const canSubmit = computed(() => !!currentExercise.value?.expectedOutput || !!currentExercise.value?.isTeacherTask || isCompetitionMode.value)

const solutionCost = 20
const solutionUnlocking = ref(false)
const unlockedSolutionCode = ref('')
const solutionUnlockedState = ref(false)
const isCompetitionMode = computed(() => !!currentExercise.value?.isCompetition)
const solutionUnlocked = computed(() => {
  return !!String(unlockedSolutionCode.value || '').trim()
})
const isSolutionUnlocked = computed(() => solutionUnlocked.value || !!solutionUnlockedState.value)
const canShowSolutionLink = computed(() => {
  if (isCompetitionMode.value) return false
  if (currentExercise.value?.isTeacherTask) return true
  return !!String(currentExercise.value?.solutionCode || '').trim()
})

const getSolutionUnlockKey = (kind, key) => {
  const uid = String(getUserId())
  return `solutionUnlocked_${uid}_${String(kind || '')}_${String(key || '')}`
}

const hydrateSolutionUnlockState = (practice) => {
  const uid = String(getUserId())
  if (!uid || uid === 'guest') return
  if (currentExercise.value?.isTeacherTask) {
    const taskId = String(currentExercise.value?.taskId || '').trim()
    if (!taskId) return
    const k = getSolutionUnlockKey('task', taskId)
    const localUnlocked = localStorage.getItem(k) === '1'
    const knownUnlocked = !!practice?.solutionUnlocked || localUnlocked
    solutionUnlockedState.value = knownUnlocked
    if (knownUnlocked) {
      const code = String(practice?.solutionCode || practice?.solution_code || '')
      if (code) unlockedSolutionCode.value = code
    }
    return
  }
  const exId = String(currentExercise.value?.id || '').trim()
  if (!exId) return
  const k = getSolutionUnlockKey('daily', exId)
  const localUnlocked = localStorage.getItem(k) === '1'
  solutionUnlockedState.value = localUnlocked
  if (localUnlocked) {
    unlockedSolutionCode.value = String(currentExercise.value?.solutionCode || '')
  }
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

const startChatTypewriter = (targetIndex, fullText) => {
  if (chatTypeTimer) {
    const previous=chatHistory.value[chatTypingIndex.value]
    if(previous?.fullContent)previous.content=previous.fullContent
    clearInterval(chatTypeTimer);
    chatTypeTimer = null;
  }
  isChatTyping.value = true
  chatTypingIndex.value = targetIndex
  const target=chatHistory.value[targetIndex]
  if(!target)return
  target.fullContent=String(fullText || '')
  const chars = Array.from(target.fullContent);
  let i = 0;
  chatTypeTimer = setInterval(() => {
    i += Math.max(2,Math.ceil(chars.length/45));
    if (chatActive && chatHistory.value.includes(target))target.content=chars.slice(0,i).join('');
    if (i >= chars.length) {
      clearInterval(chatTypeTimer);
      chatTypeTimer = null;
      isChatTyping.value = false
      chatTypingIndex.value = -1
    }
  }, 25);
};

const autoReviewing = ref(false)
const lastAutoReviewKey = ref('')
const lastAutoReviewAt = ref(0)

const triggerAutoReview = async (errText) => {
  if (isCompetitionMode.value) return
  const err = String(errText || '').trim()
  if (!err) return
  const now = Date.now()
  const key = `${String(language.value)}|${String(currentExercise.value?.id || '')}|${err.slice(0, 180)}`
  if (autoReviewing.value) return
  if (key === lastAutoReviewKey.value && now - Number(lastAutoReviewAt.value || 0) < 12000) return
  lastAutoReviewKey.value = key
  lastAutoReviewAt.value = now

  autoReviewing.value = true
  const aiIndex = chatHistory.value.push({ from: 'ai', content: '' }) - 1
  const controller = new AbortController()
  autoReviewController=controller
  const reviewOwner=chatOwner,reviewTarget=chatHistory.value[aiIndex]
  const timeoutId = setTimeout(() => controller.abort(), 3800)
  try {
    const res = await fetch('/api/ai/auto-review', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        language: language.value,
        code: buildCodeContext(userCode.value || ''),
        error: err,
        input: stdin.value || '',
        expected_output: currentExercise.value?.expectedOutput || ''
      }),
      signal: controller.signal
    })
    const data = await res.json().catch(() => ({}))
    if(!chatActive || reviewOwner!==chatOwner || chatHistory.value[aiIndex]!==reviewTarget)return
    reviewTarget.provider=data.provider==='local'?'本地规则':data.provider || '本地规则'
    if (!res.ok) {
      const detail = String(data?.detail || data?.message || data?.error || `${res.status} ${res.statusText}`)
      startChatTypewriter(aiIndex, `自动排查暂不可用：${detail}。可以把错误信息发送给编程助手重试。`)
      return
    }
    const quick = String(data?.quick || '').trim()
    const ai = String(data?.ai || '').trim()
    const combined = [quick, ai].filter(Boolean).join('\n\n').trim() || '我已收到错误信息，但AI暂时无法生成分析。'
    startChatTypewriter(aiIndex, combined)
  } catch {
    if(!chatActive || reviewOwner!==chatOwner || chatHistory.value[aiIndex]!==reviewTarget)return
    startChatTypewriter(aiIndex, '我检测到运行失败，但AI分析请求超时/失败。你可以把报错信息发给我，我来帮你定位。')
  } finally {
    clearTimeout(timeoutId)
    autoReviewing.value = false
  }
}


  const getUserId = () => {
  const user = getCurrentUser()
  if (user?.id) return user.id
  // 兼容旧方式
  const userId = localStorage.getItem('currentUserId');
  if (userId && userId !== 'undefined') return userId;
  return 'guest';
}

// 获取用户名
const getUserName = () => {
  const user = getCurrentUser()
  if (user?.name) return user.name
  if (user?.username) return user.username
  // 兼容旧方式
  const userName = localStorage.getItem('currentUserName');
  if (userName && userName !== 'undefined') return userName;
  return '游客';
}

  // const userRaw = localStorage.getItem('currentUser')
  // if (!userRaw) return 'guest'
  // try {
  //   const user = JSON.parse(userRaw)
  //   return user?.id || 'guest'
  // } catch {
  //   return 'guest'
  // }


const getTodayKey = () => getStudyDateKey()

const getDailyPracticeDoneKey = (exerciseId) => {
  const safeId = String(exerciseId || 'unknown')
  return `dailyPracticeDone_${getUserId()}_${getTodayKey()}_${safeId}`
}

const getCompetitionDraftKey = () => {
  const uid = String(getUserId() || 'guest')
  const cid = String(currentExercise.value?.competitionId || '')
  const tid = String(currentExercise.value?.id || '')
  return `competitionDraft_${uid}_${cid}_${tid}`
}

const getCompetitionSubmittedKey = () => {
  const uid = String(getUserId() || 'guest')
  const cid = String(currentExercise.value?.competitionId || '')
  const tid = String(currentExercise.value?.id || '')
  return `competitionSubmitted_${uid}_${cid}_${tid}`
}

const saveCompetitionDraft = () => {
  if (!isCompetitionMode.value) return
  if (!aceEditor) return
  const code = String(aceEditor.getValue() || '')
  try {
    localStorage.setItem(getCompetitionDraftKey(), code)
  } catch {}
  ElMessage.success('已暂存')
}

const loadRemoteState = async () => {
  const token = getAuthToken()
  if (!token) return
  try {
    const res = await fetch('/api/users/me/state', {
      headers: { 'Authorization': `Bearer ${token}` }
    })
    const data = await res.json().catch(() => ({}))
    if (!res.ok || data?.success === false) return
    const practice = data?.state?.practice_done
    if (practice && typeof practice === 'object') {
      remotePracticeDone.value = practice
    }
  } catch {}
}

const saveRemotePracticeDone = async (dateKey, exerciseId) => {
  const token = getAuthToken()
  if (!token) return
  try {
    const payload = {
      practice_done: {
        [dateKey]: {
          ...(remotePracticeDone.value?.[dateKey] || {}),
          [exerciseId]: true
        }
      }
    }
    const res = await fetch('/api/users/me/state', {
      method: 'PUT',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token}`
      },
      body: JSON.stringify(payload)
    })
    const data = await res.json().catch(() => ({}))
    if (res.ok && data?.success) {
      remotePracticeDone.value = data.state.practice_done || remotePracticeDone.value
    }
  } catch {}
}

const loadProgress = () => {
  const doneKey = getDailyPracticeDoneKey(currentExercise.value.id)
  const localDone = localStorage.getItem(doneKey) === '1'
  const dateKey = getTodayKey()
  const remoteDone = !!(remotePracticeDone.value?.[dateKey]?.[String(currentExercise.value.id || 'unknown')])
  const done = localDone || remoteDone
  progress.value = done ? 100 : 0
}

const getAceMode = (lang) => {
  if (lang === 'javascript') return 'javascript'
  if (lang === 'python') return 'python'
  if (lang === 'java') return 'java'
  if (lang === 'c') return 'c_cpp'
  return 'text'
}

onMounted(() => {
  ace.config.set('basePath', '/ace')

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

  const customCompleter = {
    getCompletions: (editor, session, pos, prefix, callback) => {
      if (!prefix) return callback(null, [])
      const lang = language.value
      const list = lang === 'python' ? pythonSuggestions : (lang === 'java' ? javaSuggestions : jsSuggestions)
      callback(null, list.map((value) => ({ caption: value, value, meta: lang, score: 2000 })))
    }
  }

  const completers = [
    customCompleter,
    langTools.snippetCompleter,
    langTools.textCompleter,
    langTools.keyWordCompleter
  ].filter(Boolean)

  aceEditor = ace.edit(editorRef.value, {
    fontSize: 16,
    theme: 'ace/theme/tomorrow_night',
    mode: `ace/mode/${getAceMode(language.value)}`,
    showPrintMargin: false,
    useWorker: false,
    behavioursEnabled: true,
    wrap: true
  });

  aceEditor.completers = completers
  aceEditor.setOptions({
    enableBasicAutocompletion: completers,
    enableLiveAutocompletion: completers,
    enableSnippets: true
  })

  let pasteTipAt = 0
  const notifyPasteBlocked = () => {
    const now = Date.now()
    if (now - pasteTipAt < 900) return
    pasteTipAt = now
    ElMessage.warning('请独立完成练习，禁止粘贴代码')
  }
  aceEditor.on('paste', (e) => {
    if (e && typeof e.text === 'string') e.text = ''
    notifyPasteBlocked()
  })
  aceEditor.commands.addCommand({
    name: 'paste',
    bindKey: { win: 'Ctrl-V', mac: 'Command-V' },
    exec: () => notifyPasteBlocked(),
    readOnly: true
  })
  aceEditor.commands.addCommand({
    name: 'paste2',
    bindKey: { win: 'Shift-Insert', mac: 'Shift-Insert' },
    exec: () => notifyPasteBlocked(),
    readOnly: true
  })

  const practiceRaw = sessionStorage.getItem('dailyPractice')
  if (practiceRaw) {
    try {
      const practice = JSON.parse(practiceRaw)
      if (practice?.language === language.value) {
        currentExercise.value = {
          id: practice.id || '',
          taskId: practice.taskId || practice.task_id || '',
          title: practice.title || currentExercise.value.title,
          description: practice.description || currentExercise.value.description,
          topic: practice.topic || practice.topics?.[0] || '',
          expectedOutput: practice.expectedOutput || practice.expected_output || '',
          solutionCode: practice.isCompetition ? '' : (practice.solutionCode || practice.solution_code || ''),
          fromWrongQuestions: !!practice.fromWrongQuestions,
          isTeacherTask: !!practice.isTeacherTask,
          isCompetition: !!practice.isCompetition,
          competitionId: String(practice.competitionId || ''),
          competitionName: String(practice.competitionName || '')
        }
        unlockedSolutionCode.value = ''
        solutionUnlockedState.value = false
        hydrateSolutionUnlockState(practice)
        const starter = practice.starterCode || practice.starter_code || ''
        if (starter) aceEditor.setValue(String(starter), -1)
        if (practice.isCompetition) {
          try {
            const draft = localStorage.getItem(getCompetitionDraftKey())
            if (draft) aceEditor.setValue(String(draft), -1)
          } catch {}
        }
      }
    } catch (e) {
    } finally {
      sessionStorage.removeItem('dailyPractice')
    }
  }
  loadProgress()
  loadRemoteState().finally(() => loadProgress())

// ========== 新增：默认数据兜底 ==========
// 如果没有从 sessionStorage 获取到题目数据，设置默认值
if (!currentExercise.value.id) {
  currentExercise.value = {
    id: 'reverse-string',
    title: '字符串反转',
    description: '输入一个字符串，输出其反转结果。要求处理空字符串与包含空格的情况。',
    expectedOutput: 'olleh',  // 有了这个，按钮就会显示
    solutionCode: `function reverseString(s) {\n    return s.split('').reverse().join('');\n}`,
    starterCode: `function reverseString(s) {\n    // 请在这里编写代码\n    return s;\n}`
  };
  // 设置默认的起始代码
  if (!aceEditor.getValue()) {
    aceEditor.setValue(currentExercise.value.starterCode, -1);
  }
  hydrateSolutionUnlockState(null)
}
// ========== 新增结束 ==========

  if (!aceEditor.getValue()) {
    if (language.value === 'python') aceEditor.setValue('print("Hello, Python AI Learning!")', -1)
    if (language.value === 'javascript') aceEditor.setValue('console.log("Hello, JavaScript AI Learning!")', -1)
    if (language.value === 'java') aceEditor.setValue('public class Main {\n    public static void main(String[] args) {\n        System.out.println(\"Hello, Java AI Learning!\");\n    }\n}', -1)
    if (language.value === 'c') aceEditor.setValue('#include <stdio.h>\n\nint main() {\n    printf(\"Hello, C AI Learning!\\n\");\n    return 0;\n}', -1)
  }

  aceEditor.commands.addCommand({
    name: 'startAutocomplete',
    bindKey: { win: 'Ctrl-Space', mac: 'Command-Space' },
    exec: (editor) => { editor.execCommand('startAutocomplete') }
  })

  aceEditor.commands.on('afterExec', (e) => {
    if (e.command.name === 'insertstring' && typeof e.args === 'string' && e.args.length === 1) {
      const ch = e.args
      if (/[a-zA-Z_.]/.test(ch)) {
        aceEditor.execCommand('startAutocomplete')
      }
    }
  })

  aceEditor.on('change', () => {
    userCode.value = aceEditor.getValue();
  });
  try {
    userCode.value = aceEditor.getValue()
  } catch {}
});

// 监听语言变化自动切换模式
watch(language, (newLang) => {
  if (aceEditor) {
    aceEditor.session.setMode(`ace/mode/${getAceMode(newLang)}`);
  }
});

// 运行代码
const runCode = async () => {
  if (running.value) return null;
  if (aceEditor) userCode.value = aceEditor.getValue();
  if (!userCode.value.trim()) {
    ElMessage.warning('请先输入代码');
    return null;
  }
  hasTried.value = true;
  const data = await runConsole({
    student_id: getUserId(),
    student_name: getUserName(),
    problem_id: currentExercise.value.id || `learn_${language.value}`,
    lang: language.value,
    code: userCode.value,
    exercise: {
      title: currentExercise.value.title,
      description: currentExercise.value.description,
      topic: currentExercise.value.topic || '',
      expectedOutput: currentExercise.value.expectedOutput || '',
      isTeacherTask: !!currentExercise.value.isTeacherTask,
      taskId: currentExercise.value.taskId || '',
    },
  });
  if (!data || data.cancelled) return null;
  if (!data.success) triggerAutoReview(data.error);
  window.dispatchEvent(new Event('code-run-stats-updated'));
  return data;
};

// ====================== 新增：获取错误分析 ======================
const getErrorAnalysis = async () => {
  const studentId = getUserId();
  try {
    const response = await fetch(`/api/analysis/${studentId}`);
    const data = await response.json();

    if (data.total_submissions > 0) {
      let analysisMsg = `\n\n📊 学习分析：\n`;
      analysisMsg += `- 总提交次数：${data.total_submissions}\n`;
      analysisMsg += `- 成功次数：${data.success_count}\n`;
      analysisMsg += `- 成功率：${data.success_rate}%\n`;
      analysisMsg += `- 尝试题目数：${data.problems_attempted}\n`;

      if (data.success_rate < 50 && data.total_submissions >= 3) {
        analysisMsg += `\n⚠️ 建议：成功率较低，请仔细检查代码语法和逻辑。`;
      }

      output.value = (output.value ? `${output.value}\n\n` : '') + analysisMsg;
    }
  } catch (error) {
    console.error('获取分析失败:', error);
  }
};

// ====================== 修改：提交打卡（添加数据库存储） ======================
const submitCode = async () => {
  if (submitting.value || running.value) return
  submitting.value = true
  hasTried.value = true;
  if (!canSubmit.value) {
    output.value = '当前题目未配置预期输出，暂无法自动判题。'
    submitting.value = false
    return
  }

  try {
    if (isCompetitionMode.value) {
      const token = getAuthToken()
      if (!token) {
        ElMessage.warning('请先登录后再提交')
        router.push('/login')
        return
      }
      if (!aceEditor) return
      const cid = String(currentExercise.value?.competitionId || '').trim()
      const taskId = String(currentExercise.value?.id || '').trim()
      if (!cid || !taskId) {
        ElMessage.error('测试信息缺失，无法提交')
        return
      }
      const code = String(aceEditor.getValue() || '')
      const res = await fetch(`/api/competitions/${encodeURIComponent(cid)}/submit`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${token}` },
        body: JSON.stringify({
          task_id: taskId,
          language: String(language.value || ''),
          code,
          input_data: String(stdin.value || '')
        })
      })
      const data = await res.json().catch(() => ({}))
      if (!res.ok || data?.success === false) {
        const msg = String(data?.detail || data?.message || `${res.status} ${res.statusText}`)
        ElMessage.error(msg)
        return
      }
      try {
        localStorage.setItem(getCompetitionSubmittedKey(), '1')
        localStorage.removeItem(getCompetitionDraftKey())
      } catch {}
      ElMessage.success('提交成功')
      const backId = encodeURIComponent(String(currentExercise.value?.competitionId || ''))
      router.push(`/competition/${backId}`)
      return
    }
    // Reuse the completed console run so submitting does not ask for all
    // interactive input a second time. Editing the code starts a fresh run.
    const source = aceEditor ? aceEditor.getValue() : userCode.value;
    const previous = lastRun.value;
    const result = previous?.request.code === source && previous?.request.lang === language.value
      ? previous.result
      : await runCode();
    if (result && result.success) {
      const expected = String(currentExercise.value.expectedOutput || '').trim();
      const actual = String(result.output).trim();
      let pass = expected ? actual.includes(expected) : true
      if (result.submission_id) {
        const token = getAuthToken()
        if (!token) {
          ElMessage.warning('登录已过期，请重新登录后提交')
          return
        }
        const response = await fetch('/api/student/practice-results', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${token}` },
          body: JSON.stringify({ submission_id: result.submission_id })
        })
        const verdict = await response.json().catch(() => ({}))
        if (!response.ok || verdict.success === false) {
          ElMessage.error(verdict.detail || verdict.message || '练习结果保存失败，请重试提交')
          return
        }
        pass = !!verdict.passed
        window.dispatchEvent(new Event('code-run-stats-updated'))
      }
      if (pass) {
        if (expected) {
          output.value += '\n\n🎉 验证通过！你的输出符合预期。';
        } else {
          output.value += '\n\n✅ 提交成功！已记录本次打卡。';
        }
        if (!isCompetitionMode.value) {
          progress.value = 100;
          const doneKey = getDailyPracticeDoneKey(currentExercise.value.id)
          localStorage.setItem(doneKey, '1')
          const dateKey = getTodayKey()
          const exId = String(currentExercise.value.id || 'unknown')
          remotePracticeDone.value = {
            ...(remotePracticeDone.value || {}),
            [dateKey]: {
              ...(remotePracticeDone.value?.[dateKey] || {}),
              [exId]: true
            }
          }
          await saveRemotePracticeDone(dateKey, exId)
        }
      } else {
        output.value += `\n\n⚠️ 验证失败：\n预期包含输出：${expected}\n实际输出：${actual}`;
      }
    }
    if (!isCompetitionMode.value) {
      await getErrorAnalysis();
    }
  } catch (error) {
    ElMessage.error(error.message || '提交失败，请稍后重试')
  } finally {
    submitting.value = false
  }
};

const openSolution = () => {
  unlockAndOpenSolution()
}

const unlockAndOpenSolution = async () => {
  if (!hasTried.value && !output.value) {
    output.value = '建议先尝试运行/提交一次，再查看参考答案。'
  }

  const token = getAuthToken()
  const user = getCurrentUser()
  const uid = String(user?.id || 'guest')
  if (!token || uid === 'guest') {
    ElMessage.warning('请先登录再解锁参考答案')
    router.push('/login')
    return
  }

  if (solutionUnlocked.value) {
    solutionVisible.value = true
    return
  }

  if (!canShowSolutionLink.value) return

  solutionUnlocking.value = true
  try {
    if (currentExercise.value?.isTeacherTask) {
      const taskId = String(currentExercise.value?.taskId || '').trim()
      if (!taskId) throw new Error('缺少任务ID')
      const res = await fetch(`/api/student/tasks/${encodeURIComponent(taskId)}/solution/unlock`, {
        method: 'POST',
        headers: { Authorization: `Bearer ${token}` }
      })
      const data = await res.json().catch(() => ({}))
      if (res.status === 404) {
        throw new Error('解锁接口 Not Found：请重启 3002 的 backend_new.py（确保包含参考答案解锁接口）')
      }
      if (!res.ok || data?.success === false) {
        throw new Error(String(data?.message || data?.detail || `${res.status} ${res.statusText}`))
      }
      const code = String(data?.solutionCode || '').trim()
      if (code) unlockedSolutionCode.value = code
      solutionUnlockedState.value = true
      try {
        localStorage.setItem(getSolutionUnlockKey('task', taskId), '1')
      } catch {}
      const pts = Number(data?.points)
      if (Number.isFinite(pts) && pts >= 0) {
        try {
          localStorage.setItem(`points_${uid}`, String(pts))
        } catch {}
      }
    } else {
      const exId = String(currentExercise.value?.id || '').trim()
      if (!exId) throw new Error('缺少题目ID')
      const res = await fetch('/api/daily-practice/solution/unlock', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${token}` },
        body: JSON.stringify({ exercise_id: exId })
      })
      const data = await res.json().catch(() => ({}))
      if (res.status === 404) {
        throw new Error('解锁接口 Not Found：请重启 3002 的 backend_new.py（确保包含参考答案解锁接口）')
      }
      if (!res.ok || data?.success === false) {
        throw new Error(String(data?.message || data?.detail || `${res.status} ${res.statusText}`))
      }
      const pts = Number(data?.points)
      if (Number.isFinite(pts) && pts >= 0) {
        try {
          localStorage.setItem(`points_${uid}`, String(pts))
        } catch {}
      }
      unlockedSolutionCode.value = String(currentExercise.value?.solutionCode || '')
      solutionUnlockedState.value = true
      try {
        localStorage.setItem(getSolutionUnlockKey('daily', exId), '1')
      } catch {}
    }

    const finalCode = String(unlockedSolutionCode.value || '').trim()
    if (!finalCode) {
      throw new Error('暂无参考答案')
    }
    solutionVisible.value = true
  } catch (e) {
    ElMessage.error(e?.message || '解锁失败')
  } finally {
    solutionUnlocking.value = false
  }
}

const fillSolution = () => {
  const code = String(unlockedSolutionCode.value || '')
  if (!code || !aceEditor) return
  aceEditor.setValue(code, -1)
  userCode.value = aceEditor.getValue()
  solutionVisible.value = false
}

const copySolution = async () => {
  const code = String(unlockedSolutionCode.value || '')
  if (!code) return
  try {
    await navigator.clipboard.writeText(code)
    output.value = (output.value ? `${output.value}\n\n` : '') + '已复制参考答案到剪贴板。'
  } catch {
    output.value = (output.value ? `${output.value}\n\n` : '') + '复制失败：请手动选中参考答案复制。'
  }
}

const askAI = () => {
  if (aceEditor) userCode.value = aceEditor.getValue();
  const code = userCode.value?.trim();
  if (!code) {
    aiInput.value = "我想自己完成这题。请给我解题思路、步骤拆解、关键点和自测方法，并告诉我第一步该写什么。";
  } else {
    aiInput.value = "请帮我检查编辑器里的代码：指出问题点/可能原因，并给我修改方向和验证方法。";
  }
  sendMessage();
};

function returnToPractice(){
  const record=takeMotionReturn('practice')
  const fallback=currentExercise.value.fromWrongQuestions ? '/wrong-questions' : '/daily-checkin'
  return morphNavigation(document.querySelector('.exercise-brief'),()=>router.push(record?.path || fallback),()=>findMotionElement(record?.key),{returning:true,afterNavigate:()=>{if(record)window.scrollTo({top:record.scroll,behavior:'instant'})}})
}
const goToLearningCenter = () => {
  router.push('/learning-center');
};

function finishChatTyping(){
  clearInterval(chatTypeTimer);chatTypeTimer=null;isChatTyping.value=false;chatTypingIndex.value=-1
  for(const item of chatHistory.value){if(item.fullContent)item.content=item.fullContent}
}
function cancelChat(){chatRequestSequence++;chatController?.abort();aiLoading.value=false;if(activeChatReply && !activeChatReply.content){activeChatReply.content='已停止等待，可以重试本次问题。';activeChatReply.error=true}}
async function deliverChat(target,payload){
  if(aiLoading.value)return
  finishChatTyping();target.content='';target.error=false;target.fullContent='';activeChatReply=target;aiLoading.value=true
  chatController=new AbortController();const sequence=++chatRequestSequence
  try{const data=await requestAssistant(payload.message,payload.context,payload.history,{signal:chatController.signal});if(sequence!==chatRequestSequence || !chatActive || !chatHistory.value.includes(target))return;target.provider=data.provider || 'AI';target.fallback=!!data.fallback;startChatTypewriter(chatHistory.value.indexOf(target),data.reply+(data.truncated?'\n\n可继续追问需要展开的部分。':''))}
  catch(error){if(sequence===chatRequestSequence && error.name!=='AbortError' && chatActive){target.content=error.message;target.error=true}}
  finally{if(sequence===chatRequestSequence)aiLoading.value=false}
}
const sendMessage = async () => {
  if(aiLoading.value)return
  if(aceEditor)userCode.value=aceEditor.getValue()
  const message=aiInput.value.trim();if(!message)return
  finishChatTyping()
  const payload={message,context:{mode:'daily_practice',language:language.value,code:buildCodeContext(userCode.value || ''),error:String(lastRun.value?.result?.error || ''),exercise:{title:currentExercise.value.title,description:currentExercise.value.description}},history:conversationHistory(chatHistory.value)}
  chatHistory.value.push({from:'user',content:message},{from:'ai',content:'',retryPayload:payload});aiInput.value=''
  await deliverChat(chatHistory.value.at(-1),payload)
}
function retryChat(target){if(target.retryPayload)deliverChat(target,target.retryPayload)}
function syncChatOwner(){const next=String(getCurrentUser()?.id || 'guest');if(next!==chatOwner){cancelChat();autoReviewController?.abort();clearInterval(chatTypeTimer);chatTypeTimer=null;isChatTyping.value=false;chatTypingIndex.value=-1;chatHistory.value=[];chatOwner=next}}
onMounted(()=>window.addEventListener('user-updated',syncChatOwner))

onBeforeUnmount(() => {
  chatActive=false;cancelChat();autoReviewController?.abort();window.removeEventListener('user-updated',syncChatOwner)
  if (aceEditor) aceEditor.destroy();
  if (chatTypeTimer) {
    clearInterval(chatTypeTimer);
    chatTypeTimer = null;
  }
});
</script>

<style scoped>
.learn-container { max-width: 1400px; margin: 0 auto; padding: 1.5rem; background: #fdfdfd; min-height: 100vh; }
.learn-header { margin-bottom: 2rem; border-bottom: 2px solid #f0f0f0; padding-bottom: 1.5rem; }
.progress { height: 10px; background: #e0e0e0; border-radius: 5px; margin-top: 0.5rem; overflow: hidden; }
.progress-fill { height: 100%; background: linear-gradient(90deg, #42b983, #85e3b5); transition: width 0.5s ease; }
.learn-content { display: grid; grid-template-columns: 1.8fr 1.2fr; gap: 2rem; }
.learn-content.single-col { grid-template-columns: 1fr; }
.editor-section, .ai-section { background: #fff; padding: 1.8rem; border-radius: 12px; box-shadow: 0 4px 20px rgba(0,0,0,0.06); border: 1px solid #f0f0f0; }
.code-editor-wrapper { margin: 1rem 0; border: 1px solid #e0e0e0; border-radius: 8px; overflow: hidden; }
.editor-actions { margin: 1.5rem 0; display: flex; gap: 1rem; }
.editor-actions button { padding: 0.8rem 1.8rem; border: none; border-radius: 6px; cursor: pointer; color: white; font-weight: 600; transition: all 0.2s; }
.editor-actions button:disabled { opacity: 0.6; cursor: not-allowed; transform: none; }
.run-btn { background: #42b983; }
.run-btn:hover { background: #3aa876; transform: translateY(-1px); }
.submit-btn { background: #f59e0b; }
.submit-btn:hover { background: #d97706; transform: translateY(-1px); }
.submit-btn.loading { position: relative; padding-right: 2.8rem; }
.submit-btn.loading::after { content: ''; position: absolute; right: 14px; top: 50%; width: 14px; height: 14px; margin-top: -7px; border-radius: 50%; border: 2px solid rgba(255,255,255,0.6); border-top-color: #fff; animation: btn-spin 0.8s linear infinite; }
.ai-btn { background: #2563eb; }
.ai-btn:hover { background: #1d4ed8; transform: translateY(-1px); }
.helper-links { margin: -6px 0 12px; display: flex; justify-content: flex-end; }
.solution-link { border: none; background: transparent; color: #2563eb; cursor: pointer; padding: 4px 0; font-weight: 600; }
.solution-link:hover { text-decoration: underline; }
.solution-mask { position: fixed; inset: 0; background: rgba(0,0,0,0.45); display: flex; align-items: center; justify-content: center; z-index: 9999; padding: 18px; }
.solution-dialog { width: min(920px, 96vw); max-height: 84vh; background: #fff; border-radius: 12px; box-shadow: 0 12px 38px rgba(0,0,0,0.22); overflow: hidden; display: flex; flex-direction: column; }
.solution-header { display: flex; align-items: center; justify-content: space-between; padding: 12px 14px; border-bottom: 1px solid #f0f0f0; }
.solution-title { font-weight: 800; color: #111; }
.solution-close { border: none; background: transparent; cursor: pointer; font-size: 22px; line-height: 1; color: #666; padding: 2px 8px; border-radius: 6px; }
.solution-close:hover { background: #f3f4f6; color: #111; }
.solution-code { margin: 0; padding: 12px 14px; background: #111827; color: #e5e7eb; overflow: auto; font-family: 'Consolas', monospace; font-size: 14px; line-height: 1.55; flex: 1; }
.solution-actions { display: flex; justify-content: flex-end; gap: 10px; padding: 12px 14px; border-top: 1px solid #f0f0f0; background: #fff; }
.solution-action { border: 1px solid #ddd; background: #fff; color: #111; padding: 10px 14px; border-radius: 8px; cursor: pointer; font-weight: 700; }
.solution-action:hover { background: #f9fafb; }
.solution-action.primary { border-color: #2563eb; background: #2563eb; color: #fff; }
.solution-action.primary:hover { background: #1d4ed8; }
.chat-history { height: 380px; overflow-y: auto; border: 1px solid #f0f0f0; padding: 1.2rem; background: #fafafa; border-radius: 8px; margin-bottom: 1rem; }
.chat-message { margin-bottom: 1rem; line-height: 1.5; padding: 0.8rem; border-radius: 8px; }
.ai-message { background: #fff; border: 1px solid #eee; color: #444; width: 85%; }
.user-message { background: #e3f2fd; color: #1976d2; text-align: right; margin-left: auto; width: 85%; }
.message-content { white-space: pre-wrap; word-break: break-word; }
.user-text { white-space: pre-wrap; }
:deep(.ai-markdown) { white-space: normal; }
:deep(.ai-markdown p) { margin: 0 0 0.6rem; }
:deep(.ai-markdown p:last-child) { margin-bottom: 0; }
:deep(.ai-markdown strong) { font-weight: 800; color: #111827; }
:deep(.ai-markdown ul), :deep(.ai-markdown ol) { margin: 0.3rem 0 0.6rem; padding-left: 1.2rem; }
:deep(.ai-markdown li) { margin: 0.2rem 0; }
:deep(.ai-markdown h1), :deep(.ai-markdown h2), :deep(.ai-markdown h3) { margin: 0.3rem 0 0.6rem; font-size: 1rem; font-weight: 800; color: #111827; }
:deep(.ai-markdown code) { background: #f3f4f6; padding: 0.1rem 0.35rem; border-radius: 6px; font-family: 'Consolas', monospace; font-size: 0.92em; }
:deep(.ai-markdown pre) { background: #111827; color: #e5e7eb; padding: 10px 12px; border-radius: 10px; overflow: auto; }
:deep(.ai-markdown pre code) { background: transparent; padding: 0; }
:deep(.ai-markdown a) { color: #2563eb; text-decoration: underline; }
.typing-text { display: inline-block; margin-right: 8px; color: #374151; font-weight: 600; }
.typing-dots { display: inline-flex; gap: 4px; vertical-align: middle; }
.typing-dots span { width: 6px; height: 6px; border-radius: 50%; background: #9ca3af; display: inline-block; animation: typing-bounce 1s infinite ease-in-out; }
.typing-dots span:nth-child(2) { animation-delay: 0.15s; }
.typing-dots span:nth-child(3) { animation-delay: 0.3s; }
.input-area { display: flex; gap: 0.5rem; }
.input-area { display: flex; gap: 0.5rem; }
.input-area textarea { flex-grow: 1; padding: 0.8rem; border: 1px solid #ddd; border-radius: 6px; font-size: 0.95rem; resize: vertical; min-height: 92px; font-family: inherit; line-height: 1.4; }
@keyframes typing-bounce {
  0%, 80%, 100% { transform: translateY(0); opacity: 0.6; }
  40% { transform: translateY(-4px); opacity: 1; }
}

@keyframes btn-spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}
.input-area button { padding: 0.8rem 1.5rem; border: none; background: #2563eb; color: white; border-radius: 6px; cursor: pointer; font-weight: 600; }
.learn-container{background:#f5f3fa;padding:24px;max-width:1480px}.learn-header{position:relative;overflow:hidden;padding:26px 30px;border:1px solid #d6c6ea;border-radius:20px;background:linear-gradient(125deg,#697bdd,#7955a5);color:#fff;margin-bottom:24px;box-shadow:0 10px 30px #8d6caf16}.learn-header h1{font-size:27px;line-height:1.5;margin:12px 0 18px}.practice-topline{display:flex;justify-content:space-between;align-items:center;gap:18px}.practice-eyebrow{font:9px Consolas,monospace;letter-spacing:2px;color:#e7d8f8c9}.practice-back{background:#ffffff12;border:1px solid #ecddff55;border-radius:8px;padding:8px 12px;font-size:11px;color:#fff;cursor:pointer}.progress-bar{display:block;width:min(100%,530px);text-align:left;background:none;border:0;color:#ede4fa;padding:0;font:inherit;font-size:12px;cursor:pointer}.progress{display:block;height:5px;background:#ffffff25;margin-top:10px}.progress-fill{display:block;background:linear-gradient(90deg,#ddbbff,#bce6ee)}.practice-flow{display:flex;align-items:center;gap:12px;flex-wrap:wrap;margin-top:23px;font-size:10px;color:#d6c4eda3}.practice-flow>span{padding:6px 9px;border-radius:7px;border:1px solid #e3ccfa24;background:#ffffff05;transition:background 200ms,color 200ms}.practice-flow>span:first-child,.practice-flow>span.active{color:#f3eaff;background:#ffffff12;border-color:#e3ccfa55}.practice-flow i{font-style:normal;color:#decbf688;animation:practice-signal 3s ease-in-out infinite}.learn-content{gap:22px;grid-template-columns:minmax(0,1.55fr) minmax(300px,1fr);align-items:start}.editor-section,.ai-section{min-width:0;border:1px solid #e4dced;border-radius:17px;padding:24px;box-shadow:0 7px 22px #9175a90b}.editor-section h2,.ai-section h2{font-size:18px;line-height:1.7;color:#685175;margin:0 0 13px}.exercise-desc{color:#8d809a;font-size:13px;line-height:1.9;white-space:pre-wrap}.practice-editor-toolbar{display:flex;justify-content:space-between;align-items:center;gap:12px;margin-top:20px;padding:10px 12px;background:#f5f0fa;border:1px solid #e6dbef;border-radius:10px 10px 0 0}.practice-editor-toolbar>span{display:flex;align-items:center;gap:8px;font:10px Consolas,monospace;color:#8b6ba8}.practice-editor-toolbar i{width:5px;height:5px;border-radius:50%;background:#a78ac5}.practice-editor-toolbar small{font:inherit;font-size:10px;color:#b1a0bd}.practice-editor-toolbar>div{display:flex;align-items:center;gap:8px;color:#a28cb3;font:10px Consolas,monospace}.practice-editor-toolbar button{background:#fff;border:1px solid #dfd1e9;border-radius:6px;padding:5px 8px;color:#9471ae;font-size:10px;cursor:pointer}.practice-editor-toolbar button:disabled{opacity:.4;cursor:default}.practice-editor-toolbar button[aria-pressed=true]{background:#e7daf4}.code-editor-wrapper{margin:0 0 17px;border-radius:0 0 10px 10px}.editor-actions{flex-wrap:wrap;gap:10px;margin:18px 0}.editor-actions button{border-radius:9px;padding:11px 17px;font-size:12px}.submit-btn{background:#9c7cba}.submit-btn:hover{background:#8c69ac}.ai-btn{background:#7c86c4}.chat-history{border:1px solid #e8dff0;background:#faf8fd;border-radius:12px}.chat-message{font-size:13px;line-height:1.8}.ai-message{border-color:#e7dcf0;border-radius:12px 12px 12px 3px}.user-message{background:#ede5f5;color:#84629b;border-radius:12px 12px 3px 12px}.input-area textarea{min-width:0;border-color:#dfd1eb;border-radius:10px}.input-area button{background:#9a7ab5;border-radius:9px}.practice-focused .editor-section{max-width:1100px;width:100%;margin:auto}.practice-focused .learn-content{grid-template-columns:minmax(0,1fr)}@keyframes practice-signal{50%{translate:3px 0;opacity:.5}}@media(max-width:1000px){.learn-content{grid-template-columns:minmax(0,1fr)}.ai-section{width:100%}.chat-history{height:310px}}@media(max-width:640px){.learn-container{padding:16px 12px}.learn-header{padding:20px 18px;border-radius:15px}.learn-header h1{font-size:22px}.practice-topline{flex-wrap:wrap;gap:10px}.practice-flow{gap:6px;font-size:9px}.practice-flow>span{padding:5px}.editor-section,.ai-section{padding:17px}.practice-editor-toolbar{flex-wrap:wrap}.practice-editor-toolbar small{display:none}.input-area{flex-direction:column}.input-area button{align-self:flex-end}.editor-actions button{padding:10px 13px}}
</style>

<style>
.ace_autocomplete {
  width: 300px !important;
  z-index: 999999 !important;
  background: #25282c !important;
  color: #fff !important;
  border: 1px solid #444 !important;
  box-shadow: 0 4px 12px rgba(0,0,0,0.5) !important;
}
.ace_autocomplete .ace_content {
  background: #25282c !important;
}
.ace_autocomplete .ace_line-hover {
  background: #45494e !important;
}
.ace_autocomplete .ace_completion-highlight {
  color: #42b983 !important;
}
</style>

<style scoped>
.assistant-provider{display:block;color:#a18caf;font-size:10px;margin-top:12px}.assistant-status{display:flex;justify-content:space-between;color:#a18caf;font-size:11px;margin-bottom:10px}.assistant-status button,.chat-retry{border:0;background:none;font:inherit;color:#9270b1;cursor:pointer}.chat-retry{font-size:11px;padding:8px 0}
</style>
