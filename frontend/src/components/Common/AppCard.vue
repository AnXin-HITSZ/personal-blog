<template>
  <div class="bg-white rounded-lg shadow-md overflow-hidden hover:shadow-lg transition-shadow duration-300" :class="customClass">
    <!-- Card Header -->
    <div v-if="$slots.header || title" class="px-6 py-4 border-b border-gray-200">
      <slot name="header">
        <h3 class="text-lg font-semibold text-gray-900">{{ title }}</h3>
        <p v-if="description" class="mt-1 text-sm text-gray-500">{{ description }}</p>
      </slot>
    </div>

    <!-- Card Content -->
    <div class="px-6 py-4">
      <slot></slot>
    </div>

    <!-- Card Footer -->
    <div v-if="$slots.footer" class="px-6 py-4 border-t border-gray-200 bg-gray-50">
      <slot name="footer"></slot>
    </div>
  </div>
</template>

<script setup lang="ts">
defineProps<{
  title?: string
  description?: string
  customClass?: string
}>()
</script>