<template>
  <div class="points-mall">
    <!-- 顶部横幅 -->
    <div class="banner">
      <div class="banner-content">
        <div class="user-points">
          <div class="points-icon">💰</div>
          <div class="points-info">
            <div class="points-label">我的积分</div>
            <div class="points-value"><AnimatedNumber :value="userPoints" :animate="exchangeSucceeded" /></div>
          </div>
        </div>
        <div class="banner-text">
          <h2 class="banner-title">积分商城</h2>
          <p class="banner-desc">用积分兑换精美礼品，学习更有动力！</p>
        </div>
      </div>
    </div>

    <!-- 分类筛选 -->
    <div class="filter-section">
      <div class="container filter-row">
        <div class="filter-tabs">
          <button 
            v-for="tab in tabs" 
            :key="tab.id"
            :class="['tab-btn', { active: activeTab === tab.id }]"
            @click="activeTab = tab.id"
          >
            {{ tab.icon }} {{ tab.name }}
          </button>
        </div>
        <div v-if="isTeacher" class="filter-actions">
          <el-button type="primary" @click="openCreateDialog">添加商品</el-button>
        </div>
      </div>
    </div>

    <!-- 商品列表 -->
    <div class="container">
      <div class="goods-grid">
        <div 
          v-for="goods in filteredGoods" 
          :key="goods.id"
          class="goods-card"
        >
          <div class="goods-image">
            <img :src="goods.image" :alt="goods.name" loading="lazy" decoding="async" />
            <div v-if="goods.stock === 0" class="sold-out">已售罄</div>
          </div>
          <div class="goods-info">
            <h3 class="goods-name">{{ goods.name }}</h3>
            <p class="goods-desc">{{ goods.desc }}</p>
            <div class="goods-meta">
              <div class="goods-points">
                <span class="points-label">积分</span>
                <span class="points-num">{{ goods.points }}</span>
              </div>
              <div class="goods-stock">库存: {{ goods.stock }}</div>
            </div>
            <button 
              class="exchange-btn"
              :class="{ disabled: userPoints < goods.points || goods.stock === 0 }"
              :disabled="userPoints < goods.points || goods.stock === 0"
              @click="handleExchange(goods, $event)"
            >
              {{ goods.stock === 0 ? '已售罄' : userPoints < goods.points ? '积分不足' : '立即兑换' }}
            </button>
          </div>
        </div>
      </div>
      <el-empty v-if="filteredGoods.length === 0" description="暂无相关商品" />
    </div>

    <!-- 兑换记录 -->
    <div ref="recordsTarget" class="container exchange-records-target">
      <div class="section-title">
        <h3>📋 我的兑换记录</h3>
      </div>
      <div v-if="exchangeRecords.length === 0" class="empty-records">
        <p>暂无兑换记录</p>
      </div>
      <div v-else class="records-list">
        <div 
          v-for="record in exchangeRecords" 
          :key="record.id"
          class="record-item"
        >
          <img :src="record.image" :alt="record.goodsName" class="record-image" loading="lazy" decoding="async" />
          <div class="record-info">
            <div class="record-name">{{ record.goodsName }}</div>
            <div class="record-meta">
              <span class="record-points">-{{ record.points }}积分</span>
              <span class="record-time">{{ record.time }}</span>
            </div>
          </div>
          <el-tag :type="getStatusType(record.status)" size="small">
            {{ getStatusText(record.status) }}
          </el-tag>
        </div>
      </div>
    </div>

    <!-- 兑换确认弹窗 -->
    <el-dialog
      v-model="confirmVisible"
      title="确认兑换"
      width="min(580px, 94vw)"
      class="motion-morph-dialog"
      @open="goodsMotion.open" @close="closeExchange"
    >
      <div ref="confirmContent" class="confirm-content">
        <div class="confirm-goods">
          <img :src="selectedGoods?.image" :alt="selectedGoods?.name" ref="confirmImage" class="confirm-image" />
          <div class="confirm-info">
            <div class="confirm-name">{{ selectedGoods?.name }}</div>
            <div class="confirm-points">{{ selectedGoods?.points }}积分</div>
          </div>
        </div>
        <div class="confirm-tip">
          <p>确认消耗 <span class="highlight">{{ selectedGoods?.points }}</span> 积分兑换此商品？</p>
          <p>兑换后积分将立即扣除。</p>
        </div>
      </div>
      <template #footer>
        <div class="dialog-footer">
          <el-button @click="confirmVisible = false">取消</el-button>
          <el-button type="primary" :loading="exchanging" @click="confirmExchange">{{ exchanging ? '正在兑换' : '确认兑换' }}</el-button>
        </div>
      </template>
    </el-dialog>

    <el-dialog v-model="createVisible" title="添加商品" width="520px" @closed="onCreateClosed">
      <el-form label-width="90px">
        <el-form-item label="名称">
          <el-input v-model="createForm.name" maxlength="40" show-word-limit placeholder="例如：定制笔记本" />
        </el-form-item>
        <el-form-item label="描述">
          <el-input v-model="createForm.desc" type="textarea" :rows="3" maxlength="200" show-word-limit placeholder="简短介绍（可选）" />
        </el-form-item>
        <el-form-item label="分类">
          <el-select v-model="createForm.category" style="width: 100%">
            <el-option label="文具" value="stationery" />
            <el-option label="数码" value="digital" />
            <el-option label="书籍" value="books" />
            <el-option label="虚拟物品" value="virtual" />
          </el-select>
        </el-form-item>
        <el-form-item label="所需积分">
          <el-input-number v-model="createForm.points" :min="0" :max="200000" :step="10" style="width: 100%" />
        </el-form-item>
        <el-form-item label="库存份数">
          <el-input-number v-model="createForm.stock" :min="0" :max="100000" :step="1" style="width: 100%" />
        </el-form-item>
        <el-form-item label="图片">
          <input class="file-input" type="file" accept="image/*" @change="onPickImage" />
          <div v-if="createPreviewUrl" class="image-preview">
            <img :src="createPreviewUrl" alt="预览" />
          </div>
        </el-form-item>
      </el-form>
      <template #footer>
        <div class="dialog-footer">
          <el-button @click="createVisible = false" :disabled="createSaving">取消</el-button>
          <el-button type="primary" @click="submitCreate" :loading="createSaving">保存</el-button>
        </div>
      </template>
    </el-dialog>

    <TopicArt scene="gift" featured />
  </div>
</template>

<script setup>
import TopicArt from '@/components/TopicArt.vue'
import { ref, computed, onMounted, onBeforeUnmount, watch } from 'vue'
import {useDialogMorph} from '@/composables/useDialogMorph'
import {flyExchangeReceipt} from '@/utils/sharedMotion'
import AnimatedNumber from '@/components/AnimatedNumber.vue'
import { ElMessage } from 'element-plus'
import axios from 'axios'
import { getAuthToken, getCurrentUser } from '@/utils/authStorage'

const userInfo = ref(getCurrentUser())
const userId = computed(() => String(userInfo.value?.id || ''))
const isLogin = computed(() => !!userId.value && userId.value !== 'guest')
const isTeacher = computed(() => String(userInfo.value?.role || '') === 'teacher')
const pointsCacheKey = computed(() => (isLogin.value ? `points_${userId.value}` : 'points_guest'))

// 本地数据 - 商品列表
const localGoods = [
  {
    id: 1,
    name: '定制笔记本',
    desc: '精美定制笔记本，记录学习点滴',
    points: 500,
    stock: 30,
    image: '/images/goods/notebook.png',
    category: 'stationery'
  },
  {
    id: 2,
    name: '钢笔套装',
    desc: '高品质钢笔，书写流畅顺滑',
    points: 800,
    stock: 20,
    image: '/images/goods/pen.png',
    category: 'stationery'
  },
  {
    id: 3,
    name: '编程书籍',
    desc: '精选编程书籍，提升技术水平',
    points: 1200,
    stock: 15,
    image: '/images/goods/book.png',
    category: 'books'
  },
  {
    id: 4,
    name: '精美帆布袋',
    desc: '环保耐用的定制帆布袋',
    points: 300,
    stock: 50,
    image: '/images/goods/bag.png',
    category: 'stationery'
  },
  {
    id: 5,
    name: '鼠标垫',
    desc: '超大号游戏鼠标垫，编程更舒适',
    points: 400,
    stock: 25,
    image: '/images/goods/mousepad.png',
    category: 'digital'
  },
  {
    id: 6,
    name: 'USB充电宝',
    desc: '10000mAh便携充电宝',
    points: 1500,
    stock: 10,
    image: '/images/goods/powerbank.png',
    category: 'digital'
  },
  {
    id: 7,
    name: '学习课程月卡',
    desc: '解锁全部精品课程',
    points: 2000,
    stock: 999,
    image: '/images/goods/course.png',
    category: 'virtual'
  },
  {
    id: 8,
    name: '精美书签',
    desc: '金属质感书签，阅读好伴侣',
    points: 100,
    stock: 100,
    image: '/images/goods/bookmark.png',
    category: 'stationery'
  }
]

// 本地数据 - 兑换记录
const localRecords = [
  {
    id: 1,
    goodsName: '精美书签',
    image: '/images/goods/bookmark.png',
    points: 100,
    time: '2026-05-20 10:30',
    status: 'completed'
  }
]

// 状态
const activeTab = ref('all')
const userPoints = ref(0)
const goods = ref([...localGoods])
const exchangeRecords = ref([])
const confirmVisible = ref(false)
const selectedGoods = ref(null)
const loading = ref(false)

const tabs = [
  { id: 'all', name: '全部', icon: '🏠' },
  { id: 'stationery', name: '文具', icon: '✏️' },
  { id: 'digital', name: '数码', icon: '💻' },
  { id: 'books', name: '书籍', icon: '📚' },
  { id: 'virtual', name: '虚拟物品', icon: '🎁' }
]

const filteredGoods = computed(() => {
  if (activeTab.value === 'all') {
    return goods.value
  }
  return goods.value.filter(g => g.category === activeTab.value)
})

// 加载用户积分
const loadUserPoints = async () => {
  if (!isLogin.value) {
    userPoints.value = 0
    return
  }
  try {
    const res = await axios.get('/api/points', { params: { user_id: userId.value, t: Date.now() } })
    if (res.data && res.data.success) {
      userPoints.value = res.data.points || 0
      try {
        localStorage.setItem(pointsCacheKey.value, String(userPoints.value))
      } catch {}
    }
  } catch (err) {
    console.log('使用本地积分数据')
  }
}

// 加载商品列表
const loadGoods = async () => {
  try {
    const res = await axios.get('/api/points/goods', { 
      params: { category: activeTab.value } 
    })
    if (res.data && res.data.success && res.data.goods) {
      goods.value = res.data.goods
    }
  } catch (err) {
    console.log('使用本地商品数据')
  }
}

// 加载兑换记录
const loadExchangeRecords = async () => {
  if (!isLogin.value) {
    exchangeRecords.value = []
    return
  }
  try {
    const res = await axios.get('/api/points/records', { params: { user_id: userId.value, t: Date.now() } })
    if (res.data && res.data.success && res.data.records) {
      exchangeRecords.value = res.data.records
    }
  } catch (err) {
    console.log('使用本地兑换记录')
  }
}

// 兑换商品
const exchanging=ref(false),exchangeSucceeded=ref(false),goodsOrigin=ref(null),confirmImage=ref(null),confirmContent=ref(null),recordsTarget=ref(null)
const goodsMotion=useDialogMorph({source:()=>goodsOrigin.value,target:()=>confirmImage.value,image:()=>selectedGoods.value?.image})
function closeExchange(){if(exchangeSucceeded.value)goodsMotion.cancel();else goodsMotion.close()}
const handleExchange = (goodsItem, event) => {
  if(exchanging.value)return
  if (!isLogin.value) {
    ElMessage.warning('请先登录')
    return
  }
  
  if (userPoints.value < goodsItem.points) {
    ElMessage.warning('积分不足')
    return
  }
  
  if (goodsItem.stock === 0) {
    ElMessage.warning('商品已售罄')
    return
  }
  
  goodsOrigin.value=event?.currentTarget?.closest('.goods-card')?.querySelector('.goods-image') || event?.currentTarget
  exchangeSucceeded.value=false
  selectedGoods.value = goodsItem
  confirmVisible.value = true
}

const confirmExchange = async () => {
  if (!selectedGoods.value || exchanging.value) return
  exchanging.value=true
  const purchased={...selectedGoods.value}
  try {
    const res = await axios.post('/api/points/exchange', {
      goods_id: selectedGoods.value.id,
      user_id: userId.value
    })
    
    if (res.data && res.data.success) {
      exchangeSucceeded.value=true
      ElMessage.success('兑换成功！')
      await Promise.all([loadUserPoints(), loadGoods(), loadExchangeRecords()])
      const receipt=flyExchangeReceipt(confirmContent.value,()=>recordsTarget.value?.querySelector('.record-image') || recordsTarget.value,{name:purchased.name,points:purchased.points})
      confirmVisible.value = false
      await receipt
    } else {
      ElMessage.error(res.data?.message || '兑换失败')
    }
  } catch (err) {
    ElMessage.error(err?.response?.data?.message || '兑换失败，请稍后重试')
  } finally { exchanging.value=false }
}

const getStatusType = (status) => {
  const map = {
    pending: 'warning',
    completed: 'success',
    cancelled: 'info'
  }
  return map[status] || ''
}

const getStatusText = (status) => {
  const map = {
    pending: '待发货',
    completed: '已完成',
    cancelled: '已取消'
  }
  return map[status] || status
}

const syncUser = () => {
  userInfo.value = getCurrentUser()
  loadUserPoints()
  loadExchangeRecords()
}

const createVisible = ref(false)
const createSaving = ref(false)
const createForm = ref({
  name: '',
  desc: '',
  points: 100,
  stock: 10,
  category: 'stationery'
})
const createImageFile = ref(null)
const createPreviewUrl = ref('')

const openCreateDialog = () => {
  createForm.value = { name: '', desc: '', points: 100, stock: 10, category: 'stationery' }
  createImageFile.value = null
  if (createPreviewUrl.value) {
    try { URL.revokeObjectURL(createPreviewUrl.value) } catch {}
  }
  createPreviewUrl.value = ''
  createVisible.value = true
}

const onPickImage = (e) => {
  const file = e?.target?.files?.[0]
  if (!file) return
  if (!String(file.type || '').startsWith('image/')) {
    ElMessage.warning('请选择图片文件')
    return
  }
  if (file.size > 3 * 1024 * 1024) {
    ElMessage.warning('图片过大（最大 3MB）')
    return
  }
  createImageFile.value = file
  if (createPreviewUrl.value) {
    try { URL.revokeObjectURL(createPreviewUrl.value) } catch {}
  }
  createPreviewUrl.value = URL.createObjectURL(file)
}

const onCreateClosed = () => {
  if (createPreviewUrl.value) {
    try { URL.revokeObjectURL(createPreviewUrl.value) } catch {}
  }
  createPreviewUrl.value = ''
  createImageFile.value = null
  createSaving.value = false
}

const submitCreate = async () => {
  if (createSaving.value) return
  const token = getAuthToken()
  if (!token) {
    ElMessage.warning('请先登录教师账号')
    return
  }
  const name = String(createForm.value?.name || '').trim()
  if (!name) {
    ElMessage.warning('请输入商品名称')
    return
  }
  createSaving.value = true
  try {
    const fd = new FormData()
    fd.append('name', name)
    fd.append('desc', String(createForm.value?.desc || '').trim())
    fd.append('category', String(createForm.value?.category || 'stationery'))
    fd.append('points', String(Number(createForm.value?.points || 0)))
    fd.append('stock', String(Number(createForm.value?.stock || 0)))
    if (createImageFile.value) {
      fd.append('image', createImageFile.value)
    }
    const res = await axios.post('/api/teacher/points/goods', fd, {
      headers: { Authorization: `Bearer ${token}` }
    })
    if (res.data && res.data.success) {
      ElMessage.success('添加成功')
      createVisible.value = false
      await loadGoods()
      return
    }
    ElMessage.error(res.data?.message || res.data?.detail || '添加失败')
  } catch (err) {
    ElMessage.error(err?.response?.data?.detail || err?.response?.data?.message || '添加失败，请稍后重试')
  } finally {
    createSaving.value = false
  }
}

onMounted(async () => {
  try {
    const cached = localStorage.getItem(pointsCacheKey.value)
    const n = Number(cached)
    if (Number.isFinite(n) && n >= 0) userPoints.value = n
  } catch {}

  window.addEventListener('user-updated', syncUser)

  loading.value = true
  try {
    await Promise.all([loadGoods(), loadUserPoints(), loadExchangeRecords()])
  } finally {
    loading.value = false
  }
})

onBeforeUnmount(() => {
  window.removeEventListener('user-updated', syncUser)
})

watch(activeTab, () => {
  loadGoods()
})
</script>

<style scoped>
.points-mall {
  min-height: 100vh;
  background: #f5f7fa;
}

.banner {
  background: linear-gradient(135deg, #f6d365 0%, #fda085 100%);
  padding: 40px 0;
}

.banner-content {
  max-width: 1200px;
  margin: 0 auto;
  padding: 0 24px;
  display: flex;
  align-items: center;
  gap: 40px;
}

.user-points {
  display: flex;
  align-items: center;
  gap: 15px;
  background: rgba(255,255,255,0.3);
  padding: 20px 30px;
  border-radius: 16px;
  backdrop-filter: blur(10px);
}

.points-icon {
  font-size: 48px;
}

.points-info {
  color: #fff;
}

.points-label {
  font-size: 14px;
  opacity: 0.9;
  margin-bottom: 5px;
}

.points-value {
  font-size: 36px;
  font-weight: 800;
}

.banner-text {
  color: #fff;
}

.banner-title {
  font-size: 32px;
  font-weight: 800;
  margin: 0 0 10px;
}

.banner-desc {
  font-size: 16px;
  margin: 0;
  opacity: 0.95;
}

.filter-section {
  background: #fff;
  box-shadow: 0 2px 8px rgba(0,0,0,0.06);
  padding: 20px 0;
}

.container {
  max-width: 1200px;
  margin: 0 auto;
  padding: 30px 24px;
}

.filter-tabs {
  display: flex;
  gap: 12px;
}
.filter-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
}
.filter-actions {
  display: flex;
  justify-content: flex-end;
  flex-shrink: 0;
}
.file-input {
  width: 100%;
}
.image-preview {
  margin-top: 10px;
  width: 100%;
  border-radius: 10px;
  overflow: hidden;
  border: 1px solid #e5e7eb;
  background: #fff;
}
.image-preview img {
  width: 100%;
  height: 160px;
  object-fit: cover;
  display: block;
}

.tab-btn {
  padding: 10px 24px;
  border: none;
  background: #f0f2f5;
  border-radius: 24px;
  font-size: 15px;
  cursor: pointer;
  transition: all 0.3s;
  font-weight: 500;
}

.tab-btn:hover {
  background: #e0e6ed;
}

.tab-btn.active {
  background: linear-gradient(135deg, #f6d365 0%, #fda085 100%);
  color: #fff;
}

.goods-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  gap: 24px;
}

.goods-card {
  background: #fff;
  border-radius: 16px;
  overflow: hidden;
  box-shadow: 0 4px 12px rgba(0,0,0,0.08);
  transition: all 0.3s;
}

.goods-card:hover {
  transform: translateY(-6px);
  box-shadow: 0 12px 28px rgba(0,0,0,0.12);
}

.goods-image {
  position: relative;
  width: 100%;
  height: 200px;
  overflow: hidden;
}

.goods-image img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.sold-out {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0,0,0,0.6);
  display: flex;
  align-items: center;
  justify-content: center;
  color: #fff;
  font-size: 20px;
  font-weight: 700;
}

.goods-info {
  padding: 20px;
}

.goods-name {
  font-size: 18px;
  font-weight: 700;
  margin: 0 0 10px;
  color: #1f2937;
}

.goods-desc {
  font-size: 14px;
  color: #6b7280;
  margin: 0 0 15px;
}

.goods-meta {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 15px;
}

.goods-points {
  display: flex;
  align-items: center;
  gap: 6px;
}

.points-label {
  font-size: 13px;
  color: #909399;
}

.points-num {
  font-size: 24px;
  font-weight: 800;
  color: #f6d365;
}

.goods-stock {
  font-size: 13px;
  color: #909399;
}

.exchange-btn {
  width: 100%;
  padding: 12px;
  border: none;
  border-radius: 10px;
  background: linear-gradient(135deg, #f6d365 0%, #fda085 100%);
  color: #fff;
  font-size: 15px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s;
}

.exchange-btn:hover:not(.disabled) {
  transform: translateY(-2px);
  box-shadow: 0 6px 16px rgba(246, 211, 101, 0.4);
}

.exchange-btn.disabled {
  background: #e0e0e0;
  cursor: not-allowed;
}

.section-title {
  margin-bottom: 20px;
}

.section-title h3 {
  font-size: 20px;
  font-weight: 700;
  color: #1f2937;
  margin: 0;
}

.records-list {
  background: #fff;
  border-radius: 12px;
  padding: 10px;
}

.record-item {
  display: flex;
  align-items: center;
  gap: 15px;
  padding: 15px;
  border-bottom: 1px solid #f0f0f0;
}

.record-item:last-child {
  border-bottom: none;
}

.record-image {
  width: 60px;
  height: 60px;
  border-radius: 8px;
  object-fit: cover;
}

.record-info {
  flex: 1;
}

.record-name {
  font-size: 15px;
  font-weight: 600;
  color: #1f2937;
  margin-bottom: 5px;
}

.record-meta {
  display: flex;
  gap: 15px;
  font-size: 13px;
  color: #6b7280;
}

.record-points {
  color: #fda085;
  font-weight: 600;
}

.empty-records {
  text-align: center;
  padding: 40px;
  color: #909399;
}

.confirm-content {
  text-align: center;
}

.confirm-goods {
  display: flex;
  align-items: center;
  gap: 15px;
  padding: 20px 0;
  border-bottom: 1px solid #f0f0f0;
  margin-bottom: 20px;
}

.confirm-image {
  width: 80px;
  height: 80px;
  border-radius: 10px;
  object-fit: cover;
}

.confirm-info {
  text-align: left;
}

.confirm-name {
  font-size: 16px;
  font-weight: 600;
  margin-bottom: 8px;
}

.confirm-points {
  font-size: 20px;
  font-weight: 700;
  color: #f6d365;
}

.confirm-tip p {
  margin: 8px 0;
  color: #6b7280;
}

.highlight {
  color: #fda085;
  font-weight: 700;
}

.dialog-footer {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
}

@media (max-width: 768px) {
  .banner-content {
    flex-direction: column;
    text-align: center;
  }
  
  .goods-grid {
    grid-template-columns: repeat(2, 1fr);
    gap: 15px;
  }
  
  .goods-image {
    height: 150px;
  }
}
.confirm-goods{display:grid;grid-template-columns:minmax(0,1fr);gap:16px;padding-bottom:20px}.confirm-image{display:block;width:100%;height:220px;object-fit:contain;border-radius:16px;background:linear-gradient(135deg,#f9f5ff,#f0ecf7);margin:0}.confirm-name{font-size:19px;color:#67527e}.confirm-tip{border-radius:12px;background:#f7f3fb;padding:14px 18px}.exchange-records-target .record-item:first-child{animation:receipt-record-in 480ms ease both}@keyframes receipt-record-in{from{opacity:.4;transform:translateY(12px)}to{opacity:1;transform:translateY(0)}}
</style>
