import axios from 'axios'

const baseURL = process.env.NEXT_PUBLIC_API_BASE_URL ?? 'http://localhost:8000'

export const api = axios.create({
  baseURL,
})

api.interceptors.request.use((config) => {
  if (typeof window !== 'undefined') {
    const token = localStorage.getItem('access_token')
    if (token) {
      config.headers.Authorization = 'Bearer ' + token
    }
  }
  return config
})
