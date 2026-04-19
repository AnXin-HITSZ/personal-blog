import request from '@/utils/request'
import type { Result, Article } from '@/types/api'

export const getAllArticlesApi = async (): Promise<Result<Article[]>> => {
  const res = await request.get('/api/article/all')
  return res.data as Result<Article[]>
}

export const addArticleApi = async (data: Article): Promise<Result> => {
  const res = await request.post('/api/article/add', data)
  return res.data as Result
}

export const editArticleApi = async (data: Article): Promise<Result> => {
  const res = await request.put('/api/article/edit', data)
  return res.data as Result
}

export const deleteArticleApi = async (articleId: number): Promise<Result> => {
  const res = await request.delete(`/api/article/delete/${articleId}`)
  return res.data as Result
}