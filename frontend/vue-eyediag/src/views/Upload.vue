<template>
  <div class="upload-container">
    <nav class="navbar">
      <div class="nav-brand">🏥 眼底病筛查系统</div>
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
      <h1 class="page-title">📸 上传照片</h1>
      <p class="page-subtitle">上传眼底照片进行AI智能诊断</p>

      <div class="upload-area" @click="triggerFileInput" @dragover.prevent @drop="handleDrop">
        <input
          type="file"
          ref="fileInput"
          @change="handleFileSelect"
          accept="image/jpeg,image/png,image/jpg"
          style="display: none"
        >
        <div v-if="!previewUrl" class="upload-placeholder">
          <div class="upload-icon">📤</div>
          <p>点击或拖拽图片到此处</p>
          <p class="upload-hint">支持 JPG、PNG 格式，单张不超过10MB</p>
        </div>
        <div v-else class="preview-container">
          <img :src="previewUrl" class="preview-image" alt="预览">
          <div class="preview-actions">
            <el-button type="info" size="small" @click.stop="clearPreview">重新选择</el-button>
            <el-button type="primary" size="small" @click.stop="uploadImage" :loading="uploading">
              {{ uploading ? '诊断中...' : '开始诊断' }}
            </el-button>
          </div>
        </div>
      </div>

      <!-- 诊断结果 -->
      <div v-if="result" class="result-card">
        <h2>诊断结果</h2>
        <div class="result-content">
          <!-- 添加文件名显示 -->
          <div class="result-item">
            <span class="result-label">文件名称：</span>
            <span class="result-value">{{ fileName }}</span>
          </div>
          <div class="result-item">
            <span class="result-label">诊断结论：</span>
            <span class="result-diagnosis" :class="resultClass">{{ result.result }}</span>
          </div>
          <div class="result-item">
            <span class="result-label">置信度：</span>
            <span class="result-value">{{ (result.confidence * 100).toFixed(1) }}%</span>
          </div>
          <div class="result-item">
            <span class="result-label">诊断时间：</span>
            <span class="result-value">{{ formatDate(result.created_at) }}</span>
          </div>
          <div class="result-actions">
            <el-button type="warning" @click="toggleFavorite" :loading="favoriteLoading">
              {{ result.is_favorite ? '取消收藏' : '添加收藏' }}
            </el-button>
            <el-button type="primary" @click="uploadAnother">再次上传</el-button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, computed } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import api from '../api'

export default {
  name: 'Upload',
  setup() {
    const router = useRouter()
    const username = ref(localStorage.getItem('username') || '')
    const isAdmin = ref(localStorage.getItem('isAdmin') === 'true')
    const fileInput = ref(null)
    const previewUrl = ref('')
    const selectedFile = ref(null)
    const fileName = ref('') // 添加文件名变量
    const uploading = ref(false)
    const result = ref(null)
    const favoriteLoading = ref(false)

    const resultClass = computed(() => {
      if (!result.value) return ''
      if (result.value.result === '正常') return 'result-normal'
      return 'result-abnormal'
    })

    const triggerFileInput = () => {
      fileInput.value.click()
    }

    const handleFileSelect = (event) => {
      const file = event.target.files[0]
      if (file) {
        validateAndPreview(file)
      }
    }

    const handleDrop = (event) => {
      event.preventDefault()
      const file = event.dataTransfer.files[0]
      if (file) {
        validateAndPreview(file)
      }
    }

    const validateAndPreview = (file) => {
      // 检查文件类型
      const allowedTypes = ['image/jpeg', 'image/png', 'image/jpg']
      if (!allowedTypes.includes(file.type)) {
        ElMessage.error('只支持 JPG、PNG 格式的图片')
        return
      }

      // 检查文件大小（10MB）
      if (file.size > 10 * 1024 * 1024) {
        ElMessage.error('图片大小不能超过 10MB')
        return
      }

      selectedFile.value = file
      fileName.value = file.name // 保存文件名
      previewUrl.value = URL.createObjectURL(file)
    }

    const clearPreview = () => {
      previewUrl.value = ''
      selectedFile.value = null
      fileName.value = '' // 清除文件名
      if (fileInput.value) {
        fileInput.value.value = ''
      }
    }

    const uploadImage = async () => {
      if (!selectedFile.value) return

      const formData = new FormData()
      formData.append('image', selectedFile.value)

      uploading.value = true
      try {
        const response = await api.post('/upload/', formData, {
          headers: { 'Content-Type': 'multipart/form-data' }
        })

        if (response.data.success) {
          result.value = response.data.record
          ElMessage.success('诊断完成')
        }
      } catch (error) {
        console.error('上传失败:', error)
        ElMessage.error(error.response?.data?.message || '上传失败')
      } finally {
        uploading.value = false
      }
    }

    const toggleFavorite = async () => {
      if (!result.value) return

      favoriteLoading.value = true
      try {
        const response = await api.post(`/records/${result.value.id}/toggle-favorite/`)
        if (response.data.success) {
          result.value.is_favorite = response.data.is_favorite
          ElMessage.success(response.data.message)
        }
      } catch (error) {
        console.error('操作失败:', error)
        ElMessage.error('操作失败')
      } finally {
        favoriteLoading.value = false
      }
    }

    const uploadAnother = () => {
      clearPreview()
      result.value = null
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

    return {
      username,
      isAdmin,
      fileInput,
      previewUrl,
      fileName, // 返回文件名变量
      uploading,
      result,
      favoriteLoading,
      resultClass,
      triggerFileInput,
      handleFileSelect,
      handleDrop,
      validateAndPreview,
      clearPreview,
      uploadImage,
      toggleFavorite,
      uploadAnother,
      formatDate,
      goBack,
      goToManageUsers,
      handleLogout
    }
  }
}
</script>

<style scoped>
.upload-container {
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
  max-width: 800px;
  margin: 0 auto;
  padding: 3rem 2rem;
  color: white;
}

.page-title {
  text-align: center;
  font-size: 2.5rem;
  margin-bottom: 0.5rem;
  text-shadow: 2px 2px 4px rgba(0, 0, 0, 0.2);
}

.page-subtitle {
  text-align: center;
  opacity: 0.9;
  margin-bottom: 3rem;
}

.upload-area {
  background: rgba(255, 255, 255, 0.2);
  backdrop-filter: blur(15px);
  border: 2px dashed rgba(255, 255, 255, 0.5);
  border-radius: 30px;
  padding: 3rem;
  text-align: center;
  cursor: pointer;
  transition: all 0.3s;
  margin-bottom: 2rem;
}

.upload-area:hover {
  background: rgba(255, 255, 255, 0.3);
  border-color: white;
}

.upload-placeholder {
  color: white;
}

.upload-icon {
  font-size: 5rem;
  margin-bottom: 1rem;
  animation: bounce 2s infinite;
}

@keyframes bounce {
  0%, 100% { transform: translateY(0); }
  50% { transform: translateY(-10px); }
}

.upload-hint {
  font-size: 0.9rem;
  opacity: 0.8;
  margin-top: 1rem;
}

.preview-container {
  position: relative;
}

.preview-image {
  max-width: 100%;
  max-height: 400px;
  border-radius: 20px;
  box-shadow: 0 10px 30px rgba(0, 0, 0, 0.3);
}

.preview-actions {
  margin-top: 1rem;
  display: flex;
  gap: 1rem;
  justify-content: center;
}

/* 诊断结果卡片样式 - 新增 */
.result-card {
  background: rgba(255, 255, 255, 0.2);
  backdrop-filter: blur(15px);
  border: 1px solid rgba(255, 255, 255, 0.3);
  border-radius: 30px;
  padding: 2rem;
  margin-top: 2rem;
  animation: fadeIn 0.5s;
}

@keyframes fadeIn {
  from { opacity: 0; transform: translateY(20px); }
  to { opacity: 1; transform: translateY(0); }
}

.result-card h2 {
  text-align: center;
  margin-bottom: 1.5rem;
  color: white;
  text-shadow: 2px 2px 4px rgba(0, 0, 0, 0.2);
}

.result-content {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.result-item {
  display: flex;
  justify-content: center;
  align-items: center;
  gap: 1rem;
  font-size: 1.2rem;
  flex-wrap: wrap;
}

.result-label {
  opacity: 0.9;
  color: white;
  font-weight: 500;
  min-width: 100px;
  text-align: right;
}

.result-value {
  font-weight: bold;
  color: white;
  min-width: 200px;
  text-align: left;
}

/* 诊断结论的特殊样式 - 白底红字/白底绿字 */
.result-diagnosis {
  font-weight: bold;
  font-size: 1.4rem;
  padding: 0.3rem 1rem;
  border-radius: 30px;
  min-width: 200px;
  text-align: center;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.result-diagnosis.result-normal {
  background-color: white;
  color: #4ecdc4;
  border: 2px solid #4ecdc4;
}

.result-diagnosis.result-abnormal {
  background-color: white;
  color: #ff6b6b;
  border: 2px solid #ff6b6b;
}

.result-actions {
  display: flex;
  gap: 1rem;
  justify-content: center;
  margin-top: 1.5rem;
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

.el-button--info {
  background: rgba(144, 147, 153, 0.3);
  border: 1px solid rgba(144, 147, 153, 0.5);
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