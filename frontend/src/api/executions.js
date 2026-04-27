import { httpClient } from './http'

export async function CreateExecutionTask(payload) {
  const response = await httpClient.post('/executions/tasks/', payload)
  return response.data
}

export async function GetExecutionTaskResults(taskId) {
  const response = await httpClient.get(`/executions/tasks/${taskId}/results/`)
  return response.data
}
