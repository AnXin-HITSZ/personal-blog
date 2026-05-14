import { createRouter, createWebHistory } from 'vue-router'
import { useUserStore } from '@/stores/user'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    {
      path: '/',
      name: 'Home',
      component: () => import('@/views/Home.vue'),
    },
    {
      path: '/qa',
      name: 'Qa',
      component: () => import('@/views/Qa.vue'),
    },
    {
      path: '/login',
      name: 'Login',
      component: () => import('@/views/Login.vue'),
    },
    {
      path: '/register',
      name: 'Register',
      component: () => import('@/views/Register.vue'),
    },
    {
      path: '/article/:id',
      name: 'ArticleDetail',
      component: () => import('@/views/ArticleDetail.vue'),
    },
    {
      path: '/admin',
      name: 'Admin',
      component: () => import('@/views/admin/Dashboard.vue'),
      meta: { requiresAuth: true },
    },
    {
      path: '/admin/editor/:id?',
      name: 'Editor',
      component: () => import('@/views/admin/Editor.vue'),
      meta: { requiresAuth: true },
    },
    {
      path: '/admin/knowledge-base',
      name: 'KnowledgeBase',
      component: () => import('@/views/admin/KnowledgeBase.vue'),
      meta: { requiresAuth: true },
    },
    {
      path: '/admin/deploy',
      name: 'DeployDashboard',
      component: () => import('@/views/admin/DeployDashboard.vue'),
      meta: { requiresAuth: true },
    },
  ],
})

router.beforeEach((to, _from) => {
  const store = useUserStore()
  if (to.meta.requiresAuth && !store.isLoggedIn) {
    return '/login'
  }
})

export default router
