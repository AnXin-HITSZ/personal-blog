<template>
  <div class="flex items-center justify-center min-h-[200px]">
    <div class="text-center">
      <div class="inline-block animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-blue-600"></div>
      <p v-if="message" class="mt-4 text-gray-600">{{ message }}</p>
      <p v-else class="mt-4 text-gray-600">Loading...</p>
    </div>
  </div>
</template>

<script setup lang="ts">
defineProps<{
  message?: string
}>()
</script>