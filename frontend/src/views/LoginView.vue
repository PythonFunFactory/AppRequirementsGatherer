<template>
  <div class="min-h-screen flex items-center justify-center bg-background px-4">
    <div class="w-full max-w-sm space-y-6">
      <!-- Logo / Title -->
      <div class="text-center space-y-2">
        <div class="inline-flex items-center justify-center w-12 h-12 rounded-xl bg-primary text-primary-foreground mb-2">
          <FileText class="w-6 h-6" />
        </div>
        <h1 class="text-2xl font-bold tracking-tight">Requirements Gatherer</h1>
        <p class="text-sm text-muted-foreground">Sign in to start capturing app requirements</p>
      </div>

      <!-- Dev mode login -->
      <template v-if="devAuth">
        <Card class="p-6 space-y-4">
          <div class="space-y-1">
            <label class="text-sm font-medium">Email</label>
            <Input v-model="devEmail" type="email" placeholder="you@example.com" @keyup.enter="handleDevLogin" />
          </div>
          <div class="space-y-1">
            <label class="text-sm font-medium">Display Name</label>
            <Input v-model="devName" placeholder="Your name" @keyup.enter="handleDevLogin" />
          </div>
          <div class="space-y-1">
            <label class="text-sm font-medium">Role</label>
            <select v-model="devRole" class="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring">
              <option value="user">User</option>
              <option value="admin">Admin</option>
            </select>
          </div>
          <Button class="w-full" :disabled="loading" @click="handleDevLogin">
            <Loader2 v-if="loading" class="w-4 h-4 animate-spin" />
            Sign in (Dev Mode)
          </Button>
          <p v-if="error" class="text-sm text-destructive text-center">{{ error }}</p>
        </Card>
        <p class="text-xs text-center text-muted-foreground">
          Dev mode is active. Set <code class="bg-muted px-1 rounded">DEV_AUTH=false</code> to enable Entra ID.
        </p>
      </template>

      <!-- Production Entra ID login -->
      <template v-else>
        <Card class="p-6">
          <Button class="w-full" @click="entraLogin">
            <img src="https://authjs.dev/img/providers/microsoft-entra-id.svg" class="w-4 h-4" alt="Microsoft" />
            Sign in with Microsoft
          </Button>
        </Card>
      </template>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { FileText, Loader2 } from 'lucide-vue-next'
import { useAuthStore } from '@/stores/auth'
import Button from '@/components/ui/Button.vue'
import Input from '@/components/ui/Input.vue'
import Card from '@/components/ui/Card.vue'

const devAuth = import.meta.env.VITE_DEV_AUTH === 'true' || true // default true until env is set
const auth = useAuthStore()
const router = useRouter()

const devEmail = ref('')
const devName = ref('Dev User')
const devRole = ref('user')
const loading = ref(false)
const error = ref('')

async function handleDevLogin() {
  if (!devEmail.value) { error.value = 'Email is required'; return }
  loading.value = true
  error.value = ''
  try {
    await auth.devLogin(devEmail.value, devName.value, devRole.value)
    router.push('/')
  } catch (e: any) {
    error.value = e?.response?.data?.detail || 'Login failed'
  } finally {
    loading.value = false
  }
}

function entraLogin() {
  window.location.href = '/auth/login'
}
</script>
