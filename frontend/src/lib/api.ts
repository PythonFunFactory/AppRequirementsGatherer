import axios from 'axios'

const api = axios.create({
  baseURL: '/',
  withCredentials: true,
})

export interface User {
  id: number
  email: string
  display_name: string
  role: 'user' | 'admin'
  created_at: string
}

export interface Session {
  id: number
  title: string
  status: 'active' | 'complete'
  created_at: string
  updated_at: string
  has_pdf: boolean
}

export interface Message {
  id: number
  role: 'user' | 'assistant'
  content: string
  created_at: string
}

export interface SessionDetail extends Session {
  messages: Message[]
  user?: User
}

export const authApi = {
  me: () => api.get<User>('/auth/me'),
  devLogin: (email: string, display_name: string, role: string) =>
    api.post('/auth/dev-login', { email, display_name, role }),
  logout: () => api.post('/auth/logout'),
}

export const sessionsApi = {
  list: () => api.get<Session[]>('/sessions'),
  create: () => api.post<Session>('/sessions'),
  get: (id: number) => api.get<SessionDetail>(`/sessions/${id}`),
  delete: (id: number) => api.delete(`/sessions/${id}`),
  generatePdf: (id: number) => api.post(`/sessions/${id}/pdf`),
}

export const adminApi = {
  listSessions: (params?: { user_id?: number; status?: string }) =>
    api.get('/admin/sessions', { params }),
  getSession: (id: number) => api.get(`/admin/sessions/${id}`),
  listUsers: () => api.get<User[]>('/admin/users'),
}

export default api
