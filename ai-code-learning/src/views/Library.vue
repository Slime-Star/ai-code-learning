<template>
  <div class="page-root">
    <div class="page-container">
      <!-- 页面标题 -->
      <div class="resource-hero"><div class="resource-hero-copy"><span class="resource-eyebrow">YOUR CODING TOOLBOX</span><h2 class="page-title">编程资源库</h2><p>工具、文档与源码，为下一次实践做好准备。</p><span class="resource-hero-hint">点击右侧文件卡片，快速选择资源分类 ↗</span></div><ContentBoundary silent><ResourceShelf :category="selectCate" @select="changeTag" /></ContentBoundary></div>

      <!-- 资源搜索+筛选区域 -->
      <div class="resource-search">
        <el-row :gutter="20" align="middle">
          <el-col :span="12">
            <el-input
              v-model="searchKey"
              placeholder="搜索资源（名称/关键词）"
              size="default"
              prefix-icon="Search"
              @input="filterResource"
              style="width: 100%;"
            />
          </el-col>
          <el-col :span="8">
            <el-select
              v-model="selectCate"
              placeholder="筛选资源分类"
              size="default"
              style="width: 100%;"
              @change="filterResource"
            >
              <el-option label="全部资源" value="" />
              <el-option
                v-for="cate in cateList"
                :key="cate.id"
                :label="cate.name"
                :value="cate.id"
              />
            </el-select>
          </el-col>
          <el-col :span="4">
            <el-button
              type="primary"
              size="default"
              style="width: 100%;"
              @click="resetFilter"
            >
              重置筛选
            </el-button>
          </el-col>
        </el-row>
      </div>

      <!-- 资源分类标签栏 -->
      <div class="resource-tags">
        <el-tag
          v-for="cate in cateList"
          :key="cate.id"
          :type="activeTag === cate.id ? 'primary' : 'info'"
          @click="changeTag(cate.id)"
          class="tag-item"
        >
          {{ cate.name }} ({{ getCateCount(cate.id) }})
        </el-tag>
      </div>

      <!-- 资源列表区域 -->
      <div class="resource-list">
        <el-empty v-if="filterResourceList.length === 0" description="暂无匹配的资源" />
        <el-card
          v-else
          shadow="hover"
          class="resource-card"
          v-for="(item, index) in paginatedResourceList"
          :key="index"
        >
          <div class="resource-card-content">
            <!-- 资源左侧信息 -->
            <div class="resource-left">
              <h3 class="resource-name">{{ item.name }}</h3>
              <p class="resource-desc">{{ item.desc }}</p>
              <div class="resource-meta">
                <span class="meta-item">{{ item.size }}</span>
                <span class="meta-item">{{ item.format }}</span>
                <span class="meta-item">下载{{ item.download }}次</span>
                <span class="meta-item">{{ item.updateTime }}</span>
              </div>
              <div class="resource-tags-small">
                <el-tag
                  v-for="tag in item.tags"
                  :key="tag"
                  size="small"
                  type="info"
                >
                  {{ tag }}
                </el-tag>
              </div>
            </div>
            <!-- 资源右侧操作 -->
            <div class="resource-right">
              <el-button
                type="primary"
                size="small"
                icon="View"
                @click="showDetail(item)"
                style="margin-right: 10px;"
              >
                详情
              </el-button>
              <el-button
                type="success"
                size="small"
                icon="Download"
                @click="downloadResource(item)"
              >
                下载
              </el-button>
            </div>
          </div>
        </el-card>
      </div>

      <!-- 分页组件 -->
      <div class="resource-pagination" v-if="filterResourceList.length > 0">
        <el-pagination
          @size-change="handleSizeChange"
          @current-change="handleCurrentChange"
          :current-page="currentPage"
          :page-sizes="[6, 12, 18, 24]"
          :page-size="pageSize"
          layout="total, sizes, prev, pager, next, jumper"
          :total="filterResourceList.length"
        >
        </el-pagination>
      </div>

      <!-- 资源详情弹窗 -->
      <el-dialog
        v-model="detailDialog"
        title="资源详情"
        width="600px"
        center
        destroy-on-close
      >
        <div class="detail-content" v-if="currentResource">
          <h4 class="detail-name">{{ currentResource.name }}</h4>
          <div class="detail-meta">
            <span class="detail-item">资源分类：{{ getCateName(currentResource.cateId) }}</span>
            <span class="detail-item">文件格式：{{ currentResource.format }}</span>
            <span class="detail-item">文件大小：{{ currentResource.size }}</span>
          </div>
          <div class="detail-meta">
            <span class="detail-item">更新时间：{{ currentResource.updateTime }}</span>
            <span class="detail-item">下载次数：{{ currentResource.download }}</span>
            <span class="detail-item">资源标签：{{ currentResource.tags.join('、') }}</span>
          </div>
          <div class="detail-desc">
            <h5>资源描述：</h5>
            <p>{{ currentResource.detailDesc }}</p>
          </div>
          <div class="detail-use">
            <h5>使用说明：</h5>
            <p>{{ currentResource.useDesc }}</p>
          </div>
        </div>
        <template #footer>
          <span class="dialog-footer">
            <el-button @click="detailDialog = false">取消</el-button>
            <el-button
              type="success"
              icon="Download"
              @click="downloadResource(currentResource); detailDialog = false"
            >
              立即下载
            </el-button>
          </span>
        </template>
      </el-dialog>
    </div>
    <WhitespaceGame scene="books" game="color" inverse />
    <CodeTicker inverse />
  </div>
</template>

<script setup>
import WhitespaceGame from '@/components/WhitespaceGame.vue'
import ResourceShelf from '@/components/ResourceShelf.vue'
import ContentBoundary from '@/components/ContentBoundary.vue'
import CodeTicker from '@/components/CodeTicker.vue'
// 导入Element Plus组件
import { ElCard, ElInput, ElSelect, ElOption, ElButton, ElTag, ElEmpty, ElPagination, ElDialog, ElMessage } from 'element-plus'
// 导入Vue响应式数据
import { ref, computed, onMounted } from 'vue'
import axios from 'axios'

// 1. 基础筛选数据
const searchKey = ref('')
const selectCate = ref('')
const activeTag = ref('')
const currentPage = ref(1)
const pageSize = ref(6)
const detailDialog = ref(false)
const currentResource = ref(null)

// 2. 资源分类列表
const cateList = ref([
  { id: '', name: '全部' }, 
  { id: 1, name: '开发工具' },
  { id: 2, name: '学习资料' },
  { id: 3, name: '源码案例' },
  { id: 4, name: '插件扩展' },
  { id: 5, name: '面试题库' },
  { id: 6, name: '环境配置' }
])

// 3. 从数据库加载资源
const resourceList = ref([])

onMounted(async () => {
  try {
    const res = await axios.get('/api/resources')
    let data = res.data.data || []

    // 数据库 tags 是字符串，转成数组（必须！）
    data = data.map(item => {
      if (item.tags && typeof item.tags === 'string') {
        item.tags = item.tags.split(',').map(t => t.trim())
      } else {
        item.tags = []
      }
      // 数据库字段 useDesc 可能是 uesDesc，兼容一下
      if (!item.useDesc && item.uesDesc) {
        item.useDesc = item.uesDesc
      }
      return item
    })

    resourceList.value = data
  } catch (err) {
    console.error('加载失败', err)
    ElMessage.error('数据库连接失败，使用本地演示数据')
  }
})

// 4. 筛选后的资源列表
const filterResourceList = computed(() => {
  return resourceList.value.filter(item => {
    const searchMatch = !searchKey.value || item.name.includes(searchKey.value) || item.desc.includes(searchKey.value)
    const cateMatch = !selectCate.value || item.cateId === Number(selectCate.value)
    const tagMatch = !activeTag.value || item.cateId === Number(activeTag.value)
    return searchMatch && cateMatch && tagMatch
  })
})

// 5. 分页
const paginatedResourceList = computed(() => {
  const start = (currentPage.value - 1) * pageSize.value
  const end = start + pageSize.value
  return filterResourceList.value.slice(start, end)
})

// 6. 分类名称
const getCateName = (cateId) => {
  const cate = cateList.value.find(item => item.id === cateId)
  return cate ? cate.name : '未知分类'
}

// 7. 分类数量
const getCateCount = (cateId) => {
  if (cateId === '') return resourceList.value.length
  return resourceList.value.filter(item => item.cateId === cateId).length
}

// 8. 切换标签
const changeTag = (cateId) => {
  activeTag.value = cateId
  selectCate.value = cateId
  currentPage.value = 1
}

// 9. 筛选
const filterResource = () => {
  currentPage.value = 1
}

// 10. 重置
const resetFilter = () => {
  searchKey.value = ''
  selectCate.value = ''
  activeTag.value = ''
  currentPage.value = 1
  ElMessage.success('筛选条件已重置')
}

// 11. 分页
const handleCurrentChange = (val) => {
  currentPage.value = val
  window.scrollTo({ top: 0, behavior: 'smooth' })
}

const handleSizeChange = (val) => {
  pageSize.value = val
  currentPage.value = 1
}

// 12. 详情
const showDetail = (resource) => {
  currentResource.value = resource
  detailDialog.value = true
}

// 13. 下载
const downloadResource = (resource) => {
  if (!resource) return ElMessage.error('请选择要下载的资源')
  
  // 优先取 downloadUrl，没有就提示
  const url = resource.downloadUrl
  if (!url || url.trim() === '') {
    ElMessage.warning('该资源暂无可用下载链接')
    return
  }
  
  window.open(url, '_blank')
  ElMessage.success(`已为您打开【${resource.name}】的下载页面`)
  resource.download += 1
}
</script>

<style scoped>
/* 页面根容器：继承项目渐变背景 */
.page-root {
  width: 100%;
  min-height: 100vh;
  margin: 0;
  padding: 0;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  padding-top: 20px;
  box-sizing: border-box;
}

/* 内容容器：居中、适配项目最大宽度 */
.page-container {
  width: 100%;
  max-width: 1200px;
  margin: 0 auto;
  padding: 0 24px;
}

/* 页面标题：白色字体，和背景对比明显 */
.page-title {
  font-size: 24px;
  font-weight: 600;
  color: #fff;
  margin: 0 0 20px 0;
  letter-spacing: 1px;
}

/* 搜索筛选区域：白色卡片样式，和项目风格统一 */
.resource-search {
  background: rgba(255, 255, 255, 0.95);
  padding: 20px;
  border-radius: 16px;
  box-shadow: 0 6px 20px rgba(0, 0, 0, 0.1);
  margin-bottom: 20px;
}

/* 分类标签栏：横向排列，间距适中 */
.resource-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
  margin-bottom: 20px;
}

/* 标签项：自定义样式，提升点击体验 */
.tag-item {
  cursor: pointer;
  padding: 6px 16px;
  font-size: 14px;
  transition: all 0.3s ease;
}

.tag-item:hover {
  transform: translateY(-2px);
}

/* 资源列表：网格布局，适配不同屏幕 */
.resource-list {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(380px, 1fr));
  gap: 20px;
  margin-bottom: 30px;
}

/* 资源卡片：自定义样式，和项目风格统一 */
.resource-card {
  border-radius: 12px;
  border: none;
  overflow: hidden;
  transition: all 0.3s ease;
  height: 100%;
}

.resource-card:hover {
  transform: translateY(-5px);
  box-shadow: 0 10px 25px rgba(0, 0, 0, 0.15);
}

/* 资源卡片内容：弹性布局，左右分布 */
.resource-card-content {
  display: flex;
  flex-direction: column;
  height: 100%;
}

/* 资源左侧信息 */
.resource-left {
  flex: 1;
  margin-bottom: 15px;
}

.resource-name {
  font-size: 18px;
  font-weight: 600;
  color: #2c3e50;
  margin: 0 0 10px 0;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.resource-desc {
  font-size: 14px;
  color: #666;
  line-height: 1.6;
  margin: 0 0 10px 0;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.resource-meta {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-bottom: 10px;
}

.meta-item {
  font-size: 12px;
  color: #999;
  background: #f5f7fa;
  padding: 2px 8px;
  border-radius: 4px;
}

.resource-tags-small {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}

/* 资源右侧操作：靠右对齐，固定底部 */
.resource-right {
  display: flex;
  justify-content: flex-end;
  align-items: center;
  margin-top: auto;
}

/* 分页组件：居中对齐 */
.resource-pagination {
  display: flex;
  justify-content: center;
  align-items: center;
  padding: 20px 0;
}

/* 详情弹窗样式 */
.detail-content {
  padding: 10px 0;
}

.detail-name {
  font-size: 20px;
  font-weight: 600;
  color: #2c3e50;
  margin: 0 0 15px 0;
  padding-bottom: 10px;
  border-bottom: 1px solid #eee;
}

.detail-meta {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
  margin-bottom: 15px;
}

.detail-item {
  font-size: 14px;
  color: #666;
  background: #f5f7fa;
  padding: 4px 10px;
  border-radius: 6px;
}

.detail-desc, .detail-use {
  margin-bottom: 15px;
}

.detail-desc h5, .detail-use h5 {
  font-size: 16px;
  font-weight: 600;
  color: #333;
  margin: 0 0 8px 0;
}

.detail-desc p, .detail-use p {
  font-size: 14px;
  color: #666;
  line-height: 1.8;
  text-align: justify;
}

.dialog-footer {
  text-align: right;
}

/* 响应式适配：平板/手机端 */
@media (max-width: 768px) {
  .resource-list {
    grid-template-columns: 1fr;
  }

  .resource-search .el-row {
    flex-direction: column;
  }

  .resource-search .el-col {
    width: 100% !important;
    margin-bottom: 15px;
  }

  .resource-search .el-col:last-child {
    margin-bottom: 0;
  }
}
.resource-hero { display: flex; justify-content: space-between; align-items: center; gap: 28px; padding: 12px 4px 14px; }
.resource-hero-copy { min-width: 0; color: #fff; }
.resource-eyebrow { font: 9px Consolas,monospace; letter-spacing: 2px; color: #e5d8f5a6; }
.resource-hero .page-title { margin: 13px 0 12px; font-size: 32px; }
.resource-hero-copy p { font-size: 14px; line-height: 1.8; color: #eae3f6; margin: 0 0 12px; }
.resource-hero-hint { font-size: 11px; color: #dfcfefb0; }
.resource-hero :deep(.resource-shelf) { flex-shrink: 0; }
@media(max-width:850px){.resource-hero{flex-direction:column;gap:6px;text-align:center}.resource-hero .page-title{font-size:28px}.resource-hero-copy p{font-size:13px}.resource-hero-hint{display:none}}
</style>
