<template>
  <div class="min-h-screen bg-background flex flex-col">
    <NavBar />

    <div class="flex-1 flex flex-col container mx-auto max-w-3xl px-4">
      <!-- Session header -->
      <div class="py-4 flex items-center justify-between border-b shrink-0">
        <div class="flex items-center gap-3 min-w-0">
          <Button variant="ghost" size="icon" @click="router.push('/')">
            <ArrowLeft class="w-4 h-4" />
          </Button>
          <div class="min-w-0">
            <p class="font-medium text-sm truncate">{{ session?.title || 'New Session' }}</p>
            <p class="text-xs text-muted-foreground">
              <Badge :variant="session?.status === 'complete' ? 'default' : 'secondary'" class="mr-1">{{ session?.status || 'active' }}</Badge>
              {{ session ? formatDate(session.updated_at) : '' }}
            </p>
          </div>
        </div>
        <div class="flex items-center gap-2 shrink-0">
          <Button
            v-if="session?.has_pdf"
            variant="outline"
            size="sm"
            @click="downloadPdf"
          >
            <FileDown class="w-4 h-4" />
            Download PDF
          </Button>
          <Button
            size="sm"
            :disabled="generatingPdf || messages.length === 0"
            @click="generatePdf"
          >
            <Loader2 v-if="generatingPdf" class="w-4 h-4 animate-spin" />
            <FileText v-else class="w-4 h-4" />
            Generate PDF
          </Button>
        </div>
      </div>

      <!-- Error banner -->
      <div v-if="pdfError" class="mt-3 px-4 py-2.5 rounded-md bg-destructive/10 text-destructive text-sm flex items-center justify-between shrink-0">
        <span>{{ pdfError }}</span>
        <button class="ml-3 opacity-60 hover:opacity-100" @click="pdfError = ''">✕</button>
      </div>

      <!-- Messages area -->
      <div ref="scrollEl" class="flex-1 overflow-y-auto py-6 space-y-4">
        <!-- Welcome message when empty -->
        <div v-if="messages.length === 0 && !streaming" class="text-center py-12 text-muted-foreground">
          <Bot class="w-12 h-12 mx-auto mb-3 opacity-30" />
          <p class="font-medium text-foreground">Start describing your app idea</p>
          <p class="text-sm mt-1 max-w-md mx-auto">Tell me about the application you'd like to build — even a rough idea is a great start. I'll ask questions to help clarify the requirements.</p>
        </div>

        <ChatMessage v-for="msg in messages" :key="msg.id" :message="msg" />

        <!-- Streaming bubble -->
        <div v-if="streaming" class="flex gap-3 justify-start">
          <div class="shrink-0 w-8 h-8 rounded-full bg-primary flex items-center justify-center text-primary-foreground mt-0.5">
            <Bot class="w-4 h-4" />
          </div>
          <div class="max-w-[75%] rounded-2xl rounded-tl-sm px-4 py-3 text-sm bg-muted leading-relaxed">
            <span class="whitespace-pre-wrap">{{ streamBuffer }}</span>
            <span class="inline-block w-2 h-4 bg-foreground/60 ml-0.5 animate-pulse rounded-sm" />
          </div>
        </div>
      </div>

      <!-- Input area -->
      <div class="border-t py-4 shrink-0">
        <div class="flex gap-2 items-end">
          <Textarea
            v-model="input"
            placeholder="Describe your app or answer the question above…"
            class="min-h-[44px] max-h-40 resize-none"
            rows="1"
            @keydown.enter.exact.prevent="sendMessage"
            @input="autoResize"
            ref="textareaEl"
          />
          <Button size="icon" :disabled="!input.trim() || streaming" @click="sendMessage">
            <Send class="w-4 h-4" />
          </Button>
        </div>
        <p class="text-xs text-muted-foreground mt-2">Press Enter to send · Shift+Enter for new line</p>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, nextTick, watch } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { ArrowLeft, Bot, FileText, FileDown, Send, Loader2 } from 'lucide-vue-next'
import { useSessionsStore } from '@/stores/sessions'
import { sessionsApi, type Message } from '@/lib/api'
import NavBar from '@/components/NavBar.vue'
import ChatMessage from '@/components/ChatMessage.vue'
import Button from '@/components/ui/Button.vue'
import Badge from '@/components/ui/Badge.vue'
import Textarea from '@/components/ui/Textarea.vue'

const router = useRouter()
const route = useRoute()
const sessionStore = useSessionsStore()

const sessionId = Number(route.params.id)
const session = ref(sessionStore.currentSession)
const messages = ref<Message[]>([])
const input = ref('')
const streaming = ref(false)
const streamBuffer = ref('')
const generatingPdf = ref(false)
const pdfError = ref('')
const scrollEl = ref<HTMLElement>()
const textareaEl = ref<HTMLElement>()

onMounted(async () => {
  await sessionStore.loadSession(sessionId)
  session.value = sessionStore.currentSession
  messages.value = sessionStore.currentSession?.messages ?? []
  scrollToBottom()
})

function scrollToBottom() {
  nextTick(() => {
    if (scrollEl.value) scrollEl.value.scrollTop = scrollEl.value.scrollHeight
  })
}

watch(streamBuffer, scrollToBottom)

async function sendMessage() {
  const text = input.value.trim()
  if (!text || streaming.value) return

  input.value = ''
  streaming.value = true
  streamBuffer.value = ''

  // Optimistically add user message to UI
  const fakeUserMsg: Message = {
    id: Date.now(),
    role: 'user',
    content: text,
    created_at: new Date().toISOString(),
  }
  messages.value.push(fakeUserMsg)
  scrollToBottom()

  try {
    const response = await fetch(`/sessions/${sessionId}/messages`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      credentials: 'include',
      body: JSON.stringify({ content: text }),
    })

    if (!response.ok) throw new Error('Request failed')
    if (!response.body) throw new Error('No response body')

    const reader = response.body.getReader()
    const decoder = new TextDecoder()

    while (true) {
      const { done, value } = await reader.read()
      if (done) break
      const chunk = decoder.decode(value, { stream: true })
      for (const line of chunk.split('\n')) {
        if (line.startsWith('data: ')) {
          const payload = line.slice(6)
          if (payload === '[DONE]') {
            // Finalize: add complete assistant message
            const assistantMsg: Message = {
              id: Date.now() + 1,
              role: 'assistant',
              content: streamBuffer.value,
              created_at: new Date().toISOString(),
            }
            messages.value.push(assistantMsg)
            streamBuffer.value = ''
            streaming.value = false
            // Refresh session to get real message IDs and updated title
            await sessionStore.loadSession(sessionId)
            session.value = sessionStore.currentSession
            messages.value = sessionStore.currentSession?.messages ?? []
            scrollToBottom()
          } else {
            try {
              const data = JSON.parse(payload)
              if (data.text) streamBuffer.value += data.text
            } catch { /* ignore parse errors */ }
          }
        }
      }
    }
  } catch (err) {
    streaming.value = false
    streamBuffer.value = ''
    console.error('Send error:', err)
  }
}

async function generatePdf() {
  generatingPdf.value = true
  pdfError.value = ''
  try {
    await sessionsApi.generatePdf(sessionId)
    await sessionStore.loadSession(sessionId)
    session.value = sessionStore.currentSession
  } catch (e: any) {
    pdfError.value = e?.response?.data?.detail || 'PDF generation failed. Please try again.'
  } finally {
    generatingPdf.value = false
  }
}

function downloadPdf() {
  window.open(`/sessions/${sessionId}/pdf`, '_blank')
}

function formatDate(iso: string) {
  return new Date(iso).toLocaleString(undefined, { dateStyle: 'medium', timeStyle: 'short' })
}

function autoResize(e: Event) {
  const el = e.target as HTMLTextAreaElement
  el.style.height = 'auto'
  el.style.height = Math.min(el.scrollHeight, 160) + 'px'
}
</script>
