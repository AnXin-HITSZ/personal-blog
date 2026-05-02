import request from '@/utils/request'
import type { Result, RAGKnowledgeBase } from '@/types/api'

const AGENT_BASE_URL = import.meta.env.VITE_AGENT_BASE_URL || 'http://localhost:8000'

export const getRAGListApi = async (): Promise<Result<RAGKnowledgeBase[]>> => {
  const res = await request.get('/api/rag/list')
  return res.data as Result<RAGKnowledgeBase[]>
}

export const addRAGApi = async (data: RAGKnowledgeBase): Promise<Result<RAGKnowledgeBase>> => {
  const res = await request.post('/api/rag/add', data)
  return res.data as Result<RAGKnowledgeBase>
}

export const updateRAGApi = async (data: RAGKnowledgeBase): Promise<Result<RAGKnowledgeBase>> => {
  const res = await request.post('/api/rag/update', data)
  return res.data as Result<RAGKnowledgeBase>
}

export const deleteRAGApi = async (ragId: number): Promise<Result> => {
  const res = await request.post(`/api/rag/delete/${ragId}`)
  return res.data as Result
}

/** 上传知识库文件到 Agent 并触发索引 */
export const uploadRAGFilesApi = async (
  namespace: string,
  collectionName: string,
  files: File[]
): Promise<{ success: boolean; message: string; fileCount: number }> => {
  const formData = new FormData()
  formData.append('namespace', namespace)
  formData.append('collection_name', collectionName)
  files.forEach(file => formData.append('files', file))

  const res = await fetch(`${AGENT_BASE_URL}/api/agent/rag/upload`, {
    method: 'POST',
    body: formData,
  })
  return res.json()
}
