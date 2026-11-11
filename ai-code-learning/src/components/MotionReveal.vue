<template>
  <Transition name="interaction-expand" @before-enter="startEnter" @enter="enter" @after-enter="clearHeight"
    @enter-cancelled="clearHeight" @before-leave="startLeave" @leave="leave" @after-leave="clearHeight" @leave-cancelled="clearHeight">
    <div v-if="open" class="motion-reveal"><slot /></div>
  </Transition>
</template>

<script setup>
defineProps({ open: Boolean })
const startEnter = el => { el.style.height = '0px' }
const enter = el => { void el.offsetHeight; el.style.height = `${el.scrollHeight}px` }
const startLeave = el => { el.style.height = `${el.getBoundingClientRect().height}px` }
const leave = el => { void el.offsetHeight; el.style.height = '0px' }
const clearHeight = el => { el.style.removeProperty('height') }
</script>

<style scoped>
.motion-reveal { display: flow-root; }
.interaction-expand-enter-active, .interaction-expand-leave-active { overflow: hidden; transition: height 220ms cubic-bezier(.2,.75,.25,1), opacity 180ms ease; }
.interaction-expand-enter-from, .interaction-expand-leave-to { opacity: 0; }
</style>
