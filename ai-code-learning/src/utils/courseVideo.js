// Accept playable media files and Bilibili's official embed, never a webpage as a <video> source.
export function resolveCourseVideo(source, baseUrl = '/') {
  if (!source || typeof source !== 'string') return null
  try {
    const url = new URL(source, 'https://local.invalid')
    if (!['https:', 'http:'].includes(url.protocol)) return null
    if (['www.bilibili.com', 'bilibili.com', 'player.bilibili.com'].includes(url.hostname)) {
      const bvid = url.pathname.match(/\/video\/(BV[a-zA-Z0-9]+)/)?.[1] || url.searchParams.get('bvid')
      if (!/^BV[a-zA-Z0-9]+$/.test(bvid || '')) return null
      const page = Math.max(1, parseInt(url.searchParams.get('p'), 10) || 1)
      return {
        type: 'bilibili',
        src: `https://player.bilibili.com/player.html?bvid=${bvid}&p=${page}&autoplay=0&danmaku=0`,
        original: `https://www.bilibili.com/video/${bvid}/?p=${page}`
      }
    }
    if (!/\.(mp4|webm|ogg|ogv)$/i.test(url.pathname)) return null
    // Local public assets must respect Vite's deployment base.
    const src = url.hostname === 'local.invalid'
      ? `${baseUrl.replace(/\/$/, '')}/${source.replace(/^\//, '')}`
      : url.href
    return { type: 'file', src }
  } catch {
    return null
  }
}
