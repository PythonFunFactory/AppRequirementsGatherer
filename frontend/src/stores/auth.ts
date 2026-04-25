import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { authApi, type User } from '@/lib/api'

export const useAuthStore = defineStore('auth', () => {
  const user = ref<User | null>(null)
  const loading = ref(false)

  const isAuthenticated = computed(() => user.value !== null)
  const isAdmin = computed(() => user.value?.role === 'admin')

  async function fetchMe() {
    loading.value = true
    try {
      const res = await authApi.me()
      user.value = res.data
    } catch {
      user.value = null
    } finally {
      loading.value = false
    }
  }

  async function devLogin(email: string, displayName: string, role: string) {
    await authApi.devLogin(email, displayName, role)
    await fetchMe()
  }

  async function logout() {
    await authApi.logout()
    user.value = null
  }

  return { user, loading, isAuthenticated, isAdmin, fetchMe, devLogin, logout }
})
