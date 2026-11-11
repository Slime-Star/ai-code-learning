import { nextTick, onBeforeUnmount } from 'vue'
import { captureMotion } from '@/utils/sharedMotion'

export function useDialogMorph({ source, target, image, round = false, preserveContent = false }) {
  let flight, original, preview
  async function open() {
    flight?.cancel()
    original = source()
    const photograph = original?.matches?.('img') ? original : original?.querySelector?.('img')
    preview = photograph?.complete && photograph.naturalWidth ? photograph.currentSrc || photograph.src : image?.()
    const shot = captureMotion(original, { image: preview, round, preserveContent })
    flight = shot
    await nextTick()
    if (shot) await shot.playTo(target)
    if (flight === shot) flight = null
  }
  function close() {
    flight?.cancel()
    const shot = captureMotion(target(), { image: preview, round, preserveContent })
    flight = shot
    if (shot) shot.playTo(original, { duration: 420, hideSource: true }).finally(() => { if (flight === shot) flight = null })
  }
  function cancel() { flight?.cancel(); flight = null }
  onBeforeUnmount(cancel)
  return { open, close, cancel }
}
