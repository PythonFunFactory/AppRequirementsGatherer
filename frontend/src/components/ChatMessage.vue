<template>
  <div :class="['flex gap-3', message.role === 'user' ? 'justify-end' : 'justify-start']">
    <!-- Assistant avatar -->
    <div v-if="message.role === 'assistant'" class="shrink-0 w-8 h-8 rounded-full bg-primary flex items-center justify-center text-primary-foreground mt-0.5">
      <Bot class="w-4 h-4" />
    </div>

    <!-- Bubble -->
    <div :class="[
      'max-w-[75%] rounded-2xl px-4 py-3 text-sm leading-relaxed',
      message.role === 'user'
        ? 'bg-primary text-primary-foreground rounded-tr-sm'
        : 'bg-muted text-foreground rounded-tl-sm'
    ]">
      <div class="whitespace-pre-wrap">{{ message.content }}</div>
      <div :class="['text-xs mt-1.5 opacity-60', message.role === 'user' ? 'text-right' : 'text-left']">
        {{ formatTime(message.created_at) }}
      </div>
    </div>

    <!-- User avatar -->
    <div v-if="message.role === 'user'" class="shrink-0 w-8 h-8 rounded-full bg-secondary flex items-center justify-center mt-0.5">
      <User class="w-4 h-4" />
    </div>
  </div>
</template>

<script setup lang="ts">
import { Bot, User } from 'lucide-vue-next'
import type { Message } from '@/lib/api'

defineProps<{ message: Message }>()

function formatTime(iso: string) {
  return new Date(iso).toLocaleTimeString(undefined, { hour: '2-digit', minute: '2-digit' })
}
</script>
