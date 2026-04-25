import { defineStore } from 'pinia'
import { ref } from 'vue'
import { sessionsApi, type Session, type SessionDetail } from '@/lib/api'

export const useSessionsStore = defineStore('sessions', () => {
  const sessions = ref<Session[]>([])
  const currentSession = ref<SessionDetail | null>(null)
  const loading = ref(false)

  async function loadSessions() {
    loading.value = true
    try {
      const res = await sessionsApi.list()
      sessions.value = res.data
    } finally {
      loading.value = false
    }
  }

  async function createSession(): Promise<Session> {
    const res = await sessionsApi.create()
    sessions.value.unshift(res.data)
    return res.data
  }

  async function loadSession(id: number) {
    loading.value = true
    try {
      const res = await sessionsApi.get(id)
      currentSession.value = res.data
    } finally {
      loading.value = false
    }
  }

  async function deleteSession(id: number) {
    await sessionsApi.delete(id)
    sessions.value = sessions.value.filter(s => s.id !== id)
    if (currentSession.value?.id === id) currentSession.value = null
  }

  return { sessions, currentSession, loading, loadSessions, createSession, loadSession, deleteSession }
})
