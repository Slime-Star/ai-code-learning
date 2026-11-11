// Render every triangle into one opaque surface instead of hundreds of 3D DOM layers.
const COLUMNS = 12, ROWS = 8, DURATION = 1280
const clamp = value => Math.max(0, Math.min(1, value))
const smooth = value => value * value * (3 - 2 * value)

export function createTriangleFlip(canvas, sources, options = {}) {
  let context
  try { context = canvas.getContext('2d', { alpha: false }) } catch { return null }
  if (typeof context?.drawImage !== 'function') return null

  const images = new Map(), pending = new Map(), fitted = new Map()
  let disposed = false, failed = false, ready = false, visible = true, frame = 0
  let width = 0, height = 0, ratio = 1, triangles = []
  let current = null, target = null, desired = options.initialIndex ?? 0, started = 0, pausedAt = null
  let resizeObserver, intersectionObserver

  function load(index) {
    if (images.has(index)) return Promise.resolve(images.get(index))
    if (pending.has(index)) return pending.get(index)
    const promise = new Promise((resolve, reject) => {
      const image = new Image()
      image.decoding = 'async'
      image.onload = async () => {
        try {
          if (typeof image.decode === 'function') await image.decode()
          if (!image.naturalWidth || !image.naturalHeight) throw new Error('Empty carousel image')
          if (!disposed) images.set(index, image)
          resolve(image)
        } catch (error) { reject(error) }
      }
      image.onerror = () => reject(new Error('Carousel image unavailable'))
      image.src = sources[index]
    }).finally(() => pending.delete(index))
    pending.set(index, promise)
    return promise
  }

  function texture(index) {
    if (fitted.has(index)) return fitted.get(index)
    const image = images.get(index), surface = document.createElement('canvas')
    surface.width = canvas.width; surface.height = canvas.height
    const paint = surface.getContext('2d', { alpha: false })
    const scale = Math.max(surface.width / image.naturalWidth, surface.height / image.naturalHeight)
    const sw = surface.width / scale, sh = surface.height / scale
    paint.drawImage(image, (image.naturalWidth - sw) / 2, (image.naturalHeight - sh) / 2, sw, sh, 0, 0, surface.width, surface.height)
    fitted.set(index, surface)
    return surface
  }

  function geometry() {
    triangles = []
    for (let row = 0; row < ROWS; row++) for (let col = 0; col < COLUMNS; col++) {
      const x = col * width / COLUMNS, y = row * height / ROWS
      const right = (col + 1) * width / COLUMNS, bottom = (row + 1) * height / ROWS
      const a = [x, y], b = [right, y], c = [right, bottom], d = [x, bottom]
      const halves = (col + row) % 2 ? [[a, b, d], [b, c, d]] : [[a, b, c], [a, c, d]]
      halves.forEach((points, half) => {
        const center = [0, 1].map(axis => points.reduce((sum, point) => sum + point[axis], 0) / 3)
        const [p, q, r] = points
        triangles.push({ points, center,
          determinant: (q[0] - p[0]) * (r[1] - p[1]) - (r[0] - p[0]) * (q[1] - p[1]),
          delay: 580 * (.58 * col / (COLUMNS - 1) + .42 * (ROWS - 1 - row) / (ROWS - 1)) + half * 8
        })
      })
    }
  }

  function drawTriangle(surface, triangle, angle, opacity) {
    if (opacity < .002) return
    const cosine = Math.cos(angle), sine = Math.sin(angle), axis = Math.SQRT1_2
    const destination = triangle.points.map(point => {
      const x = point[0] - triangle.center[0], y = point[1] - triangle.center[1]
      const dot = (x + y) * axis, z = axis * (y - x) * sine, perspective = 280 / (280 - z)
      return [triangle.center[0] + (x * cosine + axis * dot * (1 - cosine)) * perspective,
        triangle.center[1] + (y * cosine + axis * dot * (1 - cosine)) * perspective]
    })
    const [p, q, r] = triangle.points, [a, b, c] = destination, determinant = triangle.determinant
    const xx = ((b[0] - a[0]) * (r[1] - p[1]) - (c[0] - a[0]) * (q[1] - p[1])) / determinant
    const xy = ((c[0] - a[0]) * (q[0] - p[0]) - (b[0] - a[0]) * (r[0] - p[0])) / determinant
    const yx = ((b[1] - a[1]) * (r[1] - p[1]) - (c[1] - a[1]) * (q[1] - p[1])) / determinant
    const yy = ((c[1] - a[1]) * (q[0] - p[0]) - (b[1] - a[1]) * (r[0] - p[0])) / determinant
    // Overlap the clip edge slightly so fractional pixels cannot expose a hairline gap.
    const center = [0, 1].map(axis => destination.reduce((sum, point) => sum + point[axis], 0) / 3)
    const clip = destination.map(point => point.map((value, axis) => center[axis] + (value - center[axis]) * 1.045))
    context.save()
    context.globalAlpha = opacity
    context.beginPath(); context.moveTo(...clip[0]); context.lineTo(...clip[1]); context.lineTo(...clip[2]); context.closePath(); context.clip()
    context.transform(xx, yx, xy, yy, a[0] - xx * p[0] - xy * p[1], a[1] - yx * p[0] - yy * p[1])
    context.drawImage(surface, 0, 0, width, height)
    context.restore()
  }

  function paint(now) {
    if (current === null || !width || !height) return false
    context.setTransform(ratio, 0, 0, ratio, 0, 0)
    context.globalAlpha = 1
    const previous = texture(current)
    // Every frame begins with an opaque, decoded image. Never clear to a blank surface.
    context.drawImage(previous, 0, 0, width, height)
    if (target === null) return true
    const next = texture(target), elapsed = Math.max(0, (pausedAt ?? now) - started)
    context.globalAlpha = smooth(clamp(elapsed / 1000))
    context.drawImage(next, 0, 0, width, height)
    context.globalAlpha = 1
    for (const triangle of triangles) {
      const outgoing = clamp((elapsed - triangle.delay) / 420)
      const incoming = clamp((elapsed - triangle.delay - 160) / 520)
      if (outgoing < 1) drawTriangle(previous, triangle, -Math.PI / 2 * outgoing * outgoing, 1 - smooth(outgoing))
      if (incoming > 0) drawTriangle(next, triangle, Math.PI / 2 * (1 - incoming) ** 3, smooth(clamp(incoming * 2)))
    }
    context.globalAlpha = 1
    return true
  }

  function reveal() {
    if (!ready) { ready = true; options.onReady?.() }
  }

  function fail() {
    if (disposed) return
    failed = true; cancelAnimationFrame(frame); frame = 0
    options.onError?.()
  }
  function wake() {
    if (!disposed && !failed && target !== null && pausedAt === null && !frame) frame = requestAnimationFrame(tick)
  }
  function tick(now) {
    frame = 0
    if (disposed || failed || pausedAt !== null) return
    try {
      paint(now)
      if (now - started >= DURATION) {
        current = target; target = null
        paint(now); options.onChange?.(current)
        if (desired !== current) show(desired)
      } else wake()
    } catch { fail() }
  }
  function visibility() {
    const paused = document.hidden || !visible
    if (paused && pausedAt === null) {
      pausedAt = performance.now(); cancelAnimationFrame(frame); frame = 0
    } else if (!paused && pausedAt !== null) {
      if (target !== null) started += performance.now() - pausedAt
      pausedAt = null; wake()
    }
  }
  function resize() {
    if (disposed || failed) return
    const bounds = canvas.getBoundingClientRect()
    if (!bounds.width || !bounds.height) return
    const nextRatio = Math.min(window.devicePixelRatio || 1, 1.5)
    if (width === bounds.width && height === bounds.height && ratio === nextRatio) return
    width = bounds.width; height = bounds.height; ratio = nextRatio
    canvas.width = Math.max(1, Math.round(width * ratio)); canvas.height = Math.max(1, Math.round(height * ratio))
    for (const surface of fitted.values()) { surface.width = 0; surface.height = 0 }
    fitted.clear(); geometry()
    try { if (paint(performance.now())) reveal() } catch { fail() }
  }
  async function show(index) {
    if (disposed || failed || !Number.isInteger(index) || index < 0 || index >= sources.length) return
    desired = index
    try {
      await load(index)
      if (disposed || failed || desired !== index) return
      if (current === null) {
        current = index
        if (paint(performance.now())) reveal()
        options.onChange?.(current)
      } else if (target === null && current !== index) {
        // Fit the new photograph before touching the currently visible frame.
        texture(index); target = index; started = pausedAt ?? performance.now(); wake()
      }
    } catch {
      if (!disposed) options.onImageError?.(index)
      // The previous decoded photograph stays visible if loading the next one fails.
    }
  }
  function dispose() {
    if (disposed) return
    disposed = true; cancelAnimationFrame(frame); frame = 0
    resizeObserver?.disconnect(); intersectionObserver?.disconnect()
    document.removeEventListener('visibilitychange', visibility); window.removeEventListener('resize', resize)
    canvas.removeEventListener('contextlost', fail)
    for (const surface of fitted.values()) { surface.width = 0; surface.height = 0 }
    fitted.clear(); images.clear()
  }

  resize(); visibility()
  document.addEventListener('visibilitychange', visibility); window.addEventListener('resize', resize, { passive: true })
  canvas.addEventListener('contextlost', fail)
  if (typeof ResizeObserver !== 'undefined') { resizeObserver = new ResizeObserver(resize); resizeObserver.observe(canvas) }
  if (typeof IntersectionObserver !== 'undefined') {
    intersectionObserver = new IntersectionObserver(entries => { visible = entries[0]?.isIntersecting ?? true; visibility() })
    intersectionObserver.observe(canvas)
  }
  show(desired)
  sources.forEach((_, index) => { load(index).catch(() => {}) })
  return { show, dispose }
}
