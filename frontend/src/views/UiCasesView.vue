<script setup>
import { ElMessage, ElMessageBox } from 'element-plus'
import { computed, onMounted, reactive, ref } from 'vue'
import { useRoute } from 'vue-router'

import {
  CreateUiTestCase,
  DeleteUiTestCase,
  GetUiTestCases,
  UpdateUiTestCase,
} from '../api/uitest'
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
  script: 'def test_ui_example(page):\n    page.goto("https://example.com/login")\n    assert "login" in page.url',
  elements_snapshot: '{"loginButton": "button[type=submit]"}',
})

async function LoadCases() {
  loading.value = true
  try {
    const data = await GetUiTestCases(projectId.value)
    cases.value = Array.isArray(data) ? data : []
  } catch (error) {
    const message = error instanceof Error ? error.message : '加载失败'
    ElMessage.error(`加载 UI 用例失败: ${message}`)
  } finally {
    loading.value = false
  }
}

function ResetForm() {
  formState.title = ''
  formState.description = ''
  formState.status = 'draft'
  formState.script = 'def test_ui_example(page):\n    page.goto("https://example.com/login")\n    assert "login" in page.url'
  formState.elements_snapshot = '{"loginButton": "button[type=submit]"}'
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
  formState.script = row.script || ''
  formState.elements_snapshot = JSON.stringify(row.elements_snapshot || {}, null, 2)
  dialogVisible.value = true
}

function ParseElementsSnapshot() {
  try {
    return JSON.parse(formState.elements_snapshot || '{}')
  } catch {
    ElMessage.error('elements_snapshot 不是合法 JSON')
    throw new Error('invalid elements_snapshot json')
  }
}

async function SubmitCase() {
  submitLoading.value = true
  try {
    const payload = {
      project: projectId.value,
      title: formState.title,
      description: formState.description,
      status: formState.status,
      script: formState.script,
      elements_snapshot: ParseElementsSnapshot(),
    }

    if (editTargetId.value) {
      await UpdateUiTestCase(editTargetId.value, payload)
      ElMessage.success('更新成功')
    } else {
      await CreateUiTestCase(payload)
      ElMessage.success('创建成功')
    }
    dialogVisible.value = false
    await LoadCases()
  } catch (error) {
    if (error instanceof Error && error.message === 'invalid elements_snapshot json') {
      return
    }
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
    await DeleteUiTestCase(row.id)
    ElMessage.success('删除成功')
    await LoadCases()
  } catch {
    // ignore cancel
  }
}

onMounted(async () => {
  await LoadCases()
})
</script>

<template>
  <main class="page">
    <div class="page-header">
      <h2>UI 用例管理</h2>
      <div>
        <el-button :loading="loading" @click="LoadCases">刷新</el-button>
        <el-button type="primary" @click="OpenCreateDialog">新建 UI 用例</el-button>
      </div>
    </div>

    <el-table v-loading="loading" :data="cases" border>
      <el-table-column prop="id" label="ID" width="80" />
      <el-table-column prop="title" label="标题" min-width="220" />
      <el-table-column prop="status" label="状态" width="100" />
      <el-table-column label="脚本长度" width="120">
        <template #default="scope">{{ (scope.row.script || '').length }}</template>
      </el-table-column>
      <el-table-column label="操作" width="180" fixed="right">
        <template #default="scope">
          <el-button size="small" @click="OpenEditDialog(scope.row)">编辑</el-button>
          <el-button size="small" type="danger" @click="RemoveCase(scope.row)">删除</el-button>
        </template>
      </el-table-column>
    </el-table>

    <el-dialog v-model="dialogVisible" width="920px" :title="editTargetId ? '编辑 UI 用例' : '新建 UI 用例'">
      <el-form label-width="110px">
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
        <el-form-item label="UI 脚本">
          <MonacoEditor v-model="formState.script" :height="320" language="python" />
        </el-form-item>
        <el-form-item label="elements_snapshot(JSON)">
          <el-input v-model="formState.elements_snapshot" type="textarea" :rows="6" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button :loading="submitLoading" type="primary" @click="SubmitCase">保存</el-button>
      </template>
    </el-dialog>
  </main>
</template>
