import axios from 'axios'

export const httpClient = axios.create({
  baseURL: '/api',
  timeout: 10000,
  withCredentials: true,
  xsrfCookieName: 'csrftoken',
  xsrfHeaderName: 'X-CSRFToken',
})
