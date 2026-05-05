<template>
  <div class="task-node">
    <div
      class="flex items-start gap-2 px-2 py-1.5 rounded-lg transition-colors cursor-pointer hover:bg-gray-50/80 group"
      :class="{ 'bg-amber-50/40': task.taskState === 'in_progress' }"
    >
      <!-- Toggle icon for non-leaf tasks -->
      <button
        v-if="task.subtasks && task.subtasks.length > 0"
        @click="collapsed = !collapsed"
        class="mt-0.5 shrink-0 w-4 h-4 flex items-center justify-center rounded hover:bg-gray-200 transition-colors"
      >
        <svg
          class="w-3 h-3 text-gray-400 transition-transform duration-150"
          :class="{ 'rotate-90': !collapsed }"
          viewBox="0 0 20 20"
          fill="currentColor"
        >
          <path fill-rule="evenodd" d="M7.293 14.707a1 1 0 010-1.414L10.586 10 7.293 6.707a1 1 0 011.414-1.414l4 4a1 1 0 010 1.414l-4 4a1 1 0 01-1.414 0z" clip-rule="evenodd" />
        </svg>
      </button>
      <div v-else class="w-4 shrink-0" />

      <!-- State icon -->
      <span class="mt-0.5 shrink-0 text-sm leading-tight">{{ stateIcon }}</span>

      <!-- Task content -->
      <div class="min-w-0 flex-1">
        <div class="flex items-center gap-1.5">
          <span
            class="text-xs font-mono text-gray-400 shrink-0"
          >{{ task.taskPath }}</span>
          <span
            class="text-[11px] px-1.5 py-0.5 rounded-full font-medium"
            :class="stateBadgeClass"
          >{{ task.taskState }}</span>
        </div>
        <p class="text-sm text-gray-700 mt-0.5 leading-relaxed break-words">{{ task.taskGoal }}</p>
      </div>
    </div>

    <!-- Subtasks -->
    <div v-if="!collapsed && task.subtasks && task.subtasks.length > 0" class="ml-4 border-l-2 border-gray-100 pl-1">
      <PlanTaskNode
        v-for="sub in task.subtasks"
        :key="sub.taskPath"
        :task="sub"
        :depth="depth + 1"
      />
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import type { PlanTask, TaskState } from '@/types/api'

const props = defineProps<{
  task: PlanTask
  depth: number
}>()

const collapsed = ref(props.depth >= 2) // auto-collapse beyond depth 2

const stateIcon = computed(() => {
  const icons: Record<TaskState, string> = {
    verified: '✅',
    completed: '🟢',
    abandoned: '❌',
    in_progress: '💪',
    open: '🔵',
  }
  return icons[props.task.taskState] || '🔵'
})

const stateBadgeClass = computed(() => {
  const map: Record<TaskState, string> = {
    verified: 'bg-green-100 text-green-700',
    completed: 'bg-emerald-100 text-emerald-700',
    abandoned: 'bg-red-100 text-red-700',
    in_progress: 'bg-amber-100 text-amber-700',
    open: 'bg-blue-100 text-blue-700',
  }
  return map[props.task.taskState] || 'bg-gray-100 text-gray-600'
})
</script>
