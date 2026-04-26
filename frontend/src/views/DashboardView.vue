<template>
  <div class="min-h-screen bg-background">
    <NavBar />

    <main class="container mx-auto px-4 py-8 max-w-3xl">
      <div class="flex items-center justify-between mb-6">
        <div>
          <h1 class="text-2xl font-bold tracking-tight">My Sessions</h1>
          <p class="text-sm text-muted-foreground mt-0.5">Each session captures requirements for one application idea.</p>
        </div>
        <Button @click="newSession" :disabled="creating">
          <Plus class="w-4 h-4" />
          New Session
        </Button>
      </div>

      <!-- Error banner -->
      <div v-if="createError" class="mb-4 rounded-md bg-destructive/10 border border-destructive/30 px-4 py-3 text-sm text-destructive">
        {{ createError }}
      </div>

      <!-- Loading -->
      <div v-if="sessions.loading" class="space-y-3">
        <div v-for="i in 3" :key="i" class="h-20 rounded-lg bg-muted animate-pulse" />
      </div>

      <!-- Empty state -->
      <div v-else-if="sessions.sessions.length === 0" class="text-center py-16 text-muted-foreground">
        <FileText class="w-12 h-12 mx-auto mb-3 opacity-30" />
        <p class="font-medium">No sessions yet</p>
        <p class="text-sm mt-1">Click "New Session" to start gathering requirements for your first app idea.</p>
      </div>

      <!-- Session list -->
      <div v-else class="space-y-3">
        <Card
          v-for="session in sessions.sessions"
          :key="session.id"
          class="p-4 flex items-center justify-between hover:bg-accent/30 transition-colors cursor-pointer"
          @click="router.push(`/sessions/${session.id}`)"
        >
          <div class="min-w-0 flex-1">
            <div class="flex items-center gap-2">
              <p class="font-medium text-sm truncate">{{ session.title }}</p>
              <Badge :variant="session.status === 'complete' ? 'default' : 'secondary'" class="shrink-0">
                {{ session.status }}
              </Badge>
              <Badge v-if="session.has_pdf" variant="outline" class="shrink-0 gap-1">
                <FileDown class="w-3 h-3" /> PDF
              </Badge>
            </div>
            <p class="text-xs text-muted-foreground mt-0.5">{{ formatDate(session.updated_at) }}</p>
          </div>
          <ChevronRight class="w-4 h-4 text-muted-foreground shrink-0 ml-3" />
        </Card>
      </div>
    </main>
  </div>
</template>

<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { Plus, ChevronRight, FileText, FileDown } from 'lucide-vue-next'
import { useSessionsStore } from '@/stores/sessions'
import NavBar from '@/components/NavBar.vue'
import Button from '@/components/ui/Button.vue'
import Card from '@/components/ui/Card.vue'
import Badge from '@/components/ui/Badge.vue'

const sessions = useSessionsStore()
const router = useRouter()
const creating = ref(false)
const createError = ref<string | null>(null)

onMounted(() => sessions.loadSessions())

async function newSession() {
  creating.value = true
  createError.value = null
  try {
    const session = await sessions.createSession()
    router.push(`/sessions/${session.id}`)
  } catch (e: any) {
    createError.value = e?.message ?? 'Failed to create session. Please try again.'
  } finally {
    creating.value = false
  }
}

function formatDate(iso: string) {
  const normalized = iso.replace(' ', 'T')
  const d = new Date(normalized)
  if (isNaN(d.getTime())) return iso
  return d.toLocaleString(undefined, { dateStyle: 'medium', timeStyle: 'short' })
}
</script>
