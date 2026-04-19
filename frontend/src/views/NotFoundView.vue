<template>
  <div class="min-h-screen flex items-center justify-center bg-gradient-to-br from-gray-50 to-gray-100">
    <div class="text-center">
      <h1 class="text-9xl font-bold text-gray-300">404</h1>
      <h2 class="text-3xl font-bold text-gray-800 mt-4">Page Not Found</h2>
      <p class="text-gray-600 mt-4 max-w-md mx-auto">
        The page you are looking for might have been removed, had its name changed, or is temporarily unavailable.
      </p>
      <div class="mt-8">
        <router-link to="/">
          <el-button type="primary" size="large" icon="House">
            Go back home
          </el-button>
        </router-link>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
</script>