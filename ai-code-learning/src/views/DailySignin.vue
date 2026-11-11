<template>
  <div class="signin-page">
    <div class="hero-banner">
      <div class="banner-content">
        <div class="banner-left">
          <h1 class="banner-title">📅 每日签到</h1>
          <p class="banner-subtitle">坚持每天签到，领取丰厚积分！连续签到奖励更多！</p>
          <div class="banner-stats">
            <div class="stat-item">
              <span class="stat-number">{{ currentPoints }}</span>
              <span class="stat-label">当前积分</span>
            </div>
            <div class="stat-item">
              <span class="stat-number">{{ consecutiveDays }}</span>
              <span class="stat-label">连续签到</span>
            </div>
          </div>
        </div>
        <div class="banner-right">
          <div v-if="!signed" class="signin-btn-wrapper">
            <el-button 
              type="primary" 
              size="large" 
              :loading="signing"
              @click="handleSignin"
              class="signin-btn"
            >
              立即签到
            </el-button>
          </div>
          <div v-else class="signed-badge">
            <div class="check-icon">✓</div>
            <div class="signed-text">今日已签到</div>
          </div>
        </div>
      </div>
    </div>

    <div class="container">
      <div class="weekly-progress">
        <h3 class="section-title">本周签到</h3>
        <div class="days-grid">
          <div 
            v-for="(day, idx) in weekDays" 
            :key="idx"
            class="day-item"
            :class="{ 
              'today': day.isToday, 
              'signed': day.signed 
            }"
          >
            <div class="day-label">{{ day.label }}</div>
            <div v-if="day.signed" class="day-check">✓</div>
            <div v-else-if="day.isToday" class="day-today">今</div>
            <div v-else class="day-empty"></div>
          </div>
        </div>
      </div>

      <div class="rules-section">
        <h3 class="section-title">签到规则</h3>
        <div class="rules-grid">
          <div class="rule-item">
            <div class="rule-icon">1️⃣</div>
            <div class="rule-text">
              <div class="rule-title">每日基础</div>
              <div class="rule-desc">每天签到奖励 10 积分</div>
            </div>
          </div>
          <div class="rule-item">
            <div class="rule-icon">2️⃣</div>
            <div class="rule-text">
              <div class="rule-title">连续奖励</div>
              <div class="rule-desc">连续签到每天递增 5 积分</div>
            </div>
          </div>
          <div class="rule-item">
            <div class="rule-icon">3️⃣</div>
            <div class="rule-text">
              <div class="rule-title">最高奖励</div>
              <div class="rule-desc">连续 7 天，最高奖励 40 积分</div>
            </div>
          </div>
          <div class="rule-item">
            <div class="rule-icon">4️⃣</div>
            <div class="rule-text">
              <div class="rule-title">补签规则</div>
              <div class="rule-desc">中断后连续天数重新计算</div>
            </div>
          </div>
        </div>
      </div>

      <div class="quick-links">
        <h3 class="section-title">快速导航</h3>
        <div class="links-grid">
          <router-link to="/daily-checkin" class="link-item">
            <div class="link-icon">📝</div>
            <div class="link-text">每日打卡</div>
          </router-link>
          <router-link to="/points-mall" class="link-item">
            <div class="link-icon">🛒</div>
            <div class="link-text">积分商城</div>
          </router-link>
          <router-link to="/competition" class="link-item">
            <div class="link-icon">🏆</div>
            <div class="link-text">测试中心</div>
          </router-link>
        </div>
      </div>
    </div>
    <TopicArt scene="calendar" />
  </div>
</template>

<script setup>
import TopicArt from '@/components/TopicArt.vue'
import { ref, computed, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import axios from 'axios'
import { getCurrentUser } from '@/utils/authStorage'

const user = getCurrentUser()
const signed = ref(false)
const signing = ref(false)
const consecutiveDays = ref(0)
const currentPoints = ref(0)

const weekDays = computed(() => {
  const days = []
  const labels = ['周一', '周二', '周三', '周四', '周五', '周六', '周日']
  const today = new Date()
  const startOfWeek = new Date(today)
  startOfWeek.setDate(today.getDate() - (today.getDay() || 7) + 1)

  for (let i = 0; i < 7; i++) {
    const day = new Date(startOfWeek)
    day.setDate(startOfWeek.getDate() + i)
    const isToday = day.toDateString() === today.toDateString()
    days.push({
      label: labels[i],
      isToday,
      signed: false
    })
  }
  return days
})

const loadStatus = async () => {
  if (!user?.id) return
  try {
    const res = await axios.get('/api/daily-signin/status', {
      params: { user_id: user.id }
    })
    if (res.data && res.data.success) {
      signed.value = res.data.signed
      consecutiveDays.value = res.data.consecutiveDays
    }
  } catch (err) {
    console.log('加载签到状态失败:', err)
  }
}

const loadPoints = async () => {
  if (!user?.id) return
  try {
    const res = await axios.get('/api/points', {
      params: { user_id: user.id }
    })
    if (res.data && res.data.success) {
      currentPoints.value = res.data.points
    }
  } catch (err) {
    console.log('加载积分失败:', err)
  }
}

const handleSignin = async () => {
  if (!user?.id) {
    ElMessage.warning('请先登录')
    return
  }
  signing.value = true
  try {
    const res = await axios.post('/api/daily-signin', null, {
      params: { user_id: user.id, user_name: user.name || user.username }
    })
    if (res.data && res.data.success) {
      signed.value = true
      consecutiveDays.value = res.data.consecutiveDays
      ElMessage.success(`签到成功！获得 ${res.data.points} 积分，连续 ${res.data.consecutiveDays} 天！`)
      await loadPoints()
    } else {
      if (res.data?.alreadySigned) {
        signed.value = true
        ElMessage.warning(res.data?.message || '今天已经签到过了')
      } else {
        ElMessage.error(res.data?.message || '签到失败')
      }
    }
  } catch (err) {
    console.error('签到失败:', err)
    ElMessage.error(err?.response?.data?.message || '签到失败，请稍后重试')
  } finally {
    signing.value = false
  }
}

onMounted(async () => {
  await Promise.all([loadStatus(), loadPoints()])
})
</script>

<style scoped>
.signin-page {
  min-height: 100vh;
  background: #f5f7fa;
}

.hero-banner {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  padding: 60px 0;
  color: white;
}

.banner-content {
  max-width: 1200px;
  margin: 0 auto;
  padding: 0 24px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 40px;
}

.banner-title {
  font-size: 42px;
  font-weight: 800;
  margin: 0 0 16px;
}

.banner-subtitle {
  font-size: 18px;
  opacity: 0.95;
  margin: 0 0 28px;
}

.banner-stats {
  display: flex;
  gap: 32px;
}

.stat-item {
  display: flex;
  flex-direction: column;
}

.stat-number {
  font-size: 36px;
  font-weight: 800;
}

.stat-label {
  font-size: 14px;
  opacity: 0.85;
}

.signin-btn-wrapper {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 16px;
}

.signin-btn {
  padding: 16px 48px;
  font-size: 18px;
  font-weight: 700;
  border-radius: 50px;
  background: linear-gradient(135deg, #f6d365 0%, #fda085 100%);
  border: none;
  color: #1f2937;
  box-shadow: 0 8px 20px rgba(246, 211, 101, 0.4);
}

.signin-btn:hover {
  transform: translateY(-2px);
  box-shadow: 0 12px 28px rgba(246, 211, 101, 0.5);
}

.signed-badge {
  background: rgba(255, 255, 255, 0.15);
  padding: 20px 40px;
  border-radius: 50px;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
  backdrop-filter: blur(10px);
}

.check-icon {
  font-size: 48px;
  font-weight: 800;
}

.signed-text {
  font-size: 16px;
  font-weight: 600;
}

.container {
  max-width: 1200px;
  margin: 0 auto;
  padding: 40px 24px;
}

.section-title {
  font-size: 22px;
  font-weight: 700;
  color: #1f2937;
  margin: 0 0 20px;
}

.weekly-progress {
  background: white;
  border-radius: 20px;
  padding: 30px;
  margin-bottom: 24px;
  box-shadow: 0 4px 12px rgba(0,0,0,0.06);
}

.days-grid {
  display: grid;
  grid-template-columns: repeat(7, 1fr);
  gap: 12px;
}

.day-item {
  background: #f8fafc;
  border-radius: 12px;
  padding: 16px 8px;
  text-align: center;
  transition: all 0.3s;
}

.day-item.today {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
}

.day-item.signed {
  background: linear-gradient(135deg, #67c23a 0%, #85ce61 100%);
  color: white;
}

.day-label {
  font-size: 13px;
  font-weight: 600;
  margin-bottom: 10px;
}

.day-check, .day-today {
  font-size: 24px;
  font-weight: 800;
}

.rules-section {
  background: white;
  border-radius: 20px;
  padding: 30px;
  margin-bottom: 24px;
  box-shadow: 0 4px 12px rgba(0,0,0,0.06);
}

.rules-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 20px;
}

.rule-item {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 16px;
  background: #f8fafc;
  border-radius: 12px;
}

.rule-icon {
  font-size: 36px;
}

.rule-text {
  flex: 1;
}

.rule-title {
  font-size: 16px;
  font-weight: 700;
  color: #1f2937;
  margin-bottom: 4px;
}

.rule-desc {
  font-size: 14px;
  color: #6b7280;
}

.quick-links {
  background: white;
  border-radius: 20px;
  padding: 30px;
  box-shadow: 0 4px 12px rgba(0,0,0,0.06);
}

.links-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 20px;
}

.link-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 12px;
  padding: 24px 16px;
  background: linear-gradient(135deg, #f5f7fa 0%, #e8ecf1 100%);
  border-radius: 16px;
  text-decoration: none;
  color: #1f2937;
  transition: all 0.3s;
}

.link-item:hover {
  transform: translateY(-4px);
  box-shadow: 0 8px 20px rgba(0,0,0,0.1);
}

.link-icon {
  font-size: 40px;
}

.link-text {
  font-size: 16px;
  font-weight: 600;
}

@media (max-width: 768px) {
  .banner-content {
    flex-direction: column;
    text-align: center;
  }

  .banner-stats {
    justify-content: center;
  }

  .days-grid {
    grid-template-columns: repeat(7, minmax(40px, 1fr));
  }

  .rules-grid {
    grid-template-columns: 1fr;
  }

  .links-grid {
    grid-template-columns: 1fr;
  }
}
</style>