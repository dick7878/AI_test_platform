import { httpClient } from './http'

export async function GetApiTestCases(projectId) {
  const response = await httpClient.get('/api-test-cases/', {
    params: { project: projectId },
  })
  return response.data
}

export async function CreateApiTestCase(payload) {
  const response = await httpClient.post('/api-test-cases/', payload)
  return response.data
}

export async function UpdateApiTestCase(caseId, payload) {
  const response = await httpClient.put(`/api-test-cases/${caseId}/`, payload)
  return response.data
}

export async function DeleteApiTestCase(caseId) {
  await httpClient.delete(`/api-test-cases/${caseId}/`)
}
