import { httpClient } from './http'

export async function GetUiTestCases(projectId) {
  const response = await httpClient.get('/ui-test-cases/', {
    params: { project: projectId },
  })
  return response.data
}

export async function CreateUiTestCase(payload) {
  const response = await httpClient.post('/ui-test-cases/', payload)
  return response.data
}

export async function UpdateUiTestCase(caseId, payload) {
  const response = await httpClient.put(`/ui-test-cases/${caseId}/`, payload)
  return response.data
}

export async function DeleteUiTestCase(caseId) {
  await httpClient.delete(`/ui-test-cases/${caseId}/`)
}
