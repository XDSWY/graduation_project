<template>
  <div class="history-container">
    <nav class="navbar">
      <div class="nav-brand">🏥 眼底病筛查系统 - 历史记录</div>
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
      <h1 class="page-title">📋 诊断历史</h1>

      <el-table :data="records" style="width: 100%" stripe v-loading="loading">
        <el-table-column label="图片" width="100">
          <template #default="{ row }">
            <el-image
              :src="row.image_url"
              class="table-image"
              :preview-src-list="[row.image_url]"
            />
          </template>
        </el-table-column>
        <el-table-column prop="result" label="诊断结果" width="150">
          <template #default="{ row }">
            <span :class="row.result === '正常' ? 'result-normal' : 'result-abnormal'">
              {{ row.result }}
            </span>
          </template>
        </el-table-column>
        <el-table-column prop="confidence" label="置信度" width="120">
          <template #default="{ row }">
            {{ (row.confidence * 100).toFixed(1) }}%
          </template>
        </el-table-column>
        <el-table-column prop="created_at" label="诊断时间" width="180">
          <template #default="{ row }">
            {{ formatDate(row.created_at) }}
          </template>
        </el-table-column>
        <el-table-column label="操作" width="200">
          <template #default="{ row }">
            <el-button type="primary" size="small" @click="viewDetail(row)">
              查看详情
            </el-button>
            <el-button
              type="warning"
              size="small"
              @click="toggleFavorite(row)"
              :loading="row.favoriteLoading"
            >
              {{ row.is_favorite ? '取消收藏' : '收藏' }}
            </el-button>
          </template>
        </el-table-column>
      </el-table>
    </div>
  </div>
</template>

<script>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import api from '../api'

export default {
  name: 'History',
  setup() {
    const router = useRouter()
    const username = ref(localStorage.getItem('username') || '')
    const isAdmin = ref(localStorage.getItem('isAdmin') === 'true')
    const records = ref([])
    const loading = ref(false)

    const fetchRecords = async () => {
      loading.value = true
      try {
        const response = await api.get('/records/')
        if (response.data.success) {
          records.value = response.data.records.map(r => ({
            ...r,
            favoriteLoading: false
          }))
        }
      } catch (error) {
        console.error('获取记录失败:', error)
        ElMessage.error('获取记录失败')
      } finally {
        loading.value = false
      }
    }

    const viewDetail = (record) => {
      router.push(`/result/${record.id}`)
    }

    const toggleFavorite = async (record) => {
      record.favoriteLoading = true
      try {
        const response = await api.post(`/records/${record.id}/toggle-favorite/`)
        if (response.data.success) {
          record.is_favorite = response.data.is_favorite
          ElMessage.success(response.data.message)
        }
      } catch (error) {
        console.error('操作失败:', error)
        ElMessage.error('操作失败')
      } finally {
        record.favoriteLoading = false
      }
    }

    const formatDate = (dateString) => {
      const date = new Date(dateString)
      return `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, '0')}-${String(date.getDate()).padStart(2, '0')} ${String(date.getHours()).padStart(2, '0')}:${String(date.getMinutes()).padStart(2, '0')}`
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
      fetchRecords()
    })

    return {
      username,
      isAdmin,
      records,
      loading,
      viewDetail,
      toggleFavorite,
      formatDate,
      goBack,
      goToManageUsers,
      handleLogout
    }
  }
}
</script>

<style scoped>
.history-container {
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

.table-image {
  width: 60px;
  height: 60px;
  border-radius: 10px;
  object-fit: cover;
  cursor: pointer;
}

.result-normal {
  color: #4ecdc4;
  font-weight: bold;
}

.result-abnormal {
  color: #ff6b6b;
  font-weight: bold;
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

.el-button--warning {
  background: rgba(230, 162, 60, 0.3);
  border: 1px solid rgba(230, 162, 60, 0.5);
  color: white;
}

.el-button--danger {
  background: rgba(245, 108, 108, 0.3);
  border: 1px solid rgba(245, 108, 108, 0.5);
  color: white;
}

.el-button--info {
  background: rgba(144, 147, 153, 0.3);
  border: 1px solid rgba(144, 147, 153, 0.5);
  color: white;
}

.el-button:hover {
  transform: translateY(-2px);
  box-shadow: 0 5px 15px rgba(0, 0, 0, 0.3);
}
</style>