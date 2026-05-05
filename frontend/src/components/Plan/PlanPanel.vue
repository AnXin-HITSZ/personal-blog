<template>
  <div class="h-full flex flex-col">
    <!-- Header -->
    <div class="px-4 py-3 border-b border-gray-200/80 bg-white flex-shrink-0">
      <div class="flex items-center justify-between">
        <h3 class="text-xs font-bold text-gray-400 tracking-wider uppercase">Task Plan</h3>
        <el-button
          v-if="plan"
          type="danger"
          size="small"
          :icon="Delete"
          circle
          @click="handleDelete"
        />
      </div>
    </div>

    <!-- Plan Content -->
    <div class="flex-1 overflow-y-auto p-3 min-h-0">
      <!-- Empty state -->
      <div v-if="!plan" class="text-center py-8 text-gray-400">
        <svg class="w-10 h-10 mx-auto mb-2" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1">
          <path stroke-linecap="round" stroke-linejoin="round" d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2m-3 7h3m-3 4h3m-6-4h.01M9 16h.01" />
        </svg>
        <p class="text-sm">暂无计划</p>
        <p class="text-xs mt-1">AI 会自动为复杂任务创建计划</p>
      </div>

      <!-- Plan Tree -->
      <div v-else class="space-y-2">
        <!-- Main Goal -->
        <div
          class="px-3 py-2 rounded-lg bg-gradient-to-r from-blue-50 to-purple-50 border border-blue-100/60"
        >
          <div class="flex items-center gap-1.5 mb-0.5">
            <svg class="w-4 h-4 text-blue-500 shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
              <path stroke-linecap="round" stroke-linejoin="round" d="M13 10V3L4 14h7v7l9-11h-7z" />
            </svg>
            <span class="text-xs font-semibold text-gray-500">主目标</span>
          </div>
          <p class="text-sm font-medium text-gray-800 ml-5">{{ plan.mainGoal }}</p>
        </div>

        <!-- Root Task Tree -->
        <div v-if="plan.rootTask" class="ml-1">
          <div class="text-[11px] font-semibold text-gray-400 uppercase tracking-wider mb-1 px-1">任务分解</div>
          <PlanTaskNode :task="plan.rootTask" :depth="0" />
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { Delete } from '@element-plus/icons-vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { deletePlanApi } from '@/api/plan'
import type { Plan } from '@/types/api'
import PlanTaskNode from './PlanTaskNode.vue'

const props = defineProps<{
  plan: Plan | null
}>()

const emit = defineEmits<{
  delete: []
}>()

const handleDelete = async () => {
  if (!props.plan?.planId) return
  try {
    await ElMessageBox.confirm('确定删除当前计划吗？', '确认', {
      confirmButtonText: '删除',
      cancelButtonText: '取消',
      type: 'warning',
    })
    const res = await deletePlanApi(props.plan.planId)
    if (res.success) {
      ElMessage.success('计划已删除')
      emit('delete')
    }
  } catch {
    // cancelled
  }
}
</script>
