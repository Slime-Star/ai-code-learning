<template>
  <el-dialog :model-value="open" :title="course?.name || '课程播放'" width="min(1100px, 94vw)"
    top="6vh" class="motion-morph-dialog" destroy-on-close append-to-body @open="motion.open" @close="closePlayer" @update:model-value="$emit('update:open', $event)">
    <div v-if="course" class="course-player">
      <div ref="mediaStage" v-loading="loading" element-loading-background="rgba(15, 23, 42, .7)" class="media-stage">
        <iframe v-if="media?.type === 'bilibili'" :key="`${media.src}-${attempt}`" :src="media.src"
          :title="`${course.name} 视频播放器`" allow="fullscreen; picture-in-picture" allowfullscreen
          referrerpolicy="strict-origin-when-cross-origin" @load="onLoaded" @error="onError" />
        <video v-else-if="media?.type === 'file'" ref="videoRef" :key="`${media.src}-${attempt}`" :src="media.src" :poster="course.cover"
          controls playsinline preload="metadata" @loadedmetadata="restorePosition" @error="onError"
          @timeupdate="savePosition(false)" @pause="savePosition(true)" @ended="savePosition(true)" />
        <div v-else class="media-empty">暂未配置可播放的视频</div>
      </div>
      <el-alert v-if="error" :title="error" type="warning" :closable="false" show-icon><el-button size="small" @click="attempt++">重新加载视频</el-button></el-alert>
      <div class="player-details">
        <div>
          <el-tag size="small">{{ media?.type === 'bilibili' ? 'B 站课程' : '视频课程' }}</el-tag>
          <span class="teacher">{{ course.teacher }} · {{ course.level }} · {{ course.duration }}</span>
          <p>{{ course.desc }}</p>
        </div>
        <a v-if="original" :href="original" target="_blank" rel="noopener noreferrer" class="source-link">在 B 站打开 ↗</a>
      </div>
      <p v-if="media?.type === 'bilibili'" class="player-hint">视频由 B 站提供；如遇到播放限制或加载失败，可打开原站观看。</p>
    </div>
  </el-dialog>
</template>

<script setup>
import { computed, ref, watch, onBeforeUnmount } from 'vue'
import { resolveCourseVideo } from '@/utils/courseVideo'
import courseVideos from '@/config/courseVideos.json'
import {useDialogMorph} from '@/composables/useDialogMorph'

const props = defineProps({ open: Boolean, course: { type: Object, default: null }, resume: { type: Object, default: null }, origin: { default: null } })
const emit = defineEmits(['update:open', 'progress'])
const videoRef = ref(null)
const mediaStage = ref(null)
const motion = useDialogMorph({source:()=>props.origin,target:()=>mediaStage.value,image:()=>props.course?.cover})
function closePlayer(){savePosition(true);if(videoRef.value && !videoRef.value.paused)videoRef.value.pause();motion.close()}
let lastSavedAt = 0
const loading = ref(false)
const error = ref('')
const attempt=ref(0)
let loadTimer
const media = computed(() => resolveCourseVideo(props.course?.managed ? props.course.videoUrl : (courseVideos[String(props.course?.id)] || props.course?.videoUrl), import.meta.env.BASE_URL))
const original = computed(() => resolveCourseVideo(props.course?.videoUrl)?.original)
watch(() => [props.open, media.value?.src,attempt.value], () => {
  clearTimeout(loadTimer)
  loading.value = props.open && !!media.value
  error.value = ''
  if(loading.value)loadTimer=setTimeout(()=>{
    loading.value=false
    error.value=original.value ? '视频加载时间较长，可以重新加载，或打开课程原站观看。' : '视频加载时间较长，请检查网络后重新加载。'
  },15000)
}, { immediate: true })
watch(() => props.open, open => { if (!open) savePosition(true) })
onBeforeUnmount(() => {clearTimeout(loadTimer);savePosition(true)})
function onLoaded(){clearTimeout(loadTimer);loading.value=false;error.value=''}
function restorePosition() {
  onLoaded()
  lastSavedAt = 0
  const video = videoRef.value
  const resume = props.resume
  if (video && resume?.source === media.value?.src && Number.isFinite(resume.position)
      && resume.position > 0 && resume.position < video.duration - 2) {
    video.currentTime = resume.position
  }
}
function savePosition(force) {
  const video = videoRef.value
  if (!video || video.readyState < 1 || !Number.isFinite(video.duration) || !video.duration) return
  if (!force && Date.now() - lastSavedAt < 5000) return
  lastSavedAt = Date.now()
  emit('progress', { position: video.currentTime, duration: video.duration, source: media.value.src })
}
function onError() {
  clearTimeout(loadTimer)
  loading.value = false
  error.value = '视频加载失败，请检查网络或视频文件地址后重试。'
}
</script>

<style scoped>
.course-player { display: grid; gap: 18px; }
.media-stage { aspect-ratio: 16 / 9; background: #0f172a; border-radius: 14px; overflow: hidden; }
.media-stage iframe, .media-stage video { display: block; width: 100%; height: 100%; border: 0; }
.media-empty { height: 100%; display: grid; place-items: center; color: #cbd5e1; }
.player-details { display: flex; gap: 16px; justify-content: space-between; align-items: flex-start; }
.teacher { margin-left: 12px; font-size: 13px; color: #64748b; }
.player-details p { margin-top: 12px; line-height: 1.7; color: #475569; }
.source-link { flex-shrink: 0; color: #2563eb; text-decoration: none; padding: 6px 0; }
.player-hint { font-size: 12px; line-height: 1.6; color: #64748b; }
@media (max-width: 640px) {
  .player-details { flex-direction: column; }
  .teacher { display: block; margin: 10px 0 0; }
}
</style>
