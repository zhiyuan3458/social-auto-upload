/**
 * AI 模块类型定义
 */

// 页面类型
export type PageType = 'cover' | 'content' | 'summary'

// 页面数据
export interface Page {
  index: number
  type: PageType
  content: string
}

// 大纲响应
export interface OutlineResponse {
  success: boolean
  outline?: string
  pages?: Page[]
  has_images?: boolean
  error?: string
}

// 内容响应
export interface ContentResponse {
  success: boolean
  titles?: string[]
  copywriting?: string
  tags?: string[]
  error?: string
}

// 视频提示词包响应
export interface VideoPlanResponse {
  success: boolean
  video_plan?: VideoPlan
  error?: string
}

export interface VideoPlan {
  platform: string
  aspect_ratio: string
  duration_seconds: number
  creative_direction?: string
  main_subject?: string
  style_keywords?: string[]
  global_constraints?: Record<string, any>
  storyboard?: VideoStoryboardShot[]
  prompt_pack?: {
    universal?: VideoPromptPack
    keling?: VideoPromptPack
    jimeng?: VideoPromptPack
  }
}

export interface VideoStoryboardShot {
  shot: number
  duration_s?: number
  scene?: string
  camera?: string
  action?: string
  subtitle?: string
  voiceover?: string
  prompt_universal?: string
  negative_prompt?: string
}

export interface VideoPromptPack {
  global_prompt?: string
  shots?: Array<{
    shot: number
    prompt: string
    negative_prompt?: string
  }>
}

// 进度事件
export interface ProgressEvent {
  index: number
  status: 'generating' | 'done' | 'error' | 'retrying'
  current?: number
  total?: number
  image_url?: string
  message?: string
  phase?: 'cover' | 'content'
}

// 完成事件
export interface FinishEvent {
  success: boolean
  task_id: string
  images: string[]
  total: number
  completed: number
  failed: number
  failed_indices: number[]
}

// 生成的图片
export interface GeneratedImage {
  index: number
  url: string
  status: 'generating' | 'done' | 'error' | 'retrying'
  error?: string
}

// 生成的内容
export interface GeneratedContent {
  titles: string[]
  copywriting: string
  tags: string[]
  status: 'idle' | 'generating' | 'done' | 'error'
  error?: string
}

// 历史记录
export interface HistoryRecord {
  id: string
  title: string
  created_at: string
  updated_at: string
  status: string
  thumbnail: string | null
  page_count: number
  task_id: string | null
}

// 历史记录详情
export interface HistoryDetail {
  id: string
  title: string
  created_at: string
  updated_at: string
  outline: {
    raw: string
    pages: Page[]
  }
  images: {
    task_id: string | null
    generated: string[]
  }
  status: string
  thumbnail: string | null
}

// AI 配置
export interface AIConfig {
  text_generation: {
    active_provider: string
    providers: Record<string, ProviderConfig>
  }
  image_generation: {
    active_provider: string
    providers: Record<string, ProviderConfig>
  }
}

// 服务商配置
export interface ProviderConfig {
  type: string
  name?: string
  base_url: string
  api_key: string
  model: string
  temperature?: number
  max_output_tokens?: number
  default_size?: string
  quality?: string
}

// 生成器状态
export interface GeneratorState {
  stage: 'input' | 'outline' | 'generating' | 'result'
  topic: string
  outline: {
    raw: string
    pages: Page[]
  }
  progress: {
    current: number
    total: number
    status: 'idle' | 'generating' | 'done' | 'error'
  }
  images: GeneratedImage[]
  taskId: string | null
  recordId: string | null
  userImages: File[]
  content: GeneratedContent
}
