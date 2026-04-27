import { httpClient } from './http'

export async function DevLogin(payload) {
  const response = await httpClient.post('/dev/login/', payload)
  return response.data
}

export async function DevLogout() {
  const response = await httpClient.post('/dev/logout/', {})
  return response.data
}
