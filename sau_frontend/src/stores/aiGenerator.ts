/**
 * AI 生成器状态管理
 */

import { defineStore } from 'pinia'
import type { Page, GeneratedImage, GeneratedContent, GeneratorState } from '@/types/ai'

const STORAGE_KEY = 'ai-generator-state'

// 从 localStorage 加载状态
function loadState(): Partial<GeneratorState> {
  try {
    const saved = localStorage.getItem(STORAGE_KEY)
    if (saved) {
      return JSON.parse(saved)
    }
  } catch (e) {
    console.error('Failed to load state:', e)
  }
  return {}
}

// 保存状态到 localStorage
function saveState(state: GeneratorState) {
  try {
    const toSave = {
      stage: state.stage,
      topic: state.topic,
      outline: state.outline,
      progress: state.progress,
      images: state.images,
      taskId: state.taskId,
      recordId: state.recordId,
      content: state.content
    }
    localStorage.setItem(STORAGE_KEY, JSON.stringify(toSave))
  } catch (e) {
    console.error('Failed to save state:', e)
  }
}

export const useAIGeneratorStore = defineStore('aiGenerator', {
  state: (): GeneratorState => {
    const saved = loadState()
    return {
      stage: saved.stage || 'input',
      topic: saved.topic || '',
      outline: saved.outline || { raw: '', pages: [] },
      progress: saved.progress || { current: 0, total: 0, status: 'idle' },
      images: saved.images || [],
      taskId: saved.taskId || null,
      recordId: saved.recordId || null,
      userImages: [],
      content: saved.content || {
        titles: [],
        copywriting: '',
        tags: [],
        status: 'idle'
      }
    }
  },

  getters: {
    hasFailedImages: (state) => state.images.some(img => img.status === 'error'),
    failedCount: (state) => state.images.filter(img => img.status === 'error').length,
    completedCount: (state) => state.images.filter(img => img.status === 'done').length,
    isGenerating: (state) => state.progress.status === 'generating',
    progressPercent: (state) => {
      if (state.progress.total === 0) return 0
      return (state.progress.current / state.progress.total) * 100
    }
  },

  actions: {
    // 设置主题
    setTopic(topic: string) {
      this.topic = topic
      this.saveToStorage()
    },

    // 设置大纲
    setOutline(raw: string, pages: Page[]) {
      this.outline.raw = raw
      this.outline.pages = pages
      this.stage = 'outline'
      this.saveToStorage()
    },

    // 更新页面
    updatePage(index: number, content: string) {
      const page = this.outline.pages.find(p => p.index === index)
      if (page) {
        page.content = content
        this.syncRawFromPages()
        this.saveToStorage()
      }
    },

    // 同步 raw 和 pages
    syncRawFromPages() {
      this.outline.raw = this.outline.pages
        .map(page => page.content)
        .join('\n\n<page>\n\n')
    },

    // 删除页面
    deletePage(index: number) {
      this.outline.pages = this.outline.pages.filter(p => p.index !== index)
      this.outline.pages.forEach((page, idx) => {
        page.index = idx
      })
      this.syncRawFromPages()
      this.saveToStorage()
    },

    // 添加页面
    addPage(type: 'cover' | 'content' | 'summary', content: string = '') {
      const newPage: Page = {
        index: this.outline.pages.length,
        type,
        content
      }
      this.outline.pages.push(newPage)
      this.syncRawFromPages()
      this.saveToStorage()
    },

    // 开始生成
    startGeneration() {
      this.stage = 'generating'
      this.progress.current = 0
      this.progress.total = this.outline.pages.length
      this.progress.status = 'generating'
      this.images = this.outline.pages.map(page => ({
        index: page.index,
        url: '',
        status: 'generating'
      }))
      this.saveToStorage()
    },

    // 更新进度
    updateProgress(index: number, status: 'generating' | 'done' | 'error', url?: string, error?: string) {
      const image = this.images.find(img => img.index === index)
      if (image) {
        image.status = status
        if (url) image.url = url
        if (error) image.error = error
      }
      if (status === 'done') {
        this.progress.current++
      }
      this.saveToStorage()
    },

    // 更新图片
    updateImage(index: number, newUrl: string) {
      const image = this.images.find(img => img.index === index)
      if (image) {
        const timestamp = Date.now()
        image.url = `${newUrl}?t=${timestamp}`
        image.status = 'done'
        delete image.error
      }
      this.saveToStorage()
    },

    // 完成生成
    finishGeneration(taskId: string) {
      this.taskId = taskId
      this.stage = 'result'
      this.progress.status = 'done'
      this.saveToStorage()
    },

    // 设置重试中状态
    setImageRetrying(index: number) {
      const image = this.images.find(img => img.index === index)
      if (image) {
        image.status = 'retrying'
      }
      this.saveToStorage()
    },

    // 获取失败的页面
    getFailedPages(): Page[] {
      const failedIndices = this.images
        .filter(img => img.status === 'error')
        .map(img => img.index)
      return this.outline.pages.filter(page => failedIndices.includes(page.index))
    },

    // 设置历史记录 ID
    setRecordId(recordId: string | null) {
      this.recordId = recordId
      this.saveToStorage()
    },

    // 设置内容
    setContent(titles: string[], copywriting: string, tags: string[]) {
      this.content.titles = titles
      this.content.copywriting = copywriting
      this.content.tags = tags
      this.content.status = 'done'
      this.saveToStorage()
    },

    // 开始生成内容
    startContentGeneration() {
      this.content.status = 'generating'
      this.saveToStorage()
    },

    // 设置内容错误
    setContentError(error: string) {
      this.content.status = 'error'
      this.content.error = error
      this.saveToStorage()
    },

    // 重置状态
    reset() {
      this.stage = 'input'
      this.topic = ''
      this.outline = { raw: '', pages: [] }
      this.progress = { current: 0, total: 0, status: 'idle' }
      this.images = []
      this.taskId = null
      this.recordId = null
      this.userImages = []
      this.content = {
        titles: [],
        copywriting: '',
        tags: [],
        status: 'idle'
      }
      localStorage.removeItem(STORAGE_KEY)
    },

    // 保存到 localStorage
    saveToStorage() {
      saveState(this.$state)
    }
  }
})
