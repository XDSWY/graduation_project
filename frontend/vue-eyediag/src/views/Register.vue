<template>
  <div class="register-container">
    <div class="register-card">
      <h1>🏥 眼底病筛查系统</h1>
      <h2>用户注册</h2>

      <el-form
        ref="formRef"
        :model="form"
        :rules="rules"
        label-position="top"
        @submit.prevent="handleRegister"
      >
        <el-form-item label="用户名" prop="username">
          <el-input
            v-model="form.username"
            placeholder="请输入用户名"
            prefix-icon="User"
            clearable
            @blur="checkUsername"
          />
          <div v-if="usernameCheck" class="username-check" :class="usernameCheck.status">
            {{ usernameCheck.message }}
          </div>
        </el-form-item>

        <el-form-item label="密码" prop="password">
          <el-input
            v-model="form.password"
            type="password"
            placeholder="请输入密码"
            prefix-icon="Lock"
            show-password
            clearable
          />
        </el-form-item>

        <el-form-item label="确认密码" prop="confirmPassword">
          <el-input
            v-model="form.confirmPassword"
            type="password"
            placeholder="请再次输入密码"
            prefix-icon="Lock"
            show-password
            clearable
          />
        </el-form-item>

        <el-button
          type="primary"
          :loading="loading"
          @click="handleRegister"
          class="register-button"
        >
          注册
        </el-button>
      </el-form>

      <div class="login-link">
        已有账号？
        <router-link to="/login">立即登录</router-link>
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
  name: 'Register',
  setup() {
    const router = useRouter()
    const formRef = ref(null)
    const loading = ref(false)
    const usernameCheck = ref(null)

    const form = reactive({
      username: '',
      password: '',
      confirmPassword: ''
    })

    // 验证确认密码
    const validateConfirmPassword = (rule, value, callback) => {
      if (value !== form.password) {
        callback(new Error('两次输入的密码不一致'))
      } else {
        callback()
      }
    }

    const rules = {
      username: [
        { required: true, message: '请输入用户名', trigger: 'blur' },
        { min: 3, max: 20, message: '长度在 3 到 20 个字符', trigger: 'blur' }
      ],
      password: [
        { required: true, message: '请输入密码', trigger: 'blur' },
        { min: 6, message: '密码至少6个字符', trigger: 'blur' }
      ],
      confirmPassword: [
        { required: true, message: '请再次输入密码', trigger: 'blur' },
        { validator: validateConfirmPassword, trigger: 'blur' }
      ]
    }

    // 检查用户名是否可用
    const checkUsername = async () => {
      if (!form.username || form.username.length < 3) return

      try {
        const response = await api.get('/check-username/', {
          params: { username: form.username }
        })

        if (response.data.exists) {
          usernameCheck.value = {
            status: 'error',
            message: '❌ 用户名已存在'
          }
        } else {
          usernameCheck.value = {
            status: 'success',
            message: '✅ 用户名可用'
          }
        }
      } catch (error) {
        console.error('检查用户名失败:', error)
      }
    }

    const handleRegister = async () => {
      if (!formRef.value) return

      try {
        await formRef.value.validate()
        loading.value = true

        const response = await api.post('/register/', {
          username: form.username,
          password: form.password
        })

        if (response.data.success) {
          ElMessage.success('🎉 注册成功，请登录')
          // 跳转到登录页
          router.push('/login')
        }
      } catch (error) {
        console.error('注册失败:', error)
        if (error.response?.data?.message) {
          ElMessage.error(error.response.data.message)
        } else {
          ElMessage.error('注册失败，请稍后重试')
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
      usernameCheck,
      checkUsername,
      handleRegister
    }
  }
}
</script>

<style scoped>
.register-container {
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

.register-card {
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

.register-card h1 {
  text-align: center;
  color: white;
  margin-bottom: 10px;
  font-size: 2em;
  text-shadow: 2px 2px 4px rgba(0,0,0,0.2);
}

.register-card h2 {
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

.username-check {
  margin-top: 5px;
  font-size: 0.9em;
  padding-left: 5px;
  animation: slideIn 0.3s;
}

@keyframes slideIn {
  from {
    opacity: 0;
    transform: translateX(-10px);
  }
  to {
    opacity: 1;
    transform: translateX(0);
  }
}

.username-check.success {
  color: #4ecdc4;
}

.username-check.error {
  color: #ff6b6b;
}

.register-button {
  width: 100%;
  margin-top: 20px;
  background: linear-gradient(135deg, #4ECDC4, #45B7D1);
  border: none;
  height: 45px;
  font-size: 1.1em;
  font-weight: 600;
  letter-spacing: 1px;
  transition: all 0.4s;
}

.register-button:hover {
  transform: translateY(-3px);
  box-shadow: 0 15px 30px rgba(0,0,0,0.3);
}

.login-link {
  text-align: center;
  margin-top: 25px;
  color: white;
}

.login-link a {
  color: white;
  font-weight: bold;
  text-decoration: none;
  margin-left: 5px;
}

.login-link a:hover {
  text-decoration: underline;
}
</style>