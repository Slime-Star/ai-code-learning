<template>
  <div class="code-editor" ref="editorContainer"></div>
</template>

<script setup>
import { ref, onMounted, watch, onUnmounted } from 'vue'
import loader from '@monaco-editor/loader'
import { useAiStore } from '@/store/aiStore'

const aiStore = useAiStore()
const editorContainer = ref(null)
let editor = null

// 配置Monaco编辑器
loader.config({ paths: { vs: 'https://cdn.jsdelivr.net/npm/monaco-editor@0.44.0/min/vs' } })

onMounted(async () => {
  // 加载编辑器
  const monaco = await loader.init()
  // 创建编辑器
  editor = monaco.editor.create(editorContainer.value, {
    value: aiStore.currentCode,
    language: aiStore.currentLang,
    theme: 'vs-dark', // 暗色主题
    minimap: { enabled: false },
    fontSize: 14,
    automaticLayout: true, // 自动适应布局
    scrollBeyondLastLine: false
  })

  // 监听代码变化，同步到状态库
  editor.onDidChangeModelContent(() => {
    aiStore.updateCurrentCode(editor.getValue())
  })
})

// 监听语言变化，更新编辑器语言
watch(() => aiStore.currentLang, (newLang) => {
  if (editor) {
    const monaco = editor.getModel().getModeId()
    editor.getModel().setLanguage(newLang)
  }
})

// 监听代码变化，更新编辑器内容
watch(() => aiStore.currentCode, (newCode) => {
  if (editor && editor.getValue() !== newCode) {
    editor.setValue(newCode)
  }
})

onUnmounted(() => {
  if (editor) {
    editor.dispose() // 销毁编辑器，释放资源
  }
})
</script>

<style scoped>
.code-editor {
  width: 100%;
  height: 400px;
  border-radius: 8px;
  overflow: hidden;
}
</style>