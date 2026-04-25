<template>
  <div class="min-h-screen bg-background">
    <NavBar />

    <main class="container mx-auto px-4 py-8 max-w-5xl">
      <div class="mb-6">
        <h1 class="text-2xl font-bold tracking-tight">Admin Panel</h1>
        <p class="text-sm text-muted-foreground mt-0.5">All sessions across all users</p>
      </div>

      <!-- Filters -->
      <div class="flex gap-3 mb-6">
        <select v-model="statusFilter" class="h-9 rounded-md border border-input bg-background px-3 text-sm focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring">
          <option value="">All statuses</option>
          <option value="active">Active</option>
          <option value="complete">Complete</option>
        </select>
        <Input v-model="search" placeholder="Search by title…" class="h-9 max-w-xs" />
      </div>

      <!-- Loading -->
      <div v-if="loading" class="space-y-2">
        <div v-for="i in 5" :key="i" class="h-14 rounded-lg bg-muted animate-pulse" />
      </div>

      <!-- Table -->
      <div v-else class="border rounded-lg overflow-hidden">
        <table class="w-full text-sm">
          <thead class="bg-muted/50">
            <tr>
              <th class="text-left px-4 py-3 font-medium text-muted-foreground">Session</th>
              <th class="text-left px-4 py-3 font-medium text-muted-foreground hidden md:table-cell">Status</th>
              <th class="text-left px-4 py-3 font-medium text-muted-foreground hidden lg:table-cell">Updated</th>
              <th class="px-4 py-3"></th>
            </tr>
          </thead>
          <tbody class="divide-y">
            <tr v-if="filtered.length === 0">
              <td colspan="4" class="text-center py-12 text-muted-foreground">No sessions found</td>
            </tr>
            <tr
              v-for="s in filtered"
              :key="s.id"
              class="hover:bg-muted/30 transition-colors cursor-pointer"
              @click="openSession(s.id)"
            >
              <td class="px-4 py-3">
                <p class="font-medium truncate max-w-xs">{{ s.title }}</p>
              </td>
              <td class="px-4 py-3 hidden md:table-cell">
                <Badge :variant="s.status === 'complete' ? 'default' : 'secondary'">{{ s.status }}</Badge>
              </td>
              <td class="px-4 py-3 text-muted-foreground hidden lg:table-cell">{{ formatDate(s.updated_at) }}</td>
              <td class="px-4 py-3 text-right">
                <ChevronRight class="w-4 h-4 text-muted-foreground inline" />
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </main>

    <!-- Detail drawer -->
    <Transition name="slide">
      <div v-if="detail" class="fixed inset-y-0 right-0 w-full sm:w-[600px] bg-background border-l shadow-xl z-50 flex flex-col">
        <div class="flex items-center justify-between px-6 py-4 border-b shrink-0">
          <div class="min-w-0">
            <h2 class="font-semibold truncate">{{ detail.title }}</h2>
            <p class="text-xs text-muted-foreground">Session #{{ detail.id }} · {{ detail.user?.email }}</p>
          </div>
          <Button variant="ghost" size="icon" @click="detail = null">
            <X class="w-4 h-4" />
          </Button>
        </div>

        <div class="flex-1 overflow-y-auto p-6 space-y-6">
          <!-- Tech stack suggestions -->
          <div v-if="detail.tech_stack">
            <h3 class="font-semibold text-sm mb-2 flex items-center gap-2">
              <Cpu class="w-4 h-4" /> Tech Stack Suggestions
            </h3>
            <Card class="p-4 text-sm space-y-2">
              <p v-if="detail.tech_stack.rationale" class="text-muted-foreground italic">{{ detail.tech_stack.rationale }}</p>
              <div v-if="detail.tech_stack.frontend"><span class="font-medium">Frontend:</span> {{ detail.tech_stack.frontend }}</div>
              <div v-if="detail.tech_stack.backend"><span class="font-medium">Backend:</span> {{ detail.tech_stack.backend }}</div>
              <div v-if="detail.tech_stack.database"><span class="font-medium">Database:</span> {{ detail.tech_stack.database }}</div>
              <div v-if="detail.tech_stack.hosting"><span class="font-medium">Hosting:</span> {{ detail.tech_stack.hosting }}</div>
              <div v-if="detail.tech_stack.other?.length">
                <span class="font-medium">Other:</span> {{ detail.tech_stack.other.join(', ') }}
              </div>
            </Card>
          </div>

          <!-- Transcript -->
          <div>
            <h3 class="font-semibold text-sm mb-3 flex items-center gap-2">
              <MessageSquare class="w-4 h-4" /> Full Transcript
            </h3>
            <div class="space-y-3">
              <div
                v-for="msg in detail.messages"
                :key="msg.id"
                :class="['text-sm rounded-lg px-3 py-2.5', msg.role === 'user' ? 'bg-primary/10 ml-8' : 'bg-muted mr-8']"
              >
                <p class="text-xs font-semibold mb-1 text-muted-foreground uppercase tracking-wide">{{ msg.role }}</p>
                <p class="whitespace-pre-wrap leading-relaxed">{{ msg.content }}</p>
                <p class="text-xs text-muted-foreground mt-1.5">{{ formatDate(msg.created_at) }}</p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </Transition>
    <div v-if="detail" class="fixed inset-0 bg-black/20 z-40" @click="detail = null" />
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { ChevronRight, X, Cpu, MessageSquare } from 'lucide-vue-next'
import { adminApi, type Session } from '@/lib/api'
import NavBar from '@/components/NavBar.vue'
import Button from '@/components/ui/Button.vue'
import Card from '@/components/ui/Card.vue'
import Input from '@/components/ui/Input.vue'
import Badge from '@/components/ui/Badge.vue'

const sessions = ref<Session[]>([])
const loading = ref(false)
const statusFilter = ref('')
const search = ref('')
const detail = ref<any>(null)

onMounted(loadSessions)

async function loadSessions() {
  loading.value = true
  try {
    const params: any = {}
    if (statusFilter.value) params.status = statusFilter.value
    const res = await adminApi.listSessions(params)
    sessions.value = res.data
  } finally {
    loading.value = false
  }
}

const filtered = computed(() => {
  let list = sessions.value
  if (statusFilter.value) list = list.filter(s => s.status === statusFilter.value)
  if (search.value) list = list.filter(s => s.title.toLowerCase().includes(search.value.toLowerCase()))
  return list
})

async function openSession(id: number) {
  const res = await adminApi.getSession(id)
  detail.value = res.data
}

function formatDate(iso: string) {
  return new Date(iso).toLocaleString(undefined, { dateStyle: 'medium', timeStyle: 'short' })
}
</script>

<style scoped>
.slide-enter-active, .slide-leave-active { transition: transform 0.25s ease; }
.slide-enter-from, .slide-leave-to { transform: translateX(100%); }
</style>
