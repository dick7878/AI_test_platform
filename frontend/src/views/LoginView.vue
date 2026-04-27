<script setup>
import { reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'

import { DevLogin } from '../api/auth'

const router = useRouter()
const loading = ref(false)
const form = reactive({
  username: '',
  password: '',
})

async function HandleLogin() {
  if (!form.username || !form.password) {
    ElMessage.warning('请输入用户名和密码')
    return
  }

  loading.value = true
  try {
    await DevLogin({
      username: form.username,
      password: form.password,
    })
    localStorage.setItem('aits_logged_in', '1')
    ElMessage.success('登录成功')
    await router.replace('/projects')
  } catch (_error) {
    ElMessage.error('登录失败，请检查用户名或密码')
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <div class="login-page">
    <el-card class="login-card" shadow="hover">
      <template #header>
        <div class="login-title">AITS 开发登录</div>
      </template>
      <el-form @submit.prevent>
        <el-form-item label="用户名">
          <el-input v-model="form.username" placeholder="请输入用户名" />
        </el-form-item>
        <el-form-item label="密码">
          <el-input
            v-model="form.password"
            type="password"
            show-password
            placeholder="请输入密码"
            @keyup.enter="HandleLogin"
          />
        </el-form-item>
        <el-button type="primary" :loading="loading" @click="HandleLogin">
          登录
        </el-button>
      </el-form>
    </el-card>
  </div>
</template>

<style scoped>
.login-page {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 24px;
  background: #f5f7fa;
}

.login-card {
  width: 420px;
  max-width: 100%;
}

.login-title {
  font-size: 18px;
  font-weight: 600;
}
</style>
