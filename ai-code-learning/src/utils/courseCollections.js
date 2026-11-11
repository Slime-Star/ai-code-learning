import { getAuthToken, getCurrentUser, setCurrentUser } from './authStorage'

let revision = 0
let pendingMutation = Promise.resolve()

function applyIds(ids, owner, announce = false) {
  const user = getCurrentUser()
  if (user?.id !== owner) return false
  setCurrentUser({ ...user, collectedCourses: ids })
  try { localStorage.setItem(`user_${owner}_collections`, JSON.stringify(ids)) } catch {}
  if (announce) window.dispatchEvent(new CustomEvent('course-collections-updated', { detail: { userId: owner, ids } }))
  return true
}

async function request(path, token, options = {}) {
  if (!token) throw new Error('登录已失效，请重新登录后收藏课程')
  const response = await fetch(`/api/users/me/collections${path}`, {
    ...options,
    headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${token}` }
  })
  const data = await response.json().catch(() => ({}))
  if (!response.ok || !data.success) throw new Error(typeof data.detail === 'string' ? data.detail : '收藏同步失败，请稍后重试')
  return data
}

export async function loadCourseCollections() {
  const owner = getCurrentUser()?.id, token = getAuthToken(), version = revision
  const data = await request('', token, { cache: 'no-store' })
  if (getCurrentUser()?.id !== owner || getAuthToken() !== token || version !== revision) return null
  applyIds(data.ids, owner)
  return data
}

export function setCourseCollected(courseId, collected) {
  const owner = getCurrentUser()?.id, token = getAuthToken()
  revision++
  const operation = pendingMutation.catch(() => {}).then(async () => {
    if (getCurrentUser()?.id !== owner || getAuthToken() !== token) throw new Error('账号已切换，请重新操作')
    const data = await request(`/${encodeURIComponent(courseId)}`, token, { method: 'PUT', body: JSON.stringify({ collected }) })
    revision++
    if (getCurrentUser()?.id !== owner || getAuthToken() !== token) throw new Error('账号已切换，请重新操作')
    applyIds(data.ids, owner, true)
    return data
  })
  pendingMutation = operation
  return operation
}
