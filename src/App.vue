<template>
  <router-view></router-view>
</template>

<script setup>
// 根组件仅作为路由出口，无需额外代码
</script>

<style>
/* 全局样式重置 */
* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

html, body, #app {
  height: 100%;
  overflow: hidden;
}
</style>