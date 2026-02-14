/**
 * 发布预设数据 Store
 * 用于从 AI 向导页自动传递数据到发布中心
 */

import { defineStore } from 'pinia'

export interface VideoFileInfo {
  name: string
  url: string
  path: string
  size?: number
  type?: string
}

export interface PublishPresetData {
  title: string
  tags: string[]
  videoFiles: VideoFileInfo[]
  platform: number // 1=小红书, 2=视频号, 3=抖音, 4=快手
  contentType: 'video' | 'image'
}

export const usePublishPresetStore = defineStore('publishPreset', {
  state: () => ({
    preset: null as PublishPresetData | null
  }),

  actions: {
    /**
     * 设置预填数据（从 AI 向导页调用）
     */
    setPreset(data: PublishPresetData) {
      this.preset = data
    },

    /**
     * 获取并清空预填数据（发布中心调用后即清空）
     */
    consumePreset(): PublishPresetData | null {
      const data = this.preset
      this.preset = null
      return data
    },

    /**
     * 清空预填数据
     */
    clearPreset() {
      this.preset = null
    }
  }
})

