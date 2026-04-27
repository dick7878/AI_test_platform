<script setup>
import { ElMessage, ElMessageBox } from 'element-plus'
import { computed, onMounted, reactive, ref } from 'vue'
import { useRoute } from 'vue-router'

import {
  CreateApiTestCase,
  DeleteApiTestCase,
  GetApiTestCases,
  UpdateApiTestCase,
} from '../api/apitest'
import MonacoEditor from '../components/MonacoEditor.vue'

const route = useRoute()
const projectId = computed(() => Number(route.params.id))

const loading = ref(false)
const cases = ref([])
const dialogVisible = ref(false)
const submitLoading = ref(false)
const editTargetId = ref(null)

const formState = reactive({
  title: '',
  description: '',
  status: 'draft',
  method: 'GET',
  path: '/',
  script: 'def test_example(api_client):\n    response = api_client.get("/")\n    assert response.status_code == 200',
})

async function LoadCases() {
  loading.value = true
  try {
    const data = await GetApiTestCases(projectId.value)
    cases.value = Array.isArray(data) ? data : []
  } catch (error) {
    const message = error instanceof Error ? error.message : '加载失败'
    ElMessage.error(`加载 API 用例失败: ${message}`)
  } finally {
    loading.value = false
  }
}

function ResetForm() {
  formState.title = ''
  formState.description = ''
  formState.status = 'draft'
  formState.method = 'GET'
  formState.path = '/'
  formState.script = 'def test_example(api_client):\n    response = api_client.get("/")\n    assert response.status_code == 200'
  editTargetId.value = null
}

function OpenCreateDialog() {
  ResetForm()
  dialogVisible.value = true
}

function OpenEditDialog(row) {
  editTargetId.value = row.id
  formState.title = row.title
  formState.description = row.description || ''
  formState.status = row.status || 'draft'
  formState.method = row.method || 'GET'
  formState.path = row.path || '/'
  formState.script = row.script || ''
  dialogVisible.value = true
}

async function SubmitCase() {
  submitLoading.value = true
  const payload = {
    project: projectId.value,
    title: formState.title,
    description: formState.description,
    status: formState.status,
    method: formState.method,
    path: formState.path,
    headers: {},
    query_params: {},
    body: '',
    script: formState.script,
  }

  try {
    if (editTargetId.value) {
      await UpdateApiTestCase(editTargetId.value, payload)
      ElMessage.success('更新成功')
    } else {
      await CreateApiTestCase(payload)
      ElMessage.success('创建成功')
    }
    dialogVisible.value = false
    await LoadCases()
  } catch (error) {
    const message = error instanceof Error ? error.message : '保存失败'
    ElMessage.error(`保存用例失败: ${message}`)
  } finally {
    submitLoading.value = false
  }
}

async function RemoveCase(row) {
  try {
    await ElMessageBox.confirm(`确认删除用例「${row.title}」吗？`, '删除确认', {
      type: 'warning',
    })
    await DeleteApiTestCase(row.id)
    ElMessage.success('删除成功')
    await LoadCases()
  } catch {
    // user cancelled or request failed already handled by message
  }
}

async function HandleRowContextmenu(row, _column, event) {
  event.preventDefault()
  const nextStatus = row.status === 'ready' ? 'draft' : 'ready'
  try {
    await UpdateApiTestCase(row.id, {
      ...row,
      project: projectId.value,
      status: nextStatus,
    })
    ElMessage.success(`状态已切换为 ${nextStatus}`)
    await LoadCases()
  } catch (error) {
    const message = error instanceof Error ? error.message : '状态更新失败'
    ElMessage.error(message)
  }
}

onMounted(async () => {
  await LoadCases()
})
</script>

<template>
  <main class="page">
    <div class="page-header">
      <h2>API 用例管理</h2>
      <div>
        <el-button :loading="loading" @click="LoadCases">刷新</el-button>
        <el-button type="primary" @click="OpenCreateDialog">新建用例</el-button>
      </div>
    </div>

    <el-alert
      title="提示：在表格行上点击鼠标右键，可快速切换 draft/ready 状态"
      type="info"
      :closable="false"
      show-icon
      class="mb-12"
    />

    <el-table
      v-loading="loading"
      :data="cases"
      border
      @row-contextmenu="HandleRowContextmenu"
    >
      <el-table-column prop="id" label="ID" width="80" />
      <el-table-column prop="title" label="标题" min-width="200" />
      <el-table-column prop="method" label="Method" width="100" />
      <el-table-column prop="path" label="Path" min-width="180" />
      <el-table-column prop="status" label="状态" width="110" />
      <el-table-column label="操作" width="180" fixed="right">
        <template #default="scope">
          <el-button size="small" @click="OpenEditDialog(scope.row)">编辑</el-button>
          <el-button size="small" type="danger" @click="RemoveCase(scope.row)">删除</el-button>
        </template>
      </el-table-column>
    </el-table>

    <el-dialog v-model="dialogVisible" width="900px" :title="editTargetId ? '编辑用例' : '新建用例'">
      <el-form label-width="90px">
        <el-form-item label="标题">
          <el-input v-model="formState.title" />
        </el-form-item>
        <el-form-item label="描述">
          <el-input v-model="formState.description" type="textarea" rows="2" />
        </el-form-item>
        <el-form-item label="状态">
          <el-select v-model="formState.status" style="width: 180px">
            <el-option label="draft" value="draft" />
            <el-option label="ready" value="ready" />
          </el-select>
        </el-form-item>
        <el-form-item label="Method">
          <el-select v-model="formState.method" style="width: 180px">
            <el-option label="GET" value="GET" />
            <el-option label="POST" value="POST" />
            <el-option label="PUT" value="PUT" />
            <el-option label="PATCH" value="PATCH" />
            <el-option label="DELETE" value="DELETE" />
          </el-select>
        </el-form-item>
        <el-form-item label="Path">
          <el-input v-model="formState.path" />
        </el-form-item>
        <el-form-item label="脚本">
          <MonacoEditor v-model="formState.script" :height="320" language="python" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button :loading="submitLoading" type="primary" @click="SubmitCase">保存</el-button>
      </template>
    </el-dialog>
  </main>
</template>
