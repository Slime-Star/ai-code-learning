import { onBeforeUnmount, ref } from 'vue'

export function useCodeConsole() {
  const transcript = ref('')
  const input = ref('')
  const running = ref(false)
  const acceptingInput = ref(false)
  const status = ref('就绪')
  const lastRun = ref(null)
  let socket = null
  let finishRun = null

  const append = (text) => { transcript.value += String(text || '') }
  const note = (text) => {
    if (transcript.value && !transcript.value.endsWith('\n')) append('\n')
    append(`[${text}]\n`)
  }

  const run = (request) => {
    if (running.value) return Promise.resolve(null)
    transcript.value = ''
    input.value = ''
    lastRun.value = null
    running.value = true
    acceptingInput.value = false
    status.value = '连接中'

    return new Promise((resolve) => {
      let completed = false
      let connectTimer
      const finish = (result) => {
        if (completed) return
        completed = true
        clearTimeout(connectTimer)
        running.value = false
        acceptingInput.value = false
        status.value = result.cancelled ? '已停止' : result.success ? '已结束' : '运行失败'
        if (result.success) note(`程序已结束，退出代码 ${result.exit_code ?? 0}`)
        else note(result.error || '运行失败')
        if (!result.cancelled) lastRun.value = { request: { ...request }, result }
        finishRun = null
        const active = socket
        socket = null
        if (active && active.readyState < WebSocket.CLOSING) active.close()
        resolve(result)
      }
      finishRun = finish
      try {
        const url = new URL('/api/console', window.location.href)
        url.protocol = url.protocol === 'https:' ? 'wss:' : 'ws:'
        const active = new WebSocket(url)
        socket = active
        connectTimer = setTimeout(() => finish({ success: false, error: '连接超时，请确认后端已启动并支持控制台连接' }), 10000)
        active.onopen = () => {
          if (completed) return
          clearTimeout(connectTimer)
          status.value = '启动中'
          active.send(JSON.stringify({ ...request, type: 'start' }))
        }
        active.onmessage = (event) => {
          if (completed) return
          let message
          try { message = JSON.parse(event.data) } catch { return }
          if (message.type === 'started') {
            acceptingInput.value = true
            status.value = '运行中 · 可输入'
          } else if (message.type === 'status') {
            status.value = message.data
          } else if (message.type === 'output') {
            append(message.data)
          } else if (message.type === 'input') {
            input.value += message.data
            append(message.data)
          } else if (message.type === 'stdin_closed') {
            acceptingInput.value = false
            status.value = '运行中 · 输入已结束'
          } else if (message.type === 'exit') {
            finish(message)
          }
        }
        active.onerror = () => finish({ success: false, error: '控制台连接失败，请启动或重启后端服务，并确认代理支持 WebSocket' })
        active.onclose = () => finish({ success: false, error: '控制台连接已断开，请重新运行程序' })
      } catch (error) {
        finish({ success: false, error: `控制台连接失败：${error.message}` })
      }
    })
  }

  const sendInput = (text) => {
    if (!acceptingInput.value || socket?.readyState !== WebSocket.OPEN) return false
    const normalized = String(text).replace(/\r\n?/g, '\n')
    socket.send(JSON.stringify({ type: 'input', data: `${normalized}\n` }))
    return true
  }

  const endInput = () => {
    if (!acceptingInput.value || socket?.readyState !== WebSocket.OPEN) return
    socket.send(JSON.stringify({ type: 'eof' }))
    acceptingInput.value = false
    status.value = '运行中 · 输入已结束'
  }

  const stop = () => {
    if (!running.value) return
    if (socket?.readyState === WebSocket.OPEN) {
      socket.send(JSON.stringify({ type: 'stop' }))
    }
    finishRun?.({ success: false, cancelled: true, error: '程序已停止' })
  }

  const clear = () => { transcript.value = '' }
  onBeforeUnmount(stop)
  return { transcript, input, running, acceptingInput, status, lastRun, run, sendInput, endInput, stop, clear }
}
