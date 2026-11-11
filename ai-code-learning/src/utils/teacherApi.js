import { getAuthToken, getCurrentUser } from '@/utils/authStorage'

export async function teacherGet(path, { signal } = {}) {
  const token = getAuthToken()
  if (!token) throw new Error('请先登录教师账号')
  const response = await fetch(path, { signal, headers: { Authorization: `Bearer ${token}` } })
  const data = await response.json().catch(() => ({}))
  if (!response.ok || data?.success === false) throw new Error(data?.detail || data?.message || '数据加载失败，请重试')
  return data
}
export const teacherStorageKey = name => `teacher:${getCurrentUser()?.id || 'guest'}:${name}`
export function readTeacherState(name, fallback = null) {
  try { return JSON.parse(sessionStorage.getItem(teacherStorageKey(name)) || 'null') ?? fallback } catch { return fallback }
}
export function writeTeacherState(name, value) {
  try { sessionStorage.setItem(teacherStorageKey(name), JSON.stringify(value)) } catch {}
}
export function invalidateTeacherState(prefix) {
  try {
    const keyPrefix=teacherStorageKey(prefix)
    Object.keys(sessionStorage).filter(key=>key.startsWith(keyPrefix)).forEach(key=>sessionStorage.removeItem(key))
  } catch {}
}
export const isUngraded = row => !!row.submittedAt && (row.score === null || row.score === undefined)
