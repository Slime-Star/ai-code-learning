<template>
  <div class="code-judge-container">
    <div class="header">
      <h2>代码在线判题</h2>
    </div>

    <div class="tool-bar">
      <select v-model="lang" @change="changeLangMode">
        <option value="python">Python</option>
        <option value="c">C 语言</option>
        <option value="java">Java</option>
        <option value="javascript">JavaScript</option>
      </select>

      <button @click="runCode" :disabled="loading">
        {{ loading ? "判题中..." : "运行判题" }}
      </button>
    </div>

    <!-- 代码编辑器 -->
    <div id="editor" class="editor"></div>

    <!-- 判题结果 -->
    <div class="result" v-if="result">
      <div class="status">状态：{{ result.status }}</div>
      <div>运行时间：{{ result.time }}s</div>
      <div>内存占用：{{ result.memory }}KB</div>
      <div class="output">
        输出：<pre>{{ result.stdout || result.stderr || "无输出" }}</pre>
      </div>
    </div>
    <TopicArt scene="chip" />
  </div>
</template>

<script setup>
import TopicArt from '@/components/TopicArt.vue'
import { ref, onMounted } from 'vue'
import ace from 'ace-builds'

// 引入语言模式
import 'ace-builds/src-noconflict/mode-python'
import 'ace-builds/src-noconflict/mode-c_cpp'
import 'ace-builds/src-noconflict/mode-java'
import 'ace-builds/src-noconflict/mode-javascript'
import 'ace-builds/src-noconflict/theme-monokai'

const lang = ref('python')
const loading = ref(false)
const result = ref(null)
let editor = null

onMounted(() => {
  editor = ace.edit('editor')
  editor.setTheme('ace/theme/monokai')
  editor.session.setMode('ace/mode/python')
  editor.setValue('print("Hello World")')
})

// 切换语言
const changeLangMode = () => {
  const modeMap = {
    python: 'python',
    c: 'c_cpp',
    java: 'java',
    javascript: 'javascript'
  }
  editor.session.setMode(`ace/mode/${modeMap[lang.value]}`)
}

// 运行判题
const runCode = async () => {
  loading.value = true
  result.value = null

  try {
    const res = await fetch('/api/judge', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        code: editor.getValue(),
        lang: lang.value
      })
    })
    result.value = await res.json()
  } catch (err) {
    result.value = { status: '请求失败', stderr: err.message }
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.code-judge-container {
  max-width: 1200px;
  margin: 0 auto;
  padding: 20px;
}

.tool-bar {
  display: flex;
  gap: 12px;
  margin-bottom: 12px;
}

select, button {
  padding: 8px 14px;
  border-radius: 4px;
  border: 1px solid #ddd;
}

button {
  background: #42b983;
  color: white;
  border: none;
  cursor: pointer;
}

button:disabled {
  background: #999;
}

.editor {
  width: 100%;
  height: 420px;
  border: 1px solid #eee;
  border-radius: 6px;
}

.result {
  margin-top: 16px;
  padding: 16px;
  background: #f7f7f7;
  border-radius: 8px;
  line-height: 1.6;
}

pre {
  margin: 0;
  white-space: pre-wrap;
}
</style>
