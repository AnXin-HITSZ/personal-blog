<script setup lang="ts">
const year = new Date().getFullYear()
</script>

<template>
  <footer class="border-t border-gray-100 bg-white mt-auto">
    <div class="max-w-6xl mx-auto px-4 py-8 text-center text-sm text-gray-400">
      <p class="mb-1">© {{ year }} AnXin Blog. All rights reserved.</p>
      <p class="text-gray-300">用代码记录思考，用文字沉淀成长</p>
    </div>
  </footer>
</template>
