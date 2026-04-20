<template>
  <div class="min-h-screen bg-gradient-to-br from-gray-50 to-gray-100">
    <nav class="bg-white shadow-sm border-b border-gray-200">
      <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div class="flex justify-between h-16">
          <div class="flex items-center">
            <h1 class="text-2xl font-bold text-gray-900">Personal Blog</h1>
          </div>
          <div class="flex items-center space-x-4">
            <router-link to="/" class="text-gray-700 hover:text-gray-900 px-3 py-2 rounded-md text-sm font-medium">
              Home
            </router-link>
            <router-link to="/chat" class="text-gray-700 hover:text-gray-900 px-3 py-2 rounded-md text-sm font-medium">
              AI Chat
            </router-link>
            <router-link to="/profile" class="text-gray-700 hover:text-gray-900 px-3 py-2 rounded-md text-sm font-medium">
              Profile
            </router-link>
            <el-button type="primary" @click="handleLogout" class="ml-4">
              Logout
            </el-button>
          </div>
        </div>
      </div>
    </nav>

    <main class="max-w-7xl mx-auto py-12 px-4 sm:px-6 lg:px-8">
      <div class="text-center mb-12">
        <h2 class="text-4xl font-extrabold text-gray-900 sm:text-5xl">
          Welcome to Your Blog
        </h2>
        <p class="mt-4 text-xl text-gray-600">
          Share your thoughts and ideas with the world
        </p>
      </div>

      <div v-if="loading" class="text-center py-12">
        <p class="text-gray-500">Loading articles...</p>
      </div>
      <div v-else-if="articles.length === 0" class="text-center py-12">
        <p class="text-gray-500">No articles yet. Create your first article!</p>
      </div>
      <div v-else class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
        <!-- Article Cards -->
        <div v-for="article in articles" :key="article.articleId" class="bg-white rounded-lg shadow-md overflow-hidden hover:shadow-lg transition-shadow duration-300">
          <div class="p-6">
            <div class="flex items-center mb-4">
              <div class="h-10 w-10 rounded-full bg-gradient-to-r from-blue-500 to-purple-600 flex items-center justify-center text-white font-bold">
                {{ article.userId }}
              </div>
              <div class="ml-4">
                <h3 class="text-lg font-semibold text-gray-900">{{ article.title }}</h3>
                <p class="text-sm text-gray-500">Published on {{ article.createTime ? new Date(article.createTime).toLocaleDateString() : 'Unknown date' }}</p>
              </div>
            </div>
            <p class="text-gray-700 mb-4 line-clamp-3">
              {{ article.content.substring(0, 100) }}{{ article.content.length > 100 ? '...' : '' }}
            </p>
            <div class="flex justify-between items-center">
              <span class="inline-flex items-center px-3 py-1 rounded-full text-sm font-medium bg-blue-100 text-blue-800">
                Article
              </span>
              <div class="space-x-2">
                <el-button type="primary" size="small" @click="handleEditArticle(article)">
                  Edit
                </el-button>
                <el-button type="danger" size="small" @click="handleDeleteArticle(article.articleId!)">
                  Delete
                </el-button>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Create New Article Button -->
      <div class="mt-12 text-center">
        <el-button type="success" size="large" icon="Plus" class="px-8 py-3 text-lg" @click="handleCreateArticle">
          Create New Article
        </el-button>
      </div>

      <!-- Article Dialog -->
      <el-dialog v-model="showDialog" :title="dialogTitle" width="600px">
        <el-form :model="formData" label-width="80px">
          <el-form-item label="Title" required>
            <el-input v-model="formData.title" placeholder="Enter article title" />
          </el-form-item>
          <el-form-item label="Content" required>
            <el-input
              v-model="formData.content"
              type="textarea"
              :rows="8"
              placeholder="Enter article content"
            />
          </el-form-item>
        </el-form>
        <template #footer>
          <span class="dialog-footer">
            <el-button @click="showDialog = false">Cancel</el-button>
            <el-button type="primary" @click="handleSaveArticle">
              {{ editingArticleId ? 'Update' : 'Create' }}
            </el-button>
          </span>
        </template>
      </el-dialog>
    </main>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, reactive } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { getAllArticlesApi, deleteArticleApi, addArticleApi, editArticleApi } from '@/api/article'
import type { Article } from '@/types/api'

const router = useRouter()
const articles = ref<Article[]>([])
const loading = ref(false)

// dialog state
const showDialog = ref(false)
const dialogTitle = ref('Create Article')
const formData = reactive<Article>({
  title: '',
  content: ''
})
const editingArticleId = ref<number | null>(null)

const fetchArticles = async () => {
  loading.value = true
  try {
    const res = await getAllArticlesApi()
    if (res.success) {
      articles.value = res.data || []
    } else {
      ElMessage.error(res.errorMsg || 'Failed to fetch articles')
    }
  } catch (error) {
    ElMessage.error('Network error')
  } finally {
    loading.value = false
  }
}

const openCreateDialog = () => {
  dialogTitle.value = 'Create Article'
  editingArticleId.value = null
  formData.title = ''
  formData.content = ''
  showDialog.value = true
}

const openEditDialog = (article: Article) => {
  dialogTitle.value = 'Edit Article'
  editingArticleId.value = article.articleId || null
  formData.title = article.title
  formData.content = article.content
  showDialog.value = true
}

const handleSaveArticle = async () => {
  if (!formData.title.trim() || !formData.content.trim()) {
    ElMessage.warning('Please fill in title and content')
    return
  }

  try {
    let res
    if (editingArticleId.value) {
      // update existing article
      res = await editArticleApi({
        articleId: editingArticleId.value,
        title: formData.title,
        content: formData.content
      })
    } else {
      // create new article
      res = await addArticleApi({
        title: formData.title,
        content: formData.content
      })
    }

    if (res.success) {
      ElMessage.success(editingArticleId.value ? 'Article updated' : 'Article created')
      showDialog.value = false
      fetchArticles()
    } else {
      ElMessage.error(res.errorMsg || 'Operation failed')
    }
  } catch (error) {
    ElMessage.error('Network error')
  }
}

const handleCreateArticle = openCreateDialog
const handleEditArticle = openEditDialog

const handleDeleteArticle = async (articleId: number) => {
  try {
    await ElMessageBox.confirm('Are you sure to delete this article?', 'Warning', {
      confirmButtonText: 'Delete',
      cancelButtonText: 'Cancel',
      type: 'warning',
    })
    const res = await deleteArticleApi(articleId)
    if (res.success) {
      ElMessage.success('Article deleted')
      fetchArticles()
    } else {
      ElMessage.error(res.errorMsg || 'Delete failed')
    }
  } catch (error) {
    // user cancelled
  }
}

const handleLogout = () => {
  localStorage.removeItem('token')
  ElMessage.success('Logged out successfully')
  router.push('/login')
}

onMounted(() => {
  fetchArticles()
})
</script>