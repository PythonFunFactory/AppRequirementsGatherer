<template>
  <header class="border-b bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60 sticky top-0 z-50">
    <div class="container mx-auto px-4 flex h-14 items-center justify-between">
      <RouterLink to="/" class="flex items-center gap-2 font-semibold text-sm">
        <FileText class="w-5 h-5" />
        Requirements Gatherer
      </RouterLink>

      <nav class="flex items-center gap-1">
        <RouterLink
          v-if="auth.isAdmin"
          to="/admin"
          class="text-sm text-muted-foreground hover:text-foreground px-3 py-1.5 rounded-md hover:bg-accent transition-colors"
        >
          Admin
        </RouterLink>
        <div class="flex items-center gap-2 ml-2 pl-2 border-l">
          <span class="text-sm text-muted-foreground hidden sm:block">{{ auth.user?.display_name }}</span>
          <Button variant="ghost" size="sm" @click="handleLogout">
            <LogOut class="w-4 h-4" />
          </Button>
        </div>
      </nav>
    </div>
  </header>
</template>

<script setup lang="ts">
import { RouterLink, useRouter } from 'vue-router'
import { FileText, LogOut } from 'lucide-vue-next'
import { useAuthStore } from '@/stores/auth'
import Button from '@/components/ui/Button.vue'

const auth = useAuthStore()
const router = useRouter()

async function handleLogout() {
  await auth.logout()
  router.push('/login')
}
</script>
