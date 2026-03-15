<template>
  <div class="statistics-container">
    <nav class="navbar">
      <div class="nav-brand">🏥 眼底病筛查系统 - 数据统计</div>
      <div class="nav-user">
        <span class="greeting-small">你好，{{ username }}！</span>
        <div v-if="isAdmin" class="admin-card-btn" @click="goToManageUsers">
          <span class="admin-icon">👥</span>
          <span class="admin-text">管理用户</span>
        </div>
        <el-button type="primary" size="small" @click="goBack">返回主页</el-button>
        <el-button type="danger" size="small" @click="handleLogout">退出</el-button>
      </div>
    </nav>

    <div class="content">
      <h1 class="page-title">📊 数据统计</h1>

      <!-- 加载状态 -->
      <div v-if="loading" class="loading">
        <el-skeleton :rows="5" animated />
      </div>

      <div v-else>
        <!-- 个人统计卡片 -->
        <div class="stats-section">
          <h2>个人统计</h2>
          <div class="stats-grid">
            <div class="stat-card">
              <div class="stat-icon">📋</div>
              <div class="stat-number">{{ userStats.total_diagnoses || 0 }}</div>
              <div class="stat-label">我的诊断次数</div>
            </div>
            <div class="stat-card">
              <div class="stat-icon">⭐</div>
              <div class="stat-number">{{ userStats.favorites || 0 }}</div>
              <div class="stat-label">我的收藏</div>
            </div>
          </div>
        </div>

        <!-- 管理员全局统计 -->
        <div v-if="isAdmin && adminStats" class="stats-section">
          <h2>系统全局统计</h2>
          <div class="stats-grid">
            <div class="stat-card admin">
              <div class="stat-icon">📊</div>
              <div class="stat-number">{{ adminStats.total_diagnoses }}</div>
              <div class="stat-label">总诊断次数</div>
            </div>
            <div class="stat-card admin">
              <div class="stat-icon">📅</div>
              <div class="stat-number">{{ adminStats.today_diagnoses }}</div>
              <div class="stat-label">今日诊断</div>
            </div>
            <div class="stat-card admin">
              <div class="stat-icon">📆</div>
              <div class="stat-number">{{ adminStats.week_diagnoses }}</div>
              <div class="stat-label">本周诊断</div>
            </div>
            <div class="stat-card admin">
              <div class="stat-icon">📈</div>
              <div class="stat-number">{{ adminStats.month_diagnoses }}</div>
              <div class="stat-label">本月诊断</div>
            </div>
            <div class="stat-card admin">
              <div class="stat-icon">👥</div>
              <div class="stat-number">{{ adminStats.total_users }}</div>
              <div class="stat-label">总用户数</div>
            </div>
          </div>

          <!-- 疾病分布图表 -->
          <div class="chart-container">
            <h3>疾病分布</h3>
            <div ref="diseaseChart" class="chart"></div>
          </div>

          <!-- 每日诊断趋势 -->
          <div class="chart-container">
            <h3>每日诊断趋势</h3>
            <div ref="trendChart" class="chart"></div>
          </div>

          <!-- 用户排名 -->
          <div class="rank-container">
            <h3>用户诊断排名</h3>
            <el-table :data="adminStats.user_rank" style="width: 100%">
              <el-table-column prop="username" label="用户名">
                <template #default="{ row }">
                  <span :class="{ 'admin-user': row.is_admin }">{{ row.username }}</span>
                </template>
              </el-table-column>
              <el-table-column prop="diagnoses" label="诊断次数" />
            </el-table>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, onMounted, nextTick } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import * as echarts from 'echarts'
import api from '../api'

export default {
  name: 'Statistics',
  setup() {
    const router = useRouter()
    const username = ref(localStorage.getItem('username') || '')
    const isAdmin = ref(localStorage.getItem('isAdmin') === 'true')
    const loading = ref(true)
    const userStats = ref({})
    const adminStats = ref(null)
    const diseaseChart = ref(null)
    const trendChart = ref(null)

    const fetchStatistics = async () => {
      try {
        loading.value = true
        const response = await api.get('/statistics/')
        if (response.data.success) {
          userStats.value = response.data.statistics.user
          adminStats.value = response.data.statistics.admin || null

          // 等待DOM更新后初始化图表
          await nextTick()
          initCharts()
        }
      } catch (error) {
        console.error('获取统计失败:', error)
        ElMessage.error('获取统计失败')
      } finally {
        loading.value = false
      }
    }

    const initCharts = () => {
      if (!isAdmin.value || !adminStats.value) return

      // 疾病分布饼图
      if (diseaseChart.value && adminStats.value.disease_distribution) {
        const chart = echarts.init(diseaseChart.value)
        const data = adminStats.value.disease_distribution

        chart.setOption({
          tooltip: { trigger: 'item' },
          legend: { orient: 'vertical', left: 'left', textStyle: { color: '#fff' } },
          series: [{
            name: '疾病分布',
            type: 'pie',
            radius: '50%',
            data: data.map(item => ({ name: item.name, value: item.count })),
            emphasis: {
              itemStyle: {
                shadowBlur: 10,
                shadowOffsetX: 0,
                shadowColor: 'rgba(0, 0, 0, 0.5)'
              }
            }
          }],
          backgroundColor: 'transparent'
        })

        // 窗口大小变化时自适应
        window.addEventListener('resize', () => chart.resize())
      }

      // 每日趋势折线图
      if (trendChart.value && adminStats.value.daily_trend) {
        const chart = echarts.init(trendChart.value)
        const trend = adminStats.value.daily_trend

        chart.setOption({
          tooltip: { trigger: 'axis' },
          xAxis: {
            type: 'category',
            data: trend.map(item => item.date),
            axisLabel: { color: '#fff' }
          },
          yAxis: {
            type: 'value',
            axisLabel: { color: '#fff' }
          },
          series: [{
            name: '诊断次数',
            type: 'line',
            data: trend.map(item => item.count),
            smooth: true,
            lineStyle: { color: '#4ecdc4', width: 3 },
            areaStyle: { color: 'rgba(78, 205, 196, 0.3)' }
          }],
          backgroundColor: 'transparent',
          grid: { containLabel: true }
        })

        window.addEventListener('resize', () => chart.resize())
      }
    }

    const goBack = () => {
      router.push('/home')
    }

    const goToManageUsers = () => {
      router.push('/manage-users')
    }

    const handleLogout = () => {
      localStorage.removeItem('token')
      localStorage.removeItem('username')
      localStorage.removeItem('isAdmin')
      ElMessage.success('已退出登录')
      router.push('/login')
    }

    onMounted(() => {
      fetchStatistics()
    })

    return {
      username,
      isAdmin,
      loading,
      userStats,
      adminStats,
      diseaseChart,
      trendChart,
      goBack,
      goToManageUsers,
      handleLogout
    }
  }
}
</script>

<style scoped>
.statistics-container {
  min-height: 100vh;
  background: linear-gradient(-45deg, #ee7752, #e73c7e, #23a6d5, #23d5ab);
  background-size: 400% 400%;
  animation: gradient 15s ease infinite;
}

@keyframes gradient {
  0% { background-position: 0% 50%; }
  50% { background-position: 100% 50%; }
  100% { background-position: 0% 50%; }
}

.navbar {
  background: rgba(255, 255, 255, 0.15);
  backdrop-filter: blur(10px);
  border-bottom: 1px solid rgba(255, 255, 255, 0.2);
  padding: 1rem 2rem;
  display: flex;
  justify-content: space-between;
  align-items: center;
  color: white;
}

.nav-brand {
  font-size: 1.5rem;
  font-weight: bold;
  text-shadow: 2px 2px 4px rgba(0, 0, 0, 0.2);
}

.nav-user {
  display: flex;
  align-items: center;
  gap: 1rem;
}

.greeting-small {
  font-size: 1rem;
  opacity: 0.9;
}

.admin-card-btn {
  background: rgba(255, 255, 255, 0.2);
  backdrop-filter: blur(15px);
  border: 1px solid rgba(255, 255, 255, 0.3);
  border-radius: 20px;
  padding: 0.5rem 1.2rem;
  display: flex;
  align-items: center;
  gap: 0.5rem;
  cursor: pointer;
  transition: all 0.3s;
  color: white;
}

.admin-card-btn:hover {
  transform: translateY(-2px);
  background: rgba(255, 215, 0, 0.2);
  border-color: #ffd700;
}

.content {
  max-width: 1200px;
  margin: 0 auto;
  padding: 2rem;
  color: white;
}

.page-title {
  text-align: center;
  font-size: 2.5rem;
  margin-bottom: 2rem;
  text-shadow: 2px 2px 4px rgba(0, 0, 0, 0.2);
}

.stats-section {
  margin-bottom: 3rem;
  padding: 2rem;
  background: rgba(255, 255, 255, 0.1);
  backdrop-filter: blur(10px);
  border-radius: 30px;
}

.stats-section h2 {
  margin-bottom: 1.5rem;
  font-size: 1.8rem;
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 1.5rem;
  margin-bottom: 2rem;
}

.stat-card {
  background: rgba(255, 255, 255, 0.2);
  backdrop-filter: blur(15px);
  border: 1px solid rgba(255, 255, 255, 0.3);
  border-radius: 20px;
  padding: 1.5rem;
  text-align: center;
  transition: transform 0.3s;
}

.stat-card:hover {
  transform: translateY(-5px);
}

.stat-card.admin {
  background: rgba(255, 215, 0, 0.2);
  border-color: #ffd700;
}

.stat-icon {
  font-size: 2.5rem;
  margin-bottom: 0.5rem;
}

.stat-number {
  font-size: 2rem;
  font-weight: bold;
  color: #ffd700;
  margin-bottom: 0.5rem;
}

.stat-label {
  opacity: 0.9;
  font-size: 0.9rem;
}

.chart-container {
  margin: 2rem 0;
  padding: 1rem;
  background: rgba(255, 255, 255, 0.1);
  border-radius: 20px;
}

.chart-container h3 {
  margin-bottom: 1rem;
  font-size: 1.2rem;
  color: white;
}

.chart {
  width: 100%;
  height: 300px;
}

.rank-container {
  margin-top: 2rem;
}

.rank-container h3 {
  margin-bottom: 1rem;
  font-size: 1.2rem;
}

.admin-user {
  color: #ffd700;
  font-weight: bold;
}

.loading {
  padding: 2rem;
  background: rgba(255, 255, 255, 0.1);
  border-radius: 20px;
}

.el-table {
  background: transparent;
  color: white;
}

:deep(.el-table th) {
  background: rgba(0, 0, 0, 0.2);
  color: white;
  border-bottom: none;
}

:deep(.el-table td) {
  border-bottom: 1px solid rgba(255, 255, 255, 0.1);
}

:deep(.el-table tr) {
  background: transparent;
}

.el-button {
  border-radius: 20px;
}

.el-button--primary {
  background: rgba(64, 158, 255, 0.3);
  border: 1px solid rgba(64, 158, 255, 0.5);
  color: white;
}

.el-button--danger {
  background: rgba(245, 108, 108, 0.3);
  border: 1px solid rgba(245, 108, 108, 0.5);
  color: white;
}

.el-button:hover {
  transform: translateY(-2px);
  box-shadow: 0 5px 15px rgba(0, 0, 0, 0.3);
}
</style>