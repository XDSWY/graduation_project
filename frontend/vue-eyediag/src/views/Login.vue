<template>
  <div class="login-container">
    <div class="login-card">
      <h1>🏥 眼底病筛查系统</h1>
      <h2>用户登录</h2>

      <el-form
        ref="formRef"
        :model="form"
        :rules="rules"
        label-position="top"
        @submit.prevent="handleLogin"
      >
        <el-form-item label="用户名" prop="username">
          <el-input
            v-model="form.username"
            placeholder="请输入用户名"
            prefix-icon="User"
            clearable
          />
        </el-form-item>

        <el-form-item label="密码" prop="password">
          <el-input
            v-model="form.password"
            type="password"
            placeholder="请输入密码"
            prefix-icon="Lock"
            show-password
            clearable
            @keyup.enter="handleLogin"
          />
        </el-form-item>

        <el-button
          type="primary"
          :loading="loading"
          @click="handleLogin"
          class="login-button"
        >
          登录
        </el-button>
      </el-form>

      <!-- 登录失败提示 -->
      <div v-if="loginError" class="error-message">
        <el-alert
          :title="loginError"
          type="error"
          :closable="false"
          show-icon
        />
      </div>

      <div class="register-link">
        还没有账号？
        <router-link to="/register">立即注册</router-link>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, reactive } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import api from '../api'

export default {
  name: 'Login',
  setup() {
    const router = useRouter()
    const formRef = ref(null)
    const loading = ref(false)
    const loginError = ref('')

    const form = reactive({
      username: '',
      password: ''
    })

    const rules = {
      username: [
        { required: true, message: '请输入用户名', trigger: 'blur' },
        { min: 3, max: 20, message: '长度在 3 到 20 个字符', trigger: 'blur' }
      ],
      password: [
        { required: true, message: '请输入密码', trigger: 'blur' },
        { min: 6, message: '密码至少6个字符', trigger: 'blur' }
      ]
    }

    const handleLogin = async () => {
      if (!formRef.value) return

      try {
        await formRef.value.validate()
        loading.value = true
        loginError.value = ''

        const response = await api.post('/login/', {
          username: form.username,
          password: form.password
        })

        if (response.data.success) {
          // 保存token、用户名和管理员状态
          localStorage.setItem('token', response.data.token)
          localStorage.setItem('username', response.data.username)
          localStorage.setItem('isAdmin', response.data.is_admin ? 'true' : 'false')

          ElMessage.success('登录成功')
          router.push('/home')
        }
      } catch (error) {
        console.error('登录失败:', error)
        if (error.response?.status === 401) {
          // 用户名或密码错误
          loginError.value = '❌ 用户名或密码错误，请重新输入'
        } else if (error.response?.status === 400) {
          // 输入验证失败
          loginError.value = '❌ 请输入用户名和密码'
        } else {
          // 其他错误（可能是网络问题或用户不存在）
          loginError.value = '❌ 该用户尚未注册，请先注册账号'
        }
      } finally {
        loading.value = false
      }
    }

    return {
      formRef,
      form,
      rules,
      loading,
      loginError,
      handleLogin
    }
  }
}
</script>

<style scoped>
.login-container {
  min-height: 100vh;
  display: flex;
  justify-content: center;
  align-items: center;
  background: linear-gradient(-45deg, #ee7752, #e73c7e, #23a6d5, #23d5ab);
  background-size: 400% 400%;
  animation: gradient 15s ease infinite;
}

@keyframes gradient {
  0% { background-position: 0% 50%; }
  50% { background-position: 100% 50%; }
  100% { background-position: 0% 50%; }
}

.login-card {
  background: rgba(255, 255, 255, 0.2);
  backdrop-filter: blur(15px);
  -webkit-backdrop-filter: blur(15px);
  border: 1px solid rgba(255, 255, 255, 0.3);
  border-radius: 30px;
  padding: 50px;
  width: 100%;
  max-width: 480px;
  box-shadow: 0 25px 50px rgba(0, 0, 0, 0.2);
  animation: fadeIn 1s;
}

@keyframes fadeIn {
  from {
    opacity: 0;
    transform: translateY(-20px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.login-card h1 {
  text-align: center;
  color: white;
  margin-bottom: 10px;
  font-size: 2em;
  text-shadow: 2px 2px 4px rgba(0,0,0,0.2);
}

.login-card h2 {
  text-align: center;
  color: white;
  margin-bottom: 30px;
  font-size: 1.5em;
  opacity: 0.9;
}

:deep(.el-form-item__label) {
  color: white !important;
  font-weight: 500;
}

:deep(.el-input__wrapper) {
  background: rgba(255, 255, 255, 0.15);
  border: 1px solid rgba(255, 255, 255, 0.3);
  box-shadow: none;
}

:deep(.el-input__inner) {
  color: white;
}

:deep(.el-input__inner::placeholder) {
  color: rgba(255, 255, 255, 0.6);
}

:deep(.el-input__prefix-inner) {
  color: rgba(255, 255, 255, 0.7);
}

.login-button {
  width: 100%;
  margin-top: 20px;
  background: linear-gradient(135deg, #FF6B6B, #4ECDC4);
  border: none;
  height: 45px;
  font-size: 1.1em;
  font-weight: 600;
  letter-spacing: 1px;
  transition: all 0.4s;
}

.login-button:hover {
  transform: translateY(-3px);
  box-shadow: 0 15px 30px rgba(0,0,0,0.3);
}

.error-message {
  margin-top: 20px;
  animation: shake 0.5s;
}

@keyframes shake {
  0%, 100% { transform: translateX(0); }
  10%, 30%, 50%, 70%, 90% { transform: translateX(-5px); }
  20%, 40%, 60%, 80% { transform: translateX(5px); }
}

:deep(.el-alert) {
  background: rgba(255, 107, 107, 0.3);
  border: 1px solid rgba(255, 107, 107, 0.5);
  backdrop-filter: blur(5px);
  color: white;
  border-radius: 15px;
}

:deep(.el-alert__title) {
  color: white;
}

:deep(.el-alert__icon) {
  color: white;
}

.register-link {
  text-align: center;
  margin-top: 25px;
  color: white;
}

.register-link a {
  color: white;
  font-weight: bold;
  text-decoration: none;
  margin-left: 5px;
}

.register-link a:hover {
  text-decoration: underline;
}
</style>