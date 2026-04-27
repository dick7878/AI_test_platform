<script setup>
import { ElMessage } from 'element-plus'
import { onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'

import { DevLogout } from '../api/auth'
import { GetProjects } from '../api/projects'

const router = useRouter()
const loading = ref(false)
const projects = ref([])
const loadError = ref('')

async function LoadProjects() {
  loading.value = true
  loadError.value = ''
  try {
    const data = await GetProjects()
    projects.value = Array.isArray(data) ? data : []
  } catch (error) {
    const message = error instanceof Error ? error.message : '项目加载失败'
    loadError.value = message
    projects.value = []
    ElMessage.error('无法加载项目列表，请确认已登录并启动后端服务')
  } finally {
    loading.value = false
  }
}

function OpenProjectDetail(projectId) {
  router.push(`/projects/${projectId}`)
}

async function HandleLogout() {
  try {
    await DevLogout()
  } catch (_error) {
    // Logout should still continue on frontend even if backend request fails.
  } finally {
    localStorage.removeItem('aits_logged_in')
    ElMessage.success('已退出登录')
    await router.replace('/login')
  }
}

onMounted(async () => {
  await LoadProjects()
})
</script>

<template>
  <main class="page">
    <div class="page-header">
      <h2>我的项目</h2>
      <div class="header-actions">
        <el-button :loading="loading" type="primary" @click="LoadProjects">刷新</el-button>
        <el-button type="danger" plain @click="HandleLogout">退出登录</el-button>
      </div>
    </div>

    <el-alert
      v-if="loadError"
      :title="loadError"
      type="error"
      :closable="false"
      show-icon
    />

    <el-empty v-else-if="!loading && projects.length === 0" description="暂无项目" />

    <el-row v-else :gutter="16">
      <el-col v-for="project in projects" :key="project.id" :span="8">
        <el-card class="project-card" shadow="hover" @click="OpenProjectDetail(project.id)">
          <h3>{{ project.name }}</h3>
          <p class="project-description">{{ project.description || '暂无描述' }}</p>
          <div class="project-meta">ID: {{ project.id }}</div>
        </el-card>
      </el-col>
    </el-row>
  </main>
</template>

<style scoped>
.header-actions {
  display: flex;
  gap: 8px;
}
</style>
