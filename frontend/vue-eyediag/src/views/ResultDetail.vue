<template>
  <div class="detail-container">
    <nav class="navbar">
      <div class="nav-brand">🏥 眼底病筛查系统 - 诊断详情</div>
      <div class="nav-user">
        <span class="greeting-small">你好，{{ username }}！</span>
        <div v-if="isAdmin" class="admin-card-btn" @click="goToManageUsers">
          <span class="admin-icon">👥</span>
          <span class="admin-text">管理用户</span>
        </div>
        <el-button type="primary" size="small" @click="goBack">返回</el-button>
        <el-button type="danger" size="small" @click="handleLogout">退出</el-button>
      </div>
    </nav>

    <div class="content">
      <div v-if="loading" class="loading">
        <el-skeleton :rows="5" animated />
      </div>

      <div v-else-if="record" class="detail-card">
        <h1 class="page-title">诊断结果详情</h1>

        <div class="info-grid">
          <div class="info-item">
            <span class="info-label">文件名称：</span>
            <span class="info-value">{{ record.image_name || '未知' }}</span>
          </div>
          <div class="info-item">
            <span class="info-label">诊断结论：</span>
            <span class="info-diagnosis" :class="resultClass">{{ record.result }}</span>
          </div>
          <div class="info-item">
            <span class="info-label">置信度：</span>
            <span class="info-value">{{ (record.confidence * 100).toFixed(1) }}%</span>
          </div>
          <div class="info-item">
            <span class="info-label">诊断时间：</span>
            <span class="info-value">{{ formatDate(record.created_at) }}</span>
          </div>
        </div>

        <!-- 原始图片 -->
        <div class="image-section">
          <h2>原始图片</h2>
          <el-image
            :src="record.image_url"
            class="detail-image"
            :preview-src-list="[record.image_url]"
            fit="contain"
          />
        </div>

        <!-- 热力图生成按钮 -->
        <div class="heatmap-section">
          <h2>决策可视化</h2>
          <div class="heatmap-buttons">
            <el-button
              type="primary"
              size="small"
              @click="generateHeatmap('gradcam')"
              :loading="generating.gradcam"
            >
              Grad-CAM
            </el-button>
            <el-button
              type="success"
              size="small"
              @click="generateHeatmap('layercam')"
              :loading="generating.layercam"
            >
              LayerCAM
            </el-button>
            <el-button
              type="warning"
              size="small"
              @click="generateHeatmap('both')"
              :loading="generating.both"
            >
              全部
            </el-button>
          </div>

          <!-- 热力图显示 -->
          <div v-if="heatmaps.gradcam || heatmaps.layercam" class="heatmap-grid">
            <div v-if="heatmaps.gradcam" class="heatmap-item">
              <h3>Grad-CAM</h3>
              <el-image
                :src="heatmaps.gradcam"
                class="heatmap-image"
                :preview-src-list="[heatmaps.gradcam, heatmaps.layercam].filter(Boolean)"
                fit="contain"
              >
                <template #error>
                  <div class="image-error">
                    <el-icon><Picture /></el-icon>
                    <span>加载失败</span>
                  </div>
                </template>
              </el-image>
            </div>
            <div v-if="heatmaps.layercam" class="heatmap-item">
              <h3>LayerCAM</h3>
              <el-image
                :src="heatmaps.layercam"
                class="heatmap-image"
                :preview-src-list="[heatmaps.gradcam, heatmaps.layercam].filter(Boolean)"
                fit="contain"
              >
                <template #error>
                  <div class="image-error">
                    <el-icon><Picture /></el-icon>
                    <span>加载失败</span>
                  </div>
                </template>
              </el-image>
            </div>
          </div>

          <!-- 没有热力图时的提示 -->
          <div v-else class="no-heatmap">
            <el-empty description="点击上方按钮生成热力图" :image-size="60" />
          </div>
        </div>

        <!-- 操作按钮 -->
        <div class="action-buttons">
          <el-button
            type="warning"
            size="small"
            @click="toggleFavorite"
            :loading="favoriteLoading"
          >
            {{ record.is_favorite ? '取消收藏' : '添加收藏' }}
          </el-button>
          <el-button type="primary" size="small" @click="goToUpload">再次上传</el-button>
          <el-button type="danger" size="small" @click="confirmDelete">删除</el-button>
        </div>
      </div>

      <div v-else class="error-message">
        <el-result icon="error" title="记录不存在" sub-title="未找到该诊断记录">
          <template #extra>
            <el-button type="primary" @click="goBack">返回</el-button>
          </template>
        </el-result>
      </div>
    </div>

    <!-- 删除确认对话框 -->
    <el-dialog v-model="deleteDialogVisible" title="确认删除" width="30%">
      <div class="delete-warning">
        <el-icon :size="40" color="#f56c6c"><Warning /></el-icon>
        <p>确定要删除这条记录吗？</p>
        <p class="warning-text">此操作不可撤销！</p>
      </div>
      <template #footer>
        <span class="dialog-footer">
          <el-button size="small" @click="deleteDialogVisible = false">取消</el-button>
          <el-button size="small" type="danger" @click="handleDelete" :loading="deleteLoading">
            确认删除
          </el-button>
        </span>
      </template>
    </el-dialog>
  </div>
</template>

<script>
import { ref, computed, onMounted, nextTick } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { ElMessage } from 'element-plus'
import { Warning, Picture } from '@element-plus/icons-vue'
import api from '../api'

export default {
  name: 'ResultDetail',
  components: { Warning, Picture },
  setup() {
    const router = useRouter()
    const route = useRoute()
    const recordId = route.params.id

    const username = ref(localStorage.getItem('username') || '')
    const isAdmin = ref(localStorage.getItem('isAdmin') === 'true')
    const loading = ref(true)
    const record = ref(null)
    const heatmaps = ref({})
    const generating = ref({
      gradcam: false,
      layercam: false,
      both: false
    })
    const favoriteLoading = ref(false)
    const deleteDialogVisible = ref(false)
    const deleteLoading = ref(false)

    const resultClass = computed(() => {
      if (!record.value) return ''
      return record.value.result === '正常' ? 'result-normal' : 'result-abnormal'
    })

    const fetchRecordDetail = async () => {
      try {
        loading.value = true
        const response = await api.get(`/records/${recordId}/`)
        if (response.data.success) {
          record.value = response.data.record
          if (record.value.image_url) {
            const urlParts = record.value.image_url.split('/')
            record.value.image_name = urlParts[urlParts.length - 1]
          }
        }
      } catch (error) {
        console.error('获取记录失败:', error)
        ElMessage.error('获取记录失败')
      } finally {
        loading.value = false
      }
    }

    const generateHeatmap = async (method) => {
      if (method === 'both') {
        generating.value.both = true
        await Promise.all([
          generateSingleHeatmap('gradcam'),
          generateSingleHeatmap('layercam')
        ])
        generating.value.both = false
      } else {
        await generateSingleHeatmap(method)
      }
    }

    const generateSingleHeatmap = async (method) => {
      generating.value[method] = true
      try {
        const response = await api.post(`/records/${recordId}/heatmap/`, {
          methods: [method]
        })

        if (response.data.success) {
          heatmaps.value[method] = response.data.heatmaps[method]
          await nextTick()
          ElMessage.success(`${method === 'gradcam' ? 'Grad-CAM' : 'LayerCAM'} 生成成功`)
        }
      } catch (error) {
        console.error('生成热力图失败:', error)
        ElMessage.error('生成失败')
      } finally {
        generating.value[method] = false
      }
    }

    const toggleFavorite = async () => {
      if (!record.value) return

      favoriteLoading.value = true
      try {
        const response = await api.post(`/records/${recordId}/toggle-favorite/`)
        if (response.data.success) {
          record.value.is_favorite = response.data.is_favorite
          ElMessage.success(response.data.message)
        }
      } catch (error) {
        console.error('操作失败:', error)
        ElMessage.error('操作失败')
      } finally {
        favoriteLoading.value = false
      }
    }

    const confirmDelete = () => {
      deleteDialogVisible.value = true
    }

    const handleDelete = async () => {
      deleteLoading.value = true
      try {
        const response = await api.delete(`/records/${recordId}/delete/`)
        if (response.data.success) {
          ElMessage.success('删除成功')
          router.push('/history')
        }
      } catch (error) {
        console.error('删除失败:', error)
        ElMessage.error('删除失败')
      } finally {
        deleteLoading.value = false
        deleteDialogVisible.value = false
      }
    }

    const formatDate = (dateString) => {
      const date = new Date(dateString)
      return `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, '0')}-${String(date.getDate()).padStart(2, '0')} ${String(date.getHours()).padStart(2, '0')}:${String(date.getMinutes()).padStart(2, '0')}`
    }

    const goBack = () => {
      router.back()
    }

    const goToUpload = () => {
      router.push('/upload')
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
      fetchRecordDetail()
    })

    return {
      username,
      isAdmin,
      loading,
      record,
      heatmaps,
      generating,
      favoriteLoading,
      deleteDialogVisible,
      deleteLoading,
      resultClass,
      generateHeatmap,
      toggleFavorite,
      confirmDelete,
      handleDelete,
      formatDate,
      goBack,
      goToUpload,
      goToManageUsers,
      handleLogout
    }
  }
}
</script>

<style scoped>
.detail-container {
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
  padding: 0.8rem 2rem;
  display: flex;
  justify-content: space-between;
  align-items: center;
  color: white;
}

.nav-brand {
  font-size: 1.3rem;
  font-weight: bold;
  text-shadow: 2px 2px 4px rgba(0, 0, 0, 0.2);
}

.nav-user {
  display: flex;
  align-items: center;
  gap: 0.8rem;
}

.greeting-small {
  font-size: 0.9rem;
  opacity: 0.9;
}

.admin-card-btn {
  background: rgba(255, 255, 255, 0.2);
  backdrop-filter: blur(15px);
  border: 1px solid rgba(255, 255, 255, 0.3);
  border-radius: 20px;
  padding: 0.4rem 1rem;
  display: flex;
  align-items: center;
  gap: 0.4rem;
  cursor: pointer;
  transition: all 0.3s;
  color: white;
  font-size: 0.9rem;
}

.admin-card-btn:hover {
  transform: translateY(-2px);
  background: rgba(255, 215, 0, 0.2);
  border-color: #ffd700;
}

.content {
  max-width: 900px;
  margin: 0 auto;
  padding: 1.5rem;
  color: white;
}

.page-title {
  text-align: center;
  font-size: 1.8rem;
  margin-bottom: 1.2rem;
  text-shadow: 2px 2px 4px rgba(0, 0, 0, 0.2);
}

.detail-card {
  background: rgba(255, 255, 255, 0.2);
  backdrop-filter: blur(15px);
  border: 1px solid rgba(255, 255, 255, 0.3);
  border-radius: 20px;
  padding: 1.2rem;
}

.info-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 0.6rem;
  margin-bottom: 1.2rem;
  padding: 0.8rem;
  background: rgba(255, 255, 255, 0.1);
  border-radius: 12px;
  font-size: 0.9rem;
}

.info-item {
  display: flex;
  align-items: center;
  gap: 0.4rem;
}

.info-label {
  font-weight: bold;
  opacity: 0.9;
  min-width: 70px;
  font-size: 0.9rem;
}

.info-value {
  color: white;
  word-break: break-all;
  font-size: 0.9rem;
}

.info-diagnosis {
  font-weight: bold;
  padding: 0.1rem 0.8rem;
  border-radius: 20px;
  font-size: 0.95rem;
}

.info-diagnosis.result-normal {
  background-color: white;
  color: #4ecdc4;
  border: 2px solid #4ecdc4;
}

.info-diagnosis.result-abnormal {
  background-color: white;
  color: #ff6b6b;
  border: 2px solid #ff6b6b;
}

.image-section,
.heatmap-section {
  margin: 1.2rem 0;
}

.image-section h2,
.heatmap-section h2 {
  margin-bottom: 0.6rem;
  font-size: 1.2rem;
  font-weight: 500;
}

.detail-image {
  width: 100%;
  max-height: 800px;
  object-fit: contain;
  border-radius: 12px;
  background: rgba(0, 0, 0, 0.2);
}

.heatmap-buttons {
  display: flex;
  gap: 0.6rem;
  margin-bottom: 1rem;
  flex-wrap: wrap;
}

.heatmap-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
  gap: 1rem;
  margin-top: 0.1rem;
}

.heatmap-item {
  text-align: center;
}

.heatmap-item h3 {
  margin-bottom: 0.4rem;
  font-size: 0.9rem;
  color: #ffd700;
  font-weight: 500;
}

.heatmap-image {
  width: 100%;
  max-height: 400px;
  object-fit: contain;
  border-radius: 10px;
  cursor: pointer;
  transition: transform 0.3s;
  background: rgba(0, 0, 0, 0.2);
  min-height: 100px;
}

.heatmap-image:hover {
  transform: scale(1.02);
}

.image-error {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 100px;
  background: rgba(255, 255, 255, 0.1);
  border-radius: 10px;
  gap: 5px;
  color: rgba(255, 255, 255, 0.6);
  font-size: 0.8rem;
}

.no-heatmap {
  margin-top: 0.8rem;
  padding: 1rem;
  background: rgba(255, 255, 255, 0.1);
  border-radius: 12px;
}

.action-buttons {
  display: flex;
  gap: 0.6rem;
  justify-content: center;
  margin-top: 1.2rem;
  flex-wrap: wrap;
}

.delete-warning {
  text-align: center;
  padding: 0.8rem;
}

.warning-text {
  color: #f56c6c;
  font-weight: bold;
  margin-top: 0.4rem;
  font-size: 0.9rem;
}

.loading {
  padding: 1.5rem;
  background: rgba(255, 255, 255, 0.1);
  border-radius: 20px;
}

.error-message {
  padding: 1.5rem;
}

.el-button {
  border-radius: 20px;
}

.el-button--small {
  padding: 0.4rem 1rem;
  font-size: 0.85rem;
}

.el-button--primary {
  background: rgba(64, 158, 255, 0.3);
  border: 1px solid rgba(64, 158, 255, 0.5);
  color: white;
}

.el-button--success {
  background: rgba(103, 194, 58, 0.3);
  border: 1px solid rgba(103, 194, 58, 0.5);
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

.el-button:hover {
  transform: translateY(-2px);
  box-shadow: 0 5px 15px rgba(0, 0, 0, 0.3);
}
</style>