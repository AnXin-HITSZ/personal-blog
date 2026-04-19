<template>
  <div class="bg-red-50 border border-red-200 rounded-lg p-4">
    <div class="flex">
      <div class="flex-shrink-0">
        <el-icon class="h-5 w-5 text-red-400"><Warning /></el-icon>
      </div>
      <div class="ml-3">
        <h3 class="text-sm font-medium text-red-800">{{ title }}</h3>
        <div class="mt-2 text-sm text-red-700">
          <slot>{{ message }}</slot>
        </div>
        <div v-if="retryable" class="mt-4">
          <div class="flex space-x-3">
            <el-button type="danger" size="small" @click="$emit('retry')">
              Try Again
            </el-button>
            <el-button type="text" size="small" @click="$emit('dismiss')">
              Dismiss
            </el-button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { Warning } from '@element-plus/icons-vue'

defineProps<{
  title?: string
  message?: string
  retryable?: boolean
}>()

defineEmits<{
  retry: []
  dismiss: []
}>()
</script>