import request from './request'
import type { ApiResult, Article } from '@/types'

export function getArticlesApi(): Promise<ApiResult<Article[]>> {
  return request.get('/api/article/all').then((r) => r.data)
}

export function addArticleApi(data: Article): Promise<ApiResult<Article>> {
  return request.post('/api/article/add', data).then((r) => r.data)
}

export function updateArticleApi(data: Article): Promise<ApiResult<null>> {
  return request.put('/api/article/edit', data).then((r) => r.data)
}

export function deleteArticleApi(id: number): Promise<ApiResult<null>> {
  return request.delete(`/api/article/delete/${id}`).then((r) => r.data)
}
