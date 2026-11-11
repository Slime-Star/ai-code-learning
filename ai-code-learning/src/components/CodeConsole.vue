<template>
  <section class="code-console" aria-label="程序交互控制台">
    <header class="console-toolbar">
      <span class="console-title">控制台 <span class="console-status" role="status">{{ status }}</span></span>
      <div class="console-actions">
        <button v-if="acceptingInput" type="button" @click="finishInput">结束输入</button>
        <button v-if="running" type="button" class="stop-action" @click="$emit('stop')">停止</button>
        <button type="button" @click="$emit('clear')">清空</button>
      </div>
    </header>
    <div ref="viewport" class="console-viewport" @click="focusInput">
      <div v-if="!text && !running" class="console-placeholder">点击“运行代码”开始，程序输出和键盘输入将在这里显示。</div>
      <div class="console-content"><span>{{ text }}</span><textarea
        v-if="acceptingInput"
        ref="inputElement"
        v-model="draft"
        class="console-input"
        aria-label="控制台输入"
        autocomplete="off"
        autocapitalize="off"
        :spellcheck="false"
        :rows="Math.min(6, draft.split('\n').length)"
        :style="{ width: `${inputWidth}ch` }"
        @keydown="handleKeydown"
        @compositionstart="composing = true"
        @compositionend="composing = false"
      ></textarea></div>
    </div>
    <footer class="console-hint">{{ acceptingInput ? '直接输入后按 Enter 发送 · 支持粘贴多行 · Ctrl+D 结束输入 · Ctrl+C 停止' : running ? '程序正在运行，输出会实时显示。' : '运行后可在输出提示后直接输入。' }}</footer>
  </section>
</template>

<script setup>
import { computed, nextTick, ref, watch } from 'vue'

const props = defineProps({
  text: { type: String, default: '' },
  running: Boolean,
  acceptingInput: Boolean,
  status: { type: String, default: '就绪' },
})
const emit = defineEmits(['input', 'eof', 'stop', 'clear'])
const draft = ref('')
const composing = ref(false)
const viewport = ref(null)
const inputElement = ref(null)
const inputWidth = computed(() => draft.value.split('\n').reduce((width, line) => Math.max(width, Array.from(line).reduce((size, ch) => size + (ch.charCodeAt(0) > 255 ? 2 : 1), 1)), 12))

const focusInput = () => {
  if (!window.getSelection()?.isCollapsed) return
  inputElement.value?.focus({ preventScroll: true })
}
const submit = () => {
  if (!props.acceptingInput || composing.value) return
  emit('input', draft.value)
  draft.value = ''
}
const finishInput = () => {
  if (composing.value) return
  if (draft.value) submit()
  emit('eof')
}
const handleKeydown = (event) => {
  // Enter used to confirm a Chinese IME candidate must not submit the line.
  if (event.isComposing || composing.value || event.keyCode === 229) return
  if (event.ctrlKey && event.key.toLowerCase() === 'c' && window.getSelection()?.isCollapsed && event.target.selectionStart === event.target.selectionEnd) {
    event.preventDefault()
    emit('stop')
  } else if (event.ctrlKey && event.key.toLowerCase() === 'd') {
    event.preventDefault()
    finishInput()
  } else if (event.key === 'Enter' && !event.shiftKey) {
    event.preventDefault()
    submit()
  }
}

watch(() => props.running, (active) => { if (active) draft.value = '' })
watch(() => props.acceptingInput, async (active) => {
  if (active) {
    await nextTick()
    focusInput()
  }
})
watch([() => props.text, draft], async () => {
  await nextTick()
  if (inputElement.value) {
    inputElement.value.style.height = 'auto'
    inputElement.value.style.height = `${Math.min(160, inputElement.value.scrollHeight)}px`
  }
  if (viewport.value) viewport.value.scrollTop = viewport.value.scrollHeight
})
</script>

<style scoped>
.code-console { display: flex; flex-direction: column; min-height: 180px; min-width: 0; overflow: hidden; border: 1px solid #343c4a; border-radius: 8px; background: #171b22; color: #e5e7eb; }
.console-toolbar { display: flex; align-items: center; justify-content: space-between; gap: 8px; flex-wrap: wrap; padding: 9px 12px; border-bottom: 1px solid #343c4a; background: #222833; }
.console-title { font-size: 14px; font-weight: 600; }
.console-status { margin-left: 8px; font-size: 12px; font-weight: 400; color: #9caec4; }
.console-actions { display: flex; gap: 8px; }
.console-actions button { padding: 3px 7px; border: 1px solid #485263; border-radius: 4px; background: transparent; color: #d1d5db; font: inherit; font-size: 12px; cursor: pointer; }
.console-actions button:hover { background: #343c4a; }
.console-actions .stop-action { color: #fca5a5; }
.console-viewport { flex: 1; min-height: 86px; max-height: 330px; overflow: auto; padding: 12px; cursor: text; }
.console-content, .console-input { font-family: Consolas, Monaco, 'Courier New', monospace; font-size: 14px; line-height: 1.65; letter-spacing: normal; }
.console-content { white-space: pre-wrap; overflow-wrap: anywhere; }
.console-input { display: inline-block; vertical-align: top; box-sizing: content-box; min-width: 12ch; max-width: 100%; margin: 0; padding: 0; border: 0; border-radius: 0; outline: 0; resize: none; overflow: auto; background: transparent; color: #86efac; caret-color: #86efac; white-space: pre-wrap; }
.console-input:focus-visible { outline: 0; box-shadow: none; }
.console-placeholder { color: #93a0b2; font-size: 13px; line-height: 1.7; }
.console-hint { padding: 7px 12px; border-top: 1px solid #2b323e; color: #93a0b2; font-size: 11px; line-height: 1.6; }
</style>
