<script setup>
import { ElMessage } from 'element-plus'
import { onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'

import { GetProjectDetail } from '../api/projects'

const route = useRoute()
const router = useRouter()
const loading = ref(false)
const project = ref(null)
const loadError = ref('')

async function LoadProject() {
  loading.value = true
  loadError.value = ''
  try {
    project.value = await GetProjectDetail(route.params.id)
  } catch (error) {
    const message = error instanceof Error ? error.message : '项目详情加载失败'
    loadError.value = message
    project.value = null
    ElMessage.error('无法加载项目详情')
  } finally {
    loading.value = false
  }
}

function BackToProjects() {
  router.push('/projects')
}

function GoToApiCases() {
  router.push(`/projects/${route.params.id}/api-cases`)
}

function GoToUiCases() {
  router.push(`/projects/${route.params.id}/ui-cases`)
}

function GoToExecutions() {
  router.push(`/projects/${route.params.id}/executions`)
}

onMounted(async () => {
  await LoadProject()
})
</script>

<template>
  <main class="page">
    <div class="page-header">
      <h2>项目详情</h2>
      <div>
        <el-button @click="BackToProjects">返回项目列表</el-button>
        <el-button @click="GoToApiCases">进入 API 用例管理</el-button>
        <el-button @click="GoToUiCases">进入 UI 用例管理</el-button>
        <el-button type="primary" @click="GoToExecutions">进入执行与报告</el-button>
      </div>
    </div>

    <el-skeleton v-if="loading" :rows="4" animated />

    <el-alert
      v-else-if="loadError"
      :title="loadError"
      type="error"
      :closable="false"
      show-icon
    />

    <el-card v-else-if="project">
      <p><strong>ID：</strong>{{ project.id }}</p>
      <p><strong>名称：</strong>{{ project.name }}</p>
      <p><strong>描述：</strong>{{ project.description || '暂无描述' }}</p>
      <p><strong>Owner：</strong>{{ project.owner }}</p>
    </el-card>
  </main>
</template>
