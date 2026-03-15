<template>
  <div class="home-container">
    <nav class="navbar">
      <div class="nav-brand">🏥 眼底病筛查系统</div>
      <div class="nav-user">
        <span>👋 你好，{{ username }}！</span>
        <!-- 统计按钮 - 对所有用户可见 -->
        <el-button
          type="info"
          size="small"
          @click="goToStatistics"
          class="stat-btn"
        >
          📊 统计
        </el-button>
        <!-- 管理员按钮 -->
        <el-button
          v-if="isAdmin"
          type="warning"
          size="small"
          @click="goToManageUsers"
          class="admin-btn"
        >
          👥 管理用户
        </el-button>
        <el-button type="danger" size="small" @click="handleLogout">退出</el-button>
      </div>
    </nav>

    <div class="content">
      <h1>欢迎回来，{{ username }}！</h1>
      <p class="subtitle">请选择要进行的操作</p>

      <!-- 四个卡片居中一排 -->
      <div class="card-grid">
        <div class="card" @click="goToUpload">
          <div class="card-icon">📸</div>
          <h3>上传照片</h3>
          <p>上传眼底照片进行AI智能诊断</p>
        </div>

        <div class="card" @click="goToBatch">
          <div class="card-icon">📁</div>
          <h3>批量上传</h3>
          <p>同时上传多张照片，批量处理</p>
        </div>

        <div class="card" @click="goToFavorites">
          <div class="card-icon">⭐</div>
          <h3>我的收藏</h3>
          <p>查看和管理收藏的诊断记录</p>
        </div>

        <div class="card" @click="goToHistory">
          <div class="card-icon">📋</div>
          <h3>历史记录</h3>
          <p>查看所有诊断历史和Grad-CAM热力图</p>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'

export default {
  name: 'Home',
  setup() {
    const router = useRouter()
    const username = ref(localStorage.getItem('username') || '用户')
    const isAdmin = ref(localStorage.getItem('isAdmin') === 'true')

    const handleLogout = () => {
      localStorage.removeItem('token')
      localStorage.removeItem('username')
      localStorage.removeItem('isAdmin')
      ElMessage.success('已退出登录')
      router.push('/login')
    }

    const goToUpload = () => {
      router.push('/upload')
    }

    const goToBatch = () => {
      router.push('/batch')
    }

    const goToFavorites = () => {
      router.push('/favorites')
    }

    const goToHistory = () => {
      console.log('跳转到历史记录') // 添加调试日志
      router.push('/history')
    }

    const goToStatistics = () => {
      router.push('/statistics')
    }

    const goToManageUsers = () => {
      router.push('/manage-users')
    }

    return {
      username,
      isAdmin,
      handleLogout,
      goToUpload,
      goToBatch,
      goToFavorites,
      goToHistory,
      goToStatistics,
      goToManageUsers
    }
  }
}
</script>

<style scoped>
/* 动态渐变背景 */
.home-container {
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

/* 毛玻璃导航栏 */
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
  flex-wrap: wrap;
}

.nav-user span {
  font-size: 1.1rem;
  text-shadow: 1px 1px 2px rgba(0, 0, 0, 0.2);
}

/* 统计按钮样式 */
.stat-btn {
  background: rgba(64, 158, 255, 0.3);
  border: 1px solid rgba(64, 158, 255, 0.5);
  color: white;
  font-weight: bold;
  transition: all 0.3s;
  backdrop-filter: blur(5px);
}

.stat-btn:hover {
  background: rgba(64, 158, 255, 0.5);
  transform: translateY(-2px);
  box-shadow: 0 5px 15px rgba(64, 158, 255, 0.3);
}

/* 管理员按钮样式 */
.admin-btn {
  background: rgba(255, 215, 0, 0.3);
  border: 1px solid rgba(255, 215, 0, 0.5);
  color: white;
  font-weight: bold;
  transition: all 0.3s;
  backdrop-filter: blur(5px);
}

.admin-btn:hover {
  background: rgba(255, 215, 0, 0.5);
  transform: translateY(-2px);
  box-shadow: 0 5px 15px rgba(255, 215, 0, 0.3);
}

/* 退出按钮样式 */
.el-button--danger {
  background: rgba(255, 107, 107, 0.3);
  border: 1px solid rgba(255, 107, 107, 0.5);
  color: white;
  font-weight: bold;
  backdrop-filter: blur(5px);
}

.el-button--danger:hover {
  background: rgba(255, 107, 107, 0.5);
  transform: translateY(-2px);
  box-shadow: 0 5px 15px rgba(255, 107, 107, 0.3);
}

.content {
  max-width: 1200px;
  margin: 0 auto;
  padding: 3rem 2rem;
  text-align: center;
  color: white;
}

.content h1 {
  font-size: 2.5rem;
  margin-bottom: 1rem;
  text-shadow: 2px 2px 4px rgba(0, 0, 0, 0.2);
  animation: fadeInDown 1s;
}

.subtitle {
  font-size: 1.2rem;
  opacity: 0.9;
  margin-bottom: 3rem;
  text-shadow: 1px 1px 2px rgba(0, 0, 0, 0.2);
  animation: fadeInUp 1s;
}

/* 四个卡片居中一排 */
.card-grid {
  display: flex;
  justify-content: center;
  align-items: center;
  gap: 2rem;
  flex-wrap: wrap;
  animation: fadeIn 1.5s;
  margin: 0 auto;
}

.card {
  background: rgba(255, 255, 255, 0.2);
  backdrop-filter: blur(15px);
  border: 1px solid rgba(255, 255, 255, 0.3);
  border-radius: 30px;
  padding: 2rem 1.5rem;
  width: 250px;
  min-width: 220px;
  color: white;
  cursor: pointer;
  transition: all 0.4s cubic-bezier(0.175, 0.885, 0.32, 1.275);
  text-align: center;
  box-shadow: 0 25px 50px rgba(0, 0, 0, 0.2);
  position: relative;
  overflow: hidden;
}

.card::before {
  content: '';
  position: absolute;
  top: -50%;
  left: -50%;
  width: 200%;
  height: 200%;
  background: radial-gradient(circle, rgba(255, 255, 255, 0.3) 0%, transparent 70%);
  opacity: 0;
  transition: opacity 0.5s;
  pointer-events: none;
}

.card:hover {
  transform: translateY(-10px) scale(1.02);
  box-shadow: 0 40px 70px rgba(0, 0, 0, 0.3);
}

.card:hover::before {
  opacity: 1;
}

.card-icon {
  font-size: 3.5rem;
  margin-bottom: 1rem;
  animation: float 3s ease-in-out infinite;
}

@keyframes float {
  0%, 100% { transform: translateY(0); }
  50% { transform: translateY(-8px); }
}

.card h3 {
  font-size: 1.5rem;
  margin-bottom: 0.8rem;
  text-shadow: 2px 2px 4px rgba(0, 0, 0, 0.2);
}

.card p {
  font-size: 0.9rem;
  opacity: 0.9;
  line-height: 1.5;
}

@keyframes fadeInDown {
  from {
    opacity: 0;
    transform: translateY(-30px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

@keyframes fadeInUp {
  from {
    opacity: 0;
    transform: translateY(30px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

@keyframes fadeIn {
  from {
    opacity: 0;
  }
  to {
    opacity: 1;
  }
}

/* 响应式设计 */
@media (max-width: 1024px) {
  .card {
    width: 220px;
    padding: 1.5rem 1rem;
  }
}

@media (max-width: 768px) {
  .nav-user {
    gap: 0.5rem;
  }

  .nav-user span {
    font-size: 0.9rem;
  }

  .card {
    width: 100%;
    max-width: 280px;
  }
}
</style>