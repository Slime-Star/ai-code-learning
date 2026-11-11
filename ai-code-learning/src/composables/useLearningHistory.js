import { ref, onMounted, onBeforeUnmount } from 'vue'
import { getCurrentUser } from '@/utils/authStorage'

const storageKey = () => `learning-history:v1:${getCurrentUser()?.id ?? 'guest'}`
const validNumber = value => Number.isFinite(value) && value >= 0

export function useLearningHistory() {
  const history = ref([])
  function refresh() {
    try {
      const data = JSON.parse(localStorage.getItem(storageKey()) || '[]')
      history.value = Array.isArray(data) ? data.filter(item =>
        item && Number.isInteger(item.id) && validNumber(item.updatedAt)
      ).slice(0, 50) : []
    } catch { history.value = [] }
  }
  function save(id, progress = {}) {
    const previous = history.value.find(item => item.id === id) || {}
    const record = { ...previous, id, updatedAt: Date.now() }
    if (validNumber(progress.position) && validNumber(progress.duration)) {
      Object.assign(record, progress)
    }
    history.value = [record, ...history.value.filter(item => item.id !== id)].slice(0, 50)
    try { localStorage.setItem(storageKey(), JSON.stringify(history.value)) } catch {}
  }
  refresh()
  onMounted(() => {
    window.addEventListener('user-updated', refresh)
    window.addEventListener('storage', refresh)
  })
  onBeforeUnmount(() => {
    window.removeEventListener('user-updated', refresh)
    window.removeEventListener('storage', refresh)
  })
  return { history, save }
}
