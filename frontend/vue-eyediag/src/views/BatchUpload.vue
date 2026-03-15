<template>
  <div class="batch-container">
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
      <h1 class="page-title">📁 批量上传</h1>
      <p class="page-subtitle">同时上传多张照片，批量处理</p>

      <div class="upload-area" @click="triggerFileInput" @dragover.prevent @drop="handleDrop">
        <input
          type="file"
          ref="fileInput"
          @change="handleFileSelect"
          accept="image/jpeg,image/png,image/jpg"
          multiple
          style="display: none"
        >
        <div class="upload-icon">📤</div>
        <p>点击或拖拽图片到此处</p>
        <p class="upload-hint">支持多选，最多20张，每张不超过10MB</p>
      </div>

      <!-- 文件列表 -->
      <div v-if="files.length > 0" class="file-list">
        <div class="file-list-header">
          <h3>已选择 {{ files.length }} 张图片</h3>
          <el-button type="primary" @click="uploadAll" :loading="uploading">
            {{ uploading ? '处理中...' : '开始批量诊断' }}
          </el-button>
        </div>

        <el-table :data="files" style="width: 100%" stripe>
          <el-table-column label="预览" width="100">
            <template #default="{ row }">
              <img :src="row.preview" class="table-preview">
            </template>
          </el-table-column>
          <el-table-column prop="name" label="文件名" />
          <el-table-column prop="size" label="大小" width="120">
            <template #default="{ row }">
              {{ (row.size / 1024).toFixed(1) }} KB
            </template>
          </el-table-column>
          <el-table-column label="诊断结果" width="200">
            <template #default="{ row }">
              <span v-if="row.result" :class="row.resultClass">
                {{ row.result }} ({{ (row.confidence * 100).toFixed(1) }}%)
              </span>
              <span v-else class="pending">等待诊断</span>
            </template>
          </el-table-column>
          <el-table-column label="操作" width="100">
            <template #default="{ row, $index }">
              <el-button
                type="danger"
                size="small"
                circle
                @click="removeFile($index)"
              >×</el-button>
            </template>
          </el-table-column>
        </el-table>
      </div>

      <!-- 批量结果导出 -->
      <div v-if="completedCount > 0" class="export-section">
        <el-button type="success" @click="exportResults" :loading="exporting">
          导出诊断报告 (CSV)
        </el-button>
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
  name: 'BatchUpload',
  setup() {
    const router = useRouter()
    const username = ref(localStorage.getItem('username') || '')
    const isAdmin = ref(localStorage.getItem('isAdmin') === 'true')
    const fileInput = ref(null)
    const files = ref([])
    const uploading = ref(false)
    const exporting = ref(false)

    const completedCount = computed(() => {
      return files.value.filter(f => f.result).length
    })

    const triggerFileInput = () => {
      fileInput.value.click()
    }

    const handleFileSelect = (event) => {
      const selectedFiles = Array.from(event.target.files)
      addFiles(selectedFiles)
    }

    const handleDrop = (event) => {
      event.preventDefault()
      const droppedFiles = Array.from(event.dataTransfer.files)
      addFiles(droppedFiles)
    }

    const addFiles = (newFiles) => {
      // 检查总数
      if (files.value.length + newFiles.length > 20) {
        ElMessage.warning('最多只能上传20张图片')
        return
      }

      newFiles.forEach(file => {
        // 检查文件类型
        const allowedTypes = ['image/jpeg', 'image/png', 'image/jpg']
        if (!allowedTypes.includes(file.type)) {
          ElMessage.warning(`文件 ${file.name} 格式不支持，已跳过`)
          return
        }

        // 检查文件大小
        if (file.size > 10 * 1024 * 1024) {
          ElMessage.warning(`文件 ${file.name} 超过10MB，已跳过`)
          return
        }

        files.value.push({
          file: file,
          name: file.name,
          size: file.size,
          preview: URL.createObjectURL(file),
          result: null,
          confidence: 0,
          resultClass: '',
          id: null
        })
      })

      // 清空 input 以便重新选择
      if (fileInput.value) {
        fileInput.value.value = ''
      }
    }

    const removeFile = (index) => {
      URL.revokeObjectURL(files.value[index].preview)
      files.value.splice(index, 1)
    }

    const uploadAll = async () => {
      if (files.value.length === 0) return

      const formData = new FormData()
      files.value.forEach(item => {
        formData.append('images', item.file)
      })

      uploading.value = true
      try {
        const response = await api.post('/batch-upload/', formData, {
          headers: { 'Content-Type': 'multipart/form-data' }
        })

        if (response.data.success) {
          // 更新每个文件的结果
          response.data.records.forEach((record, index) => {
            if (index < files.value.length) {
              files.value[index].result = record.result
              files.value[index].confidence = record.confidence
              files.value[index].id = record.id
              files.value[index].resultClass =
                record.result === '正常' ? 'result-normal' : 'result-abnormal'
            }
          })

          ElMessage.success(response.data.message)
        }
      } catch (error) {
        console.error('批量上传失败:', error)
        ElMessage.error(error.response?.data?.message || '批量上传失败')
      } finally {
        uploading.value = false
      }
    }

    const exportResults = async () => {
      exporting.value = true
      try {
        // 生成 CSV 内容
        const headers = ['文件名', '诊断结果', '置信度', '诊断时间']
        const rows = files.value
          .filter(f => f.result)
          .map(f => [
            f.name,
            f.result,
            `${(f.confidence * 100).toFixed(1)}%`,
            new Date().toLocaleString()
          ])

        const csvContent = [
          headers.join(','),
          ...rows.map(row => row.join(','))
        ].join('\n')

        // 下载 CSV
        const blob = new Blob(['\uFEFF' + csvContent], { type: 'text/csv;charset=utf-8;' })
        const link = document.createElement('a')
        link.href = URL.createObjectURL(blob)
        link.download = `诊断报告_${new Date().toISOString().slice(0,10)}.csv`
        link.click()

        ElMessage.success('报告导出成功')
      } catch (error) {
        console.error('导出失败:', error)
        ElMessage.error('导出失败')
      } finally {
        exporting.value = false
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

    return {
      username,
      isAdmin,
      fileInput,
      files,
      uploading,
      exporting,
      completedCount,
      triggerFileInput,
      handleFileSelect,
      handleDrop,
      removeFile,
      uploadAll,
      exportResults,
      goBack,
      goToManageUsers,
      handleLogout
    }
  }
}
</script>

<style scoped>
.batch-container {
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
  max-width: 1000px;
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

.file-list {
  background: rgba(255, 255, 255, 0.2);
  backdrop-filter: blur(15px);
  border-radius: 20px;
  padding: 2rem;
  margin-top: 2rem;
}

.file-list-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1.5rem;
}

.table-preview {
  width: 60px;
  height: 60px;
  object-fit: cover;
  border-radius: 10px;
}

.pending {
  color: #aaa;
}

.result-normal {
  color: #4ecdc4;
  font-weight: bold;
}

.result-abnormal {
  color: #ff6b6b;
  font-weight: bold;
}

.export-section {
  text-align: center;
  margin-top: 2rem;
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

.el-button--success {
  background: rgba(103, 194, 58, 0.3);
  border: 1px solid rgba(103, 194, 58, 0.5);
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