<template>
  <div class="home-page">
    <!-- 顶部导航栏 -->
    <el-header class="main-header">
      <div class="header-content">
        <h1 class="title-text">AI辅助编程学习平台</h1>
        <p class="title-subtext">一站式编程答疑 · 实时代码辅助 · 多语言学习</p>
      </div>
    </el-header>
    <!-- 独立导航栏（放在标题下方，主内容上方） -->
    <div class="top-nav-container">
      <el-menu class="top-nav" mode="horizontal" background-color="rgba(255, 255, 255, 0.95)" text-color="#333" active-text-color="#4096ff">
        <el-menu-item index="1" class="nav-item">首页</el-menu-item>
        <el-menu-item index="2" class="nav-item">学习中心</el-menu-item>
        <el-menu-item index="3" class="nav-item">资源库</el-menu-item>
        <el-menu-item index="4" class="nav-item">论坛</el-menu-item>
        <el-menu-item index="5" class="nav-item">登录/注册</el-menu-item>
        <el-menu-item index="6" class="nav-item">帮助</el-menu-item>
        <el-menu-item index="7" class="nav-search">
          <el-input placeholder="搜索内容..." size="small" prefix-icon="Search" style="width: 200px;" />
        </el-menu-item>
      </el-menu>
    </div>

    <!-- 主内容区（完整正确结构） -->
<el-container>
  <!-- 左侧侧边栏 -->
  <el-aside width="220px" class="lang-aside">
    <div class="aside-header">
      <span>选择编程语言</span>
    </div>
    <el-menu
      default-active="javascript"
      class="lang-menu"
      @select="handleLangSelect"
      background-color="rgba(255, 255, 255, 0.9)"
      text-color="#333"
      active-text-color="#4096ff"
    >
      <el-menu-item index="javascript">
        <span>JavaScript</span>
      </el-menu-item>
      <el-menu-item index="python">
        <span>Python</span>
      </el-menu-item>
      <el-menu-item index="java">
        <span>Java</span>
      </el-menu-item>
      <el-menu-item index="c">
        <span>C</span>
      </el-menu-item>
      <el-menu-item index="vue">
        <span>Vue</span>
      </el-menu-item>
      <el-menu-item index="react">
        <span>React</span>
      </el-menu-item>
    </el-menu>
  </el-aside>

  <!-- 右侧主内容 -->
  <el-main class="main-content">
    <el-row :gutter="24">
      <!-- 代码编辑器卡片 -->
      <el-col :span="12">
        <div class="content-card">
          <div class="card-header">
            <h3 class="card-title">代码编辑器 ({{ currentLang }})</h3>
            <el-button type="text" class="card-action" @click="clearCode">清空代码</el-button>
          </div>
          <div class="card-body">
            <CodeEditor />
          </div>
          <div class="card-footer">
            <el-button size="small" type="primary" @click="formatCode">格式化代码</el-button>
            <el-button size="small" type="success" @click="runCode">运行代码</el-button>
            <el-button size="small" type="info" @click="exportCode">导出代码</el-button>
          </div>
        </div>
      </el-col>

      <!-- AI问答卡片 -->
      <el-col :span="12">
        <div class="content-card">
          <div class="card-header">
            <h3 class="card-title">AI编程助手</h3>
            <el-button type="text" class="card-action" @click="clearChat">清空对话</el-button>
          </div>
          <div class="card-body">
            <AiChat />
          </div>
          <div class="card-footer ai-tips">
            <el-tag size="small" type="info">支持：代码解释、Bug修复、逻辑优化、语法讲解</el-tag>
          </div>
        </div>
      </el-col>
    </el-row>
  </el-main>
</el-container>

    <!-- 底部信息 -->
    <el-footer class="main-footer">
      <p>© 2026 AI辅助编程学习平台 - 让编程学习更简单</p>
    </el-footer>
  </div>
</template>

<script setup>
import { computed, ref } from 'vue'
import { useAiStore } from '@/store/aiStore'
import CodeEditor from '@/components/CodeEditor.vue'
import AiChat from '@/components/AiChat.vue'
// 引入Element Plus的消息提示（必须）
import { ElMessage } from 'element-plus'

const aiStore = useAiStore()
const currentLang = computed(() => aiStore.currentLang)
// 代码运行结果
const runResult = ref('')

// 切换编程语言
const handleLangSelect = (lang) => {
  aiStore.updateCurrentLang(lang)
}

// 清空代码
const clearCode = () => {
  aiStore.updateCurrentCode('')
  ElMessage.info('代码已清空')
}

// 清空聊天记录
const clearChat = () => {
  aiStore.clearChatHistory()
  ElMessage.info('聊天记录已清空')
}

// 简化版：格式化代码（原生实现，无依赖）
const formatCode = () => {
  const code = aiStore.currentCode
  if (!code) return ElMessage.warning('请先输入代码')

  // 基础缩进格式化（适配多数语言）
  try {
    // 按行分割，给非空行添加2个空格缩进
    const lines = code.split('\n')
    const formattedLines = lines.map(line => {
      return line.trim() ? `  ${line}` : line
    })
    const formattedCode = formattedLines.join('\n')
    
    aiStore.updateCurrentCode(formattedCode)
    ElMessage.success('代码格式化成功')
  } catch (err) {
    ElMessage.error('格式化失败，请检查代码')
  }
}

// 简化版：运行代码（前端模拟）
const runCode = () => {
  const code = aiStore.currentCode
  if (!code) return ElMessage.warning('请先输入代码')

  ElMessage.info('开始运行代码...')
  setTimeout(() => {
    switch (currentLang.value) {
      case 'javascript':
        try {
          // 仅模拟JS运行（前端安全版，避免全局eval风险）
          const result = Function(`"use strict"; return (${code})`)()
          ElMessage.success(`运行成功！结果：${result}`)
        } catch (err) {
          ElMessage.error(`运行失败：${err.message}`)
        }
        break
      default:
        ElMessage.info(`暂不支持${currentLang.value}语言的前端运行，可对接后端接口实现`)
    }
  }, 800)
}

// 简化版：导出代码（原生下载）
const exportCode = () => {
  const code = aiStore.currentCode
  if (!code) return ElMessage.warning('请先输入代码')

  // 创建下载文件
  const blob = new Blob([code], { type: 'text/plain;charset=utf-8' })
  const downloadLink = document.createElement('a')
  downloadLink.href = URL.createObjectURL(blob)
  // 生成带语言和时间的文件名
  const fileName = `编程代码_${currentLang.value}_${new Date().getTime()}.txt`
  downloadLink.download = fileName
  downloadLink.click()
  // 释放URL对象
  URL.revokeObjectURL(downloadLink.href)
  
  ElMessage.success(`代码已导出：${fileName}`)
}
</script>

<style scoped>
/* 全局页面样式 */
.home-page {
  height: 100%;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
}

/* 顶部标题区 */
.title-header {
  background-color: rgba(255, 255, 255, 0.95);
  border-bottom: 1px solid #e8f4ff;
  padding: 20px 0;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.08);
  text-align: center;
  position: relative;
  z-index: 998;
}

/* 独立导航栏容器 */
.top-nav-container {
  background-color: rgba(255, 255, 255, 0.95);
  border-bottom: 1px solid #e8f4ff;
  padding: 10px 0;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);
  position: relative;
  z-index: 999;
  text-align: center;
}

/* 导航栏样式 */
.top-nav {
  border-bottom: none;
  justify-content: center;
  gap: 20px;
}

.nav-item {
  font-size: 14px;
}

.nav-search {
  margin-left: 20px;
}

/* 主内容容器 */
.main-container {
  margin-top: 20px; /* 与导航栏保持距离 */
  padding: 0 24px;
}

/* 主内容区 */
.main-content {
  padding: 24px;
  background-color: transparent;
}

.title-text {
  font-size: 42px;
  font-weight: 700;
  color: #2c3e50;
  margin: 0 0 8px 0;
  letter-spacing: 1px;
}

.title-subtext {
  font-size: 16px;
  color: #666;
  margin: 0 0 12px 0;
}

/* 新增顶部导航样式 */
.top-nav {
  border-bottom: none;
  justify-content: center;
  gap: 20px;
  padding: 10px 0;
}

.nav-item {
  font-size: 14px;
}

.nav-search {
  margin-left: 20px;
}

/* 左侧语言侧边栏 */
.lang-aside {
  background-color: transparent;
  padding: 20px 10px;
}

.aside-header {
  color: white;
  font-size: 16px;
  font-weight: 500;
  margin-bottom: 16px;
  padding: 0 12px;
}

.lang-menu {
  border-radius: 12px;
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.1);
}

/* 主内容区 */
.main-content {
  padding: 24px;
  background-color: transparent;
  margin-top: 60px; /* 增加顶部外边距，彻底避开导航栏 */
}

/* 内容卡片 */
.content-card {
  background: rgba(255, 255, 255, 0.95);
  border-radius: 16px;
  box-shadow: 0 6px 20px rgba(0, 0, 0, 0.1);
  overflow: hidden;
  height: 700px;
  display: flex;
  flex-direction: column;
  transition: all 0.3s ease;
}

.content-card:hover {
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.15);
  transform: translateY(-2px);
}

/* 卡片头部 */
.card-header {
  padding: 16px 20px;
  border-bottom: 1px solid #f0f2f5;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.card-title {
  margin: 0;
  font-size: 18px;
  font-weight: 600;
  color: #2c3e50;
}

.card-action {
  color: #909399;
  transition: color 0.2s;
}

.card-action:hover {
  color: #4096ff;
}

/* 卡片主体 */
.card-body {
  flex: 1;
  padding: 20px;
  overflow: hidden;
}

/* 卡片底部 */
.card-footer {
  padding: 12px 20px;
  border-top: 1px solid #f0f2f5;
  display: flex;
  gap: 8px;
  align-items: center;
}

.ai-tips {
  justify-content: center;
}

/* 底部版权 */
.main-footer {
  text-align: center;
  padding: 16px;
  background-color: rgba(255, 255, 255, 0.9);
  color: #666;
  font-size: 14px;
  border-top: 1px solid #e8f4ff;
}

/* 响应式适配 */
@media (max-width: 1200px) {
  .title-text {
    font-size: 36px;
  }
  .content-card {
    height: 600px;
  }
  .top-nav {
    gap: 10px;
  }
  .nav-search {
    margin-left: 10px;
  }
}

@media (max-width: 768px) {
  .lang-aside {
    width: 180px !important;
  }
  .title-text {
    font-size: 28px;
  }
  .content-card {
    height: 500px;
  }
  .top-nav {
    flex-wrap: wrap;
  }
}
</style>