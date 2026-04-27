<script setup>
import { ElMessage } from 'element-plus'
import { computed, onBeforeUnmount, onMounted, ref } from 'vue'
import { useRoute } from 'vue-router'

import { GetApiTestCases } from '../api/apitest'
import { CreateExecutionTask, GetExecutionTaskResults } from '../api/executions'
import { GetUiTestCases } from '../api/uitest'

const route = useRoute()
const projectId = computed(() => Number(route.params.id))

const loadingCases = ref(false)
const triggering = ref(false)
const polling = ref(false)
const apiCases = ref([])
const uiCases = ref([])
const selectedCaseIds = ref([])
const envIdInput = ref('')
const currentTaskId = ref(null)
const taskStatus = ref('idle')
const taskSummary = ref(null)
const resultRows = ref([])

let pollTimer = null

function BuildCaseOptionList(cases, prefix) {
  return cases.map((item) => ({
    label: `[${prefix.toUpperCase()}] ${item.title} (${item.path || '-'})`,
    value: `${prefix}:${item.id}`,
  }))
}

const allCaseOptions = computed(() => [
  ...BuildCaseOptionList(apiCases.value, 'api'),
  ...BuildCaseOptionList(uiCases.value, 'ui'),
])

async function LoadCases() {
  loadingCases.value = true
  try {
    const [apiData, uiData] = await Promise.all([
      GetApiTestCases(projectId.value),
      GetUiTestCases(projectId.value),
    ])
    apiCases.value = Array.isArray(apiData) ? apiData : []
    uiCases.value = Array.isArray(uiData) ? uiData : []
  } catch (error) {
    const message = error instanceof Error ? error.message : '加载用例失败'
    ElMessage.error(`加载用例失败: ${message}`)
  } finally {
    loadingCases.value = false
  }
}

async function TriggerExecution() {
  if (selectedCaseIds.value.length === 0) {
    ElMessage.warning('请至少选择一个用例')
    return
  }

  triggering.value = true
  try {
    const payload = {
      project_id: projectId.value,
      case_ids: selectedCaseIds.value,
      env_id: envIdInput.value ? Number(envIdInput.value) : null,
    }
    const data = await CreateExecutionTask(payload)
    currentTaskId.value = data.task_id
    taskStatus.value = data.status
    taskSummary.value = null
    resultRows.value = []
    StartPolling()
    ElMessage.success(`执行任务已触发，任务ID: ${data.task_id}`)
  } catch (error) {
    const message = error instanceof Error ? error.message : '触发执行失败'
    ElMessage.error(`触发执行失败: ${message}`)
  } finally {
    triggering.value = false
  }
}

function StopPolling() {
  if (pollTimer) {
    clearInterval(pollTimer)
    pollTimer = null
  }
  polling.value = false
}

function StartPolling() {
  StopPolling()
  polling.value = true
  void RefreshTaskResult()
  pollTimer = setInterval(() => {
    void RefreshTaskResult()
  }, 3000)
}

async function RefreshTaskResult() {
  if (!currentTaskId.value) return
  try {
    const data = await GetExecutionTaskResults(currentTaskId.value)
    taskStatus.value = data.status
    taskSummary.value = data.summary
    resultRows.value = Array.isArray(data.results) ? data.results : []

    if (data.status === 'finished') {
      StopPolling()
    }
  } catch (error) {
    const message = error instanceof Error ? error.message : '拉取结果失败'
    ElMessage.error(`拉取结果失败: ${message}`)
    StopPolling()
  }
}

function FormatScreenshots(row) {
  if (!Array.isArray(row.screenshots) || row.screenshots.length === 0) {
    return []
  }
  return row.screenshots
}

onMounted(async () => {
  await LoadCases()
})

onBeforeUnmount(() => {
  StopPolling()
})
</script>

<template>
  <main class="page">
    <div class="page-header">
      <h2>执行与报告</h2>
      <el-button :loading="loadingCases" @click="LoadCases">刷新用例</el-button>
    </div>

    <el-card class="mb-12">
      <template #header>
        <span>执行参数</span>
      </template>

      <el-form label-width="100px">
        <el-form-item label="选择用例">
          <el-select
            v-model="selectedCaseIds"
            multiple
            filterable
            clearable
            placeholder="请选择 API/UI 用例"
            style="width: 100%"
          >
            <el-option
              v-for="option in allCaseOptions"
              :key="option.value"
              :label="option.label"
              :value="option.value"
            />
          </el-select>
        </el-form-item>

        <el-form-item label="环境ID">
          <el-input v-model="envIdInput" placeholder="可选，例如 1" />
        </el-form-item>

        <el-form-item>
          <el-button :loading="triggering" type="primary" @click="TriggerExecution">开始执行</el-button>
          <el-button
            v-if="currentTaskId"
            :loading="polling"
            @click="RefreshTaskResult"
          >
            手动刷新结果
          </el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <el-card v-if="currentTaskId" class="mb-12">
      <template #header>
        <span>任务状态</span>
      </template>
      <p><strong>任务ID：</strong>{{ currentTaskId }}</p>
      <p><strong>状态：</strong>{{ taskStatus }}</p>
      <p v-if="taskSummary"><strong>摘要：</strong>{{ taskSummary }}</p>
    </el-card>

    <el-card v-if="currentTaskId">
      <template #header>
        <span>执行结果</span>
      </template>

      <el-empty v-if="resultRows.length === 0" description="暂无结果，执行中请稍候" />

      <el-table v-else :data="resultRows" border>
        <el-table-column prop="id" label="结果ID" width="90" />
        <el-table-column prop="content_type" label="类型" width="100" />
        <el-table-column prop="object_id" label="用例ID" width="90" />
        <el-table-column prop="status" label="状态" width="90" />
        <el-table-column prop="duration" label="耗时(s)" width="100" />
        <el-table-column prop="logs" label="日志" min-width="280" show-overflow-tooltip />
        <el-table-column label="截图" min-width="220">
          <template #default="scope">
            <div v-if="FormatScreenshots(scope.row).length === 0">-</div>
            <div v-else>
              <a
                v-for="(path, index) in FormatScreenshots(scope.row)"
                :key="`${scope.row.id}-${index}`"
                :href="path"
                target="_blank"
              >
                截图{{ index + 1 }}
              </a>
            </div>
          </template>
        </el-table-column>
      </el-table>
    </el-card>
  </main>
</template>
