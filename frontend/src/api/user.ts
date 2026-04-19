import request from '@/utils/request'
import type { Result } from '@/types/api'

export interface User {
  id?: number
  username: string
  password?: string
  // Add other user fields as needed
}

export const addUserApi = (data: User): Promise<Result> => {
  return request.post('/api/user/add', data)
}

export const deleteUserApi = (userId: number): Promise<Result> => {
  return request.post(`/api/user/delete/${userId}`)
}