<template>
  <div class="manage-container">
    <nav class="navbar">
      <div class="nav-brand">🏥 眼底病筛查系统 - 管理员</div>
      <div class="nav-user">
        <span>👤 {{ username }}</span>
        <el-button type="primary" size="small" @click="goBack">返回主页</el-button>
        <el-button type="danger" size="small" @click="handleLogout">退出</el-button>
      </div>
    </nav>

    <div class="content">
      <h1>👥 用户管理</h1>
      <p class="subtitle">管理系统中的所有用户</p>

      <!-- 统计卡片 -->
      <div class="stats-grid">
        <div class="stat-card">
          <div class="stat-number">{{ totalUsers }}</div>
          <div class="stat-label">总用户数</div>
        </div>
        <div class="stat-card">
          <div class="stat-number">{{ normalUsers }}</div>
          <div class="stat-label">普通用户</div>
        </div>
        <div class="stat-card">
          <div class="stat-number">1</div>
          <div class="stat-label">管理员</div>
        </div>
      </div>

      <!-- 搜索框 -->
      <el-input
        v-model="searchQuery"
        placeholder="搜索用户名..."
        prefix-icon="Search"
        clearable
        class="search-input"
        @input="filterUsers"
      />

      <!-- 用户列表 -->
      <el-table :data="filteredUsers" style="width: 100%" stripe>
        <el-table-column prop="id" label="ID" width="80" />
        <el-table-column prop="username" label="用户名" />
        <el-table-column label="角色" width="120">
          <template #default="scope">
            <el-tag v-if="scope.row.is_admin" type="danger">管理员</el-tag>
            <el-tag v-else type="info">普通用户</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="date_joined" label="注册时间" width="180" />
        <el-table-column prop="last_login" label="最后登录" width="180">
          <template #default="scope">
            {{ scope.row.last_login || '从未登录' }}
          </template>
        </el-table-column>
        <el-table-column label="操作" width="150" fixed="right">
          <template #default="scope">
            <el-button
              v-if="!scope.row.is_admin"
              type="danger"
              size="small"
              @click="confirmDelete(scope.row)"
            >
              删除
            </el-button>
            <el-tag v-else type="danger" size="small">不可删除</el-tag>
          </template>
        </el-table-column>
      </el-table>

      <!-- 加载状态 -->
      <div v-if="loading" class="loading">
        <el-skeleton :rows="5" animated />
      </div>
    </div>

    <!-- 删除确认对话框 -->
    <el-dialog
      v-model="dialogVisible"
      title="确认删除"
      width="30%"
    >
      <div class="delete-warning">
        <el-icon :size="50" color="#f56c6c"><Warning /></el-icon>
        <p>确定要删除用户 <strong>{{ selectedUser?.username }}</strong> 吗？</p>
        <p class="warning-text">此操作不可撤销！</p>
      </div>
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="dialogVisible = false">取消</el-button>
          <el-button type="danger" @click="handleDelete" :loading="deleteLoading">
            确认删除
          </el-button>
        </span>
      </template>
    </el-dialog>
  </div>
</template>

<script>
import { ref, onMounted, computed } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Warning } from '@element-plus/icons-vue'
import api from '../api'

export default {
  name: 'ManageUsers',
  components: {
    Warning
  },
  setup() {
    const router = useRouter()
    const username = ref(localStorage.getItem('username') || '')
    const users = ref([])
    const filteredUsers = ref([])
    const searchQuery = ref('')
    const loading = ref(true)
    const dialogVisible = ref(false)
    const deleteLoading = ref(false)
    const selectedUser = ref(null)

    // 计算统计
    const totalUsers = computed(() => users.value.length)
    const normalUsers = computed(() => users.value.filter(u => !u.is_admin).length)

    // 获取用户列表
    const fetchUsers = async () => {
      try {
        loading.value = true
        const response = await api.get('/users/')
        if (response.data.success) {
          users.value = response.data.users
          filteredUsers.value = response.data.users
        }
      } catch (error) {
        console.error('获取用户列表失败:', error)
        ElMessage.error('获取用户列表失败')
      } finally {
        loading.value = false
      }
    }

    // 搜索过滤
    const filterUsers = () => {
      if (!searchQuery.value) {
        filteredUsers.value = users.value
        return
      }
      filteredUsers.value = users.value.filter(user =>
        user.username.toLowerCase().includes(searchQuery.value.toLowerCase())
      )
    }

    // 确认删除
    const confirmDelete = (user) => {
      selectedUser.value = user
      dialogVisible.value = true
    }

    // 执行删除
    const handleDelete = async () => {
      if (!selectedUser.value) return

      deleteLoading.value = true
      try {
        const response = await api.delete(`/users/${selectedUser.value.id}/`)
        if (response.data.success) {
          ElMessage.success(response.data.message)
          // 刷新列表
          await fetchUsers()
          dialogVisible.value = false
        }
      } catch (error) {
        console.error('删除用户失败:', error)
        ElMessage.error(error.response?.data?.message || '删除失败')
      } finally {
        deleteLoading.value = false
        selectedUser.value = null
      }
    }

    const goBack = () => {
      router.push('/home')
    }

    const handleLogout = () => {
      localStorage.removeItem('token')
      localStorage.removeItem('username')
      localStorage.removeItem('isAdmin')
      ElMessage.success('已退出登录')
      router.push('/login')
    }

    onMounted(() => {
      // 检查是否是管理员
      if (localStorage.getItem('isAdmin') !== 'true') {
        ElMessage.error('无权限访问')
        router.push('/home')
        return
      }
      fetchUsers()
    })

    return {
      username,
      users,
      filteredUsers,
      searchQuery,
      loading,
      dialogVisible,
      deleteLoading,
      selectedUser,
      totalUsers,
      normalUsers,
      filterUsers,
      confirmDelete,
      handleDelete,
      goBack,
      handleLogout
    }
  }
}
</script>

<style scoped>
.manage-container {
  min-height: 100vh;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
}

.navbar {
  background: rgba(255, 255, 255, 0.1);
  backdrop-filter: blur(10px);
  padding: 1rem 2rem;
  display: flex;
  justify-content: space-between;
  align-items: center;
  color: white;
  border-bottom: 1px solid rgba(255, 255, 255, 0.2);
}

.nav-brand {
  font-size: 1.5rem;
  font-weight: bold;
}

.nav-user {
  display: flex;
  align-items: center;
  gap: 1rem;
}

.nav-user span {
  font-size: 1.1rem;
}

.content {
  max-width: 1200px;
  margin: 0 auto;
  padding: 2rem;
  color: white;
}

.content h1 {
  font-size: 2.5rem;
  margin-bottom: 0.5rem;
  text-align: center;
}

.subtitle {
  text-align: center;
  opacity: 0.9;
  margin-bottom: 2rem;
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 2rem;
  margin-bottom: 2rem;
}

.stat-card {
  background: rgba(255, 255, 255, 0.2);
  backdrop-filter: blur(10px);
  border: 1px solid rgba(255, 255, 255, 0.3);
  border-radius: 15px;
  padding: 1.5rem;
  text-align: center;
}

.stat-number {
  font-size: 2.5rem;
  font-weight: bold;
  color: #ffd700;
}

.stat-label {
  margin-top: 0.5rem;
  font-size: 1rem;
  opacity: 0.9;
}

.search-input {
  margin-bottom: 2rem;
  background: rgba(255, 255, 255, 0.2);
  border: 1px solid rgba(255, 255, 255, 0.3);
}

:deep(.el-input__wrapper) {
  background: rgba(255, 255, 255, 0.2);
  box-shadow: none;
}

:deep(.el-input__inner) {
  color: white;
}

:deep(.el-input__inner::placeholder) {
  color: rgba(255, 255, 255, 0.6);
}

:deep(.el-table) {
  background: rgba(255, 255, 255, 0.1);
  backdrop-filter: blur(10px);
  color: white;
  border-radius: 15px;
  overflow: hidden;
}

:deep(.el-table th) {
  background: rgba(0, 0, 0, 0.3);
  color: white;
  border-bottom: none;
}

:deep(.el-table td) {
  border-bottom: 1px solid rgba(255, 255, 255, 0.1);
}

:deep(.el-table tr) {
  background: transparent;
}

:deep(.el-table--striped .el-table__body tr.el-table__row--striped td) {
  background: rgba(255, 255, 255, 0.05);
}

.loading {
  margin-top: 2rem;
}

.delete-warning {
  text-align: center;
  padding: 1rem;
}

.warning-text {
  color: #f56c6c;
  font-weight: bold;
  margin-top: 0.5rem;
}
</style>