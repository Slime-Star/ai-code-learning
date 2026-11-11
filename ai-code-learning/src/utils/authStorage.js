const USER_KEY = 'currentUser'
const TOKEN_KEY = 'authToken'

const canUseSession = () => {
  try {
    return typeof window !== 'undefined' && !!window.sessionStorage
  } catch {
    return false
  }
}

const canUseLocal = () => {
  try {
    return typeof window !== 'undefined' && !!window.localStorage
  } catch {
    return false
  }
}

export const getCurrentUser = () => {
  const raw = canUseSession() ? sessionStorage.getItem(USER_KEY) : null
  if (!raw) return null
  try {
    return JSON.parse(raw)
  } catch {
    return null
  }
}

export const setCurrentUser = (user) => {
  if (canUseSession()) {
    sessionStorage.setItem(USER_KEY, JSON.stringify(user || {}))
  }
}

export const removeCurrentUser = () => {
  if (canUseSession()) {
    sessionStorage.removeItem(USER_KEY)
  }
  if (canUseLocal()) {
    localStorage.removeItem(USER_KEY)
  }
}

export const getAuthToken = () => {
  if (canUseSession()) {
    const token = sessionStorage.getItem(TOKEN_KEY)
    if (token) return token
  }
  if (canUseLocal()) {
    return localStorage.getItem(TOKEN_KEY) || ''
  }
  return ''
}

export const setAuthToken = (token) => {
  if (canUseSession()) {
    sessionStorage.setItem(TOKEN_KEY, String(token || ''))
  } else if (canUseLocal()) {
    localStorage.setItem(TOKEN_KEY, String(token || ''))
  }
}

export const removeAuthToken = () => {
  if (canUseSession()) sessionStorage.removeItem(TOKEN_KEY)
  if (canUseLocal()) localStorage.removeItem(TOKEN_KEY)
}

export const migrateLegacyAuthToSession = () => {
  if (!canUseSession() || !canUseLocal()) return
  if (!sessionStorage.getItem(USER_KEY)) {
    const legacyUser = localStorage.getItem(USER_KEY)
    if (legacyUser) sessionStorage.setItem(USER_KEY, legacyUser)
  }
  if (!sessionStorage.getItem(TOKEN_KEY)) {
    const legacyToken = localStorage.getItem(TOKEN_KEY)
    if (legacyToken) sessionStorage.setItem(TOKEN_KEY, legacyToken)
  }
}
