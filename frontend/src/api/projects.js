import { httpClient } from './http'

export async function GetProjects() {
  const response = await httpClient.get('/projects/')
  return response.data
}

export async function GetProjectDetail(projectId) {
  const response = await httpClient.get(`/projects/${projectId}/`)
  return response.data
}
