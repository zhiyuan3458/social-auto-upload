/**
 * AI API 模块
 */

import request from '@/utils/request'
import type {
  Page,
  OutlineResponse,
  ContentResponse,
  ProgressEvent,
  FinishEvent,
  HistoryRecord,
  HistoryDetail,
  AIConfig
} from '@/types/ai'

// 获取后端 API 基础地址
const getBaseUrl = () => import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:5409'
const API_BASE_URL = '/api/ai'

/**
 * 生成大纲
 */
export async function generateOutline(
  topic: string,
  images?: File[]
): Promise<OutlineResponse> {
  if (images && images.length > 0) {
    const formData = new FormData()
    formData.append('topic', topic)
    images.forEach((file) => {
      formData.append('images', file)
    })

    const response = await request.post<OutlineResponse>(
      `${API_BASE_URL}/outline`,
      formData,
      {
        headers: { 'Content-Type': 'multipart/form-data' }
      }
    )
    return response.data || response
  }

  const response = await request.post<OutlineResponse>(`${API_BASE_URL}/outline`, { topic })
  return response.data || response
}

/**
 * 生成内容（标题、文案、标签）
 */
export async function generateContent(
  topic: string,
  outline: string
): Promise<ContentResponse> {
  const response = await request.post<ContentResponse>(`${API_BASE_URL}/content`, {
    topic,
    outline
  })
  return response.data || response
}

/**
 * 获取图片 URL
 */
export function getImageUrl(taskId: string, filename: string, thumbnail: boolean = true): string {
  const thumbParam = thumbnail ? '?thumbnail=true' : '?thumbnail=false'
  return `${getBaseUrl()}${API_BASE_URL}/images/${taskId}/${filename}${thumbParam}`
}

/**
 * 生成图片（SSE 流式）
 */
export async function generateImages(
  pages: Page[],
  taskId: string | null,
  fullOutline: string,
  callbacks: {
    onProgress?: (event: ProgressEvent) => void
    onComplete?: (event: ProgressEvent) => void
    onError?: (event: ProgressEvent) => void
    onFinish?: (event: FinishEvent) => void
    onStreamError?: (error: Error) => void
  },
  userImages?: File[],
  userTopic?: string
): Promise<void> {
  try {
    // 将图片转为 base64
    let userImagesBase64: string[] = []
    if (userImages && userImages.length > 0) {
      userImagesBase64 = await Promise.all(
        userImages.map(file => {
          return new Promise<string>((resolve, reject) => {
            const reader = new FileReader()
            reader.onload = () => resolve(reader.result as string)
            reader.onerror = reject
            reader.readAsDataURL(file)
          })
        })
      )
    }

    const response = await fetch(`${getBaseUrl()}${API_BASE_URL}/generate`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        pages,
        task_id: taskId,
        full_outline: fullOutline,
        user_images: userImagesBase64.length > 0 ? userImagesBase64 : undefined,
        user_topic: userTopic || ''
      })
    })

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`)
    }

    const reader = response.body?.getReader()
    if (!reader) {
      throw new Error('Cannot read response stream')
    }

    const decoder = new TextDecoder()
    let buffer = ''

    while (true) {
      const { done, value } = await reader.read()
      if (done) break

      buffer += decoder.decode(value, { stream: true })
      const lines = buffer.split('\n\n')
      buffer = lines.pop() || ''

      for (const line of lines) {
        if (!line.trim()) continue

        const [eventLine, dataLine] = line.split('\n')
        if (!eventLine || !dataLine) continue

        const eventType = eventLine.replace('event: ', '').trim()
        const eventData = dataLine.replace('data: ', '').trim()

        try {
          const data = JSON.parse(eventData)

          switch (eventType) {
            case 'progress':
              callbacks.onProgress?.(data)
              break
            case 'complete':
              callbacks.onComplete?.(data)
              break
            case 'error':
              callbacks.onError?.(data)
              break
            case 'finish':
              callbacks.onFinish?.(data)
              break
          }
        } catch (e) {
          console.error('Failed to parse SSE data:', e)
        }
      }
    }
  } catch (error) {
    callbacks.onStreamError?.(error as Error)
  }
}

/**
 * 重新生成单张图片
 */
export async function regenerateImage(
  taskId: string,
  page: Page,
  useReference: boolean = true,
  context?: { fullOutline?: string; userTopic?: string }
): Promise<{ success: boolean; index: number; image_url?: string; error?: string }> {
  const response = await request.post(`${API_BASE_URL}/regenerate`, {
    task_id: taskId,
    page,
    use_reference: useReference,
    full_outline: context?.fullOutline,
    user_topic: context?.userTopic
  })
  return response.data || response
}

// ==================== 历史记录 API ====================

/**
 * 获取历史记录列表
 */
export async function getHistoryList(
  page: number = 1,
  pageSize: number = 20,
  status?: string
): Promise<{
  success: boolean
  records: HistoryRecord[]
  total: number
  page: number
  page_size: number
  total_pages: number
  error?: string
}> {
  const params: Record<string, any> = { page, page_size: pageSize }
  if (status) params.status = status

  const response = await request.get(`${API_BASE_URL}/history`, { params })
  return response.data || response
}

/**
 * 创建历史记录
 */
export async function createHistory(
  topic: string,
  outline: { raw: string; pages: Page[] },
  taskId?: string
): Promise<{ success: boolean; record_id?: string; error?: string }> {
  const response = await request.post(`${API_BASE_URL}/history`, {
    topic,
    outline,
    task_id: taskId
  })
  return response.data || response
}

/**
 * 获取历史记录详情
 */
export async function getHistory(
  recordId: string
): Promise<{ success: boolean; record?: HistoryDetail; error?: string }> {
  const response = await request.get(`${API_BASE_URL}/history/${recordId}`)
  return response.data || response
}

/**
 * 更新历史记录
 */
export async function updateHistory(
  recordId: string,
  data: {
    outline?: { raw: string; pages: Page[] }
    images?: { task_id: string | null; generated: string[] }
    status?: string
    thumbnail?: string
  }
): Promise<{ success: boolean; error?: string }> {
  const response = await request.put(`${API_BASE_URL}/history/${recordId}`, data)
  return response.data || response
}

/**
 * 删除历史记录
 */
export async function deleteHistory(
  recordId: string
): Promise<{ success: boolean; error?: string }> {
  const response = await request.delete(`${API_BASE_URL}/history/${recordId}`)
  return response.data || response
}

// ==================== 配置 API ====================

/**
 * 获取 AI 配置
 */
export async function getAIConfig(): Promise<{
  success: boolean
  config?: AIConfig
  error?: string
}> {
  const response = await request.get(`${API_BASE_URL}/config`)
  return response.data || response
}

/**
 * 更新 AI 配置
 */
export async function updateAIConfig(
  config: Partial<AIConfig>
): Promise<{ success: boolean; message?: string; error?: string }> {
  const response = await request.post(`${API_BASE_URL}/config`, config)
  return response.data || response
}

/**
 * 测试 AI 服务商连接
 */
export async function testAIConnection(config: {
  type: string
  api_key: string
  base_url: string
  model: string
}): Promise<{ success: boolean; message?: string; error?: string }> {
  const response = await request.post(`${API_BASE_URL}/config/test`, config)
  return response.data || response
}
