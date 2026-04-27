<script setup>
import { ElMessage } from 'element-plus'
import { onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'

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

onMounted(async () => {
  await LoadProjects()
})
</script>

<template>
  <main class="page">
    <div class="page-header">
      <h2>我的项目</h2>
      <el-button :loading="loading" type="primary" @click="LoadProjects">刷新</el-button>
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
