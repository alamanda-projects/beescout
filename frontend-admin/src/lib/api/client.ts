import axios from 'axios'

const apiBase = process.env.NEXT_PUBLIC_API_BASE || '/api'

export const apiClient = axios.create({
  baseURL: apiBase,
  withCredentials: true,
  headers: { 'Content-Type': 'application/json' },
})

let isRedirecting = false

apiClient.interceptors.response.use(
  (response) => response,
  async (error) => {
    if (
      error.response?.status === 401 &&
      typeof window !== 'undefined' &&
      !isRedirecting &&
      !window.location.pathname.includes('/login')
    ) {
      isRedirecting = true
      // Pakai apiBase yang sama dgn axios client — relatif '/api/logout' hanya
      // benar di prod (nginx). Di dev (tanpa nginx) URL relatif nyasar ke Next.js
      // server → 404 → cookie tak terhapus → infinite redirect loop.
      await fetch(`${apiBase}/logout`, { method: 'POST', credentials: 'include' }).catch(() => {})
      window.location.href = '/login'
    }
    return Promise.reject(error)
  }
)
