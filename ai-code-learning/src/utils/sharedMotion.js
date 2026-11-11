import { nextTick } from 'vue'

let active = null
let routeMotion = 0
const returns = new Map()
const listRestores = new Map(), pageSeeds = new Map(), warmedRoutes = new WeakMap()
const settledCallbacks = new Set()
const frame = () => new Promise(resolve => requestAnimationFrame(resolve))
const elementOf = value => typeof value === 'function' ? value() : value?.$el || value
const valid = rect => rect?.width > 0 && rect?.height > 0

export const isSharedNavigation = () => routeMotion > 0
export function afterSharedNavigation(callback) {
  let cancelled = false
  const run = () => { if (!cancelled) Promise.resolve().then(() => { if (!cancelled) return callback() }).catch(() => {}) }
  if (isSharedNavigation()) settledCallbacks.add(run)
  else run()
  return () => { cancelled = true; settledCallbacks.delete(run) }
}
export const findMotionElement = key => Array.from(document.querySelectorAll('[data-motion-key]')).find(element => element.dataset.motionKey === key && !element.closest('.page-leave-active'))
export function takeMotionReturn(key) {
  const record = returns.get(key); returns.delete(key)
  if (record?.state) listRestores.set(record.path.split('?')[0], record.state)
  return record
}
export function takeMotionList(path, owner = 'guest') {
  const state = listRestores.get(path); listRestores.delete(path)
  return state && String(state.owner) === String(owner) ? state : null
}
export function rememberMotionReturn(key, path, element, state) {
  returns.set(key, { path, key: element?.dataset.motionKey, scroll: window.scrollY, state })
}
export function seedMotionPage(path, owner, data) { pageSeeds.clear(); pageSeeds.set(path, { owner, data, time: Date.now() }) }
export function takeMotionPage(path, owner) {
  const seed = pageSeeds.get(path); pageSeeds.delete(path)
  return seed && String(seed.owner) === String(owner) && Date.now() - seed.time < 10000 ? seed.data : null
}
export function warmMotionRoute(router, path) {
  for (const record of router.resolve(path).matched) {
    const loader = record.components?.default
    if (typeof loader !== 'function' || warmedRoutes.has(loader)) continue
    const warm = new Promise(resolve => setTimeout(resolve, 0)).then(() => loader()).catch(() => {})
    warmedRoutes.set(loader, warm)
  }
}

export function captureMotion(source, { image, round = false, content, preserveContent = false } = {}) {
  source = elementOf(source)
  if (!source?.isConnected || document.hidden || typeof source.animate !== 'function') return null
  const start = source.getBoundingClientRect()
  if (!valid(start) || start.bottom < 0 || start.top > window.innerHeight) return null
  active?.cancel()
  const style = getComputedStyle(source), shell = document.createElement('div')
  shell.className = 'shared-motion-snapshot'
  shell.setAttribute('aria-hidden', 'true'); shell.inert = true
  Object.assign(shell.style, {
    position: 'fixed', left: `${start.left}px`, top: `${start.top}px`, width: `${start.width}px`, height: `${start.height}px`,
    margin: '0', zIndex: '4000', pointerEvents: 'none', overflow: 'hidden', transformOrigin: '0 0',
    borderRadius: round ? '50%' : style.borderRadius || '16px', background: style.backgroundColor,
    color: style.color, font: style.font, boxShadow: round ? 'none' : '0 18px 50px #44335d25', contain: 'layout paint'
  })
  let visual
  if (image) {
    visual = document.createElement('img'); visual.src = image; visual.alt = ''
    Object.assign(visual.style, { width: '100%', height: '100%', objectFit: 'cover', display: 'block' })
  } else {
    visual = (content || source).cloneNode(true)
    visual.querySelectorAll(`input,textarea,select,script,iframe,video,canvas${preserveContent ? '' : ',button,[role="button"]'}`).forEach(node => node.remove())
    for (const node of [visual, ...visual.querySelectorAll('*')]) {
      node.removeAttribute('id'); node.removeAttribute('autofocus'); node.removeAttribute('tabindex')
      node.style.animation = 'none'; node.style.transition = 'none'
    }
    Object.assign(visual.style, { position: 'relative', inset: 'auto', width: '100%', height: '100%', minWidth: '0', maxWidth: 'none', margin: '0', transform: 'none', opacity: '1', visibility: 'visible' })
  }
  shell.append(visual); document.body.append(shell)
  visual.querySelectorAll('animate,animateMotion,animateTransform').forEach(node => node.remove())
  const hidden = new Map()
  const effects = []
  let animation, cleaned = false, safety
  function hide(element) {
    if (element?.isConnected && !hidden.has(element)) { hidden.set(element, element.style.visibility); element.style.visibility = 'hidden' }
  }
  function cleanup() {
    if (cleaned) return
    cleaned = true; clearTimeout(safety); animation?.cancel()
    effects.forEach(effect => effect.cancel())
    hidden.forEach((visibility, element) => { if (element.isConnected) element.style.visibility = visibility })
    shell.remove(); if (active === handle) active = null
  }
  async function playTo(target, { duration = preserveContent ? 440 : 560, hideSource = false, holdTarget = true, waitForTarget = true } = {}) {
    try {
      let destination
      for (let attempt = 0; attempt < (waitForTarget ? 24 : 1) && !cleaned && !document.hidden; attempt++) {
        destination = elementOf(target)
        if (destination?.isConnected && valid(destination.getBoundingClientRect())) break
        if (waitForTarget) await frame()
      }
      if (cleaned || document.hidden) return false
      const end = destination?.isConnected ? destination.getBoundingClientRect() : null
      if (!valid(end)) {
        if (preserveContent) {
          animation = shell.animate([{ opacity: 1 }, { opacity: 0 }], { duration: 160, fill: 'forwards' })
          await animation.finished.catch(() => {})
        }
        return false
      }
      if (hideSource) hide(source)
      if (holdTarget && !preserveContent) hide(destination)
      shell.style.willChange = 'transform, opacity'
      const sx = end.width / start.width, sy = end.height / start.height
      const finish = `translate3d(${end.left - start.left}px,${end.top - start.top}px,0) scale(${sx},${sy})`
      const easing = 'cubic-bezier(.22,.75,.22,1)'
      if (preserveContent) {
        // Counter-scale the content: the card changes shape while its lettering stays legible.
        const contentFrames = Array.from({ length: 13 }, (_, index) => {
          const offset = index / 12
          return { offset, transformOrigin: '0 0', transform: `scale(${1 / (1 + (sx - 1) * offset)},${1 / (1 + (sy - 1) * offset)})` }
        })
        const contentEffect = visual.animate(contentFrames, { duration, easing, fill: 'both' })
        const arrive = destination.animate([{ opacity: 0 }, { opacity: 0, offset: .36 }, { opacity: 1 }], { duration, easing, fill: 'both' })
        for (const effect of [contentEffect, arrive]) { effect.finished.catch(() => {}); effects.push(effect) }
      }
      animation = shell.animate(preserveContent ? [
        { transform: 'translate3d(0,0,0) scale(1,1)', opacity: 1 },
        { transform: finish, opacity: 0 }
      ] : [
        { transform: 'translate3d(0,0,0) scale(1,1)', opacity: 1 },
        { transform: finish, opacity: 1, offset: .86 },
        { transform: finish, opacity: 0 }
      ], { duration, easing, fill: 'forwards' })
      await animation.finished.catch(() => {})
      return !cleaned
    } catch { return false } finally { cleanup() }
  }
  const handle = { playTo, cancel: cleanup }
  active = handle
  safety = setTimeout(cleanup, 3500)
  return handle
}

export async function morphNavigation(source, navigate, target, { remember, from, state, afterNavigate, image, round, returning = false } = {}) {
  source = elementOf(source)
  const shot = captureMotion(source, { image, round, preserveContent: !image && !round })
  if (remember && from && source) rememberMotionReturn(remember, from, source, state)
  if (!shot) {
    try { const result = await navigate(); await nextTick(); if (!result) afterNavigate?.(); return !result } catch { return false }
  }
  routeMotion++
  try {
    const result = await navigate()
    if (result) { shot?.cancel(); return false }
    await nextTick()
    afterNavigate?.()
    if (!document.hidden) await frame()
    if (shot) await shot.playTo(target, { waitForTarget: !returning, hideSource: true })
    return true
  } catch { shot?.cancel(); return false } finally {
    routeMotion = Math.max(0, routeMotion - 1)
    if (!routeMotion) {
      const callbacks = [...settledCallbacks]; settledCallbacks.clear()
      callbacks.forEach(callback => callback())
    }
  }
}

export function routeDestination(selector) {
  return () => document.querySelector(`.page-view:not(.page-leave-active) ${selector}`)
}

export async function flyExchangeReceipt(source, target, { name, points }) {
  const origin = elementOf(source), destination = elementOf(target)
  if (!origin?.isConnected || !destination?.isConnected || document.hidden || typeof origin.animate !== 'function') return
  const bounds = origin.getBoundingClientRect(), receipt = document.createElement('div')
  receipt.className = 'exchange-motion-receipt'
  const stamp = document.createElement('span'), title = document.createElement('strong'), caption = document.createElement('small')
  stamp.textContent = '✓ 兑换成功'; title.textContent = name; caption.textContent = `${points} 积分 · 已加入兑换记录`
  receipt.append(stamp, title, caption)
  Object.assign(receipt.style, { position: 'fixed', left: `${bounds.left + bounds.width / 2 - 120}px`, top: `${bounds.top + bounds.height / 2 - 72}px`, width: '240px', height: '144px', zIndex: '4000' })
  document.body.append(receipt)
  const shot = captureMotion(receipt)
  receipt.remove()
  if (shot) await shot.playTo(destination, { duration: 760, holdTarget: false })
}
