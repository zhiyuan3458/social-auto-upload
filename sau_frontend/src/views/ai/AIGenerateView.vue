<template>
  <div class="generate-container">
    <el-card>
      <template #header>
        <div class="card-header">
          <div>
            <span class="title">生成图片</span>
            <el-tag v-if="store.isGenerating" type="warning" size="small" style="margin-left: 10px">
              生成中...
            </el-tag>
            <el-tag v-else-if="store.hasFailedImages" type="danger" size="small" style="margin-left: 10px">
              {{ store.failedCount }} 张失败
            </el-tag>
            <el-tag v-else-if="store.progress.status === 'done'" type="success" size="small" style="margin-left: 10px">
              完成
            </el-tag>
          </div>
          <div class="actions">
            <el-button 
              v-if="store.hasFailedImages && !store.isGenerating"
              type="warning"
              @click="retryAllFailed"
              :loading="isRetrying"
            >
              补全失败图片
            </el-button>
            <el-button @click="router.push('/ai-create/outline')">返回大纲</el-button>
            <el-button 
              type="primary" 
              @click="router.push('/ai-create/result')"
              :disabled="store.completedCount === 0"
            >
              查看结果
            </el-button>
          </div>
        </div>
      </template>

      <!-- 进度条 -->
      <div class="progress-section">
        <div class="progress-info">
          <span>进度</span>
          <span>{{ store.progress.current }} / {{ store.progress.total }}</span>
        </div>
        <el-progress 
          :percentage="store.progressPercent" 
          :status="store.progress.status === 'done' ? 'success' : undefined"
        />
      </div>

      <!-- 错误提示 -->
      <el-alert
        v-if="error"
        :title="error"
        type="error"
        show-icon
        closable
        @close="error = ''"
        style="margin: 20px 0"
      />

      <!-- 图片网格 -->
      <div class="images-grid">
        <div 
          v-for="image in store.images" 
          :key="image.index"
          class="image-card"
        >
          <!-- 已生成 -->
          <div v-if="image.url && image.status === 'done'" class="image-preview">
            <el-image 
              :src="image.url" 
              fit="cover"
              :preview-src-list="[image.url.replace('?thumbnail=true', '?thumbnail=false')]"
            />
            <div class="image-overlay">
              <el-button 
                size="small"
                @click="regenerateImage(image.index)"
                :loading="image.status === 'retrying'"
              >
                重新生成
              </el-button>
            </div>
          </div>

          <!-- 生成中 -->
          <div v-else-if="image.status === 'generating' || image.status === 'retrying'" class="image-placeholder loading">
            <el-icon class="loading-icon"><Loading /></el-icon>
            <span>{{ image.status === 'retrying' ? '重试中...' : '生成中...' }}</span>
          </div>

          <!-- 失败 -->
          <div v-else-if="image.status === 'error'" class="image-placeholder error">
            <el-icon class="error-icon"><CircleClose /></el-icon>
            <span>生成失败</span>
            <el-button size="small" @click="regenerateImage(image.index)">重试</el-button>
          </div>

          <!-- 等待 -->
          <div v-else class="image-placeholder">
            <span>等待中</span>
          </div>

          <!-- 底部信息 -->
          <div class="image-footer">
            <span>第 {{ image.index + 1 }} 页</span>
            <el-tag :type="getStatusType(image.status)" size="small">
              {{ getStatusText(image.status) }}
            </el-tag>
          </div>
        </div>
      </div>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { Loading, CircleClose } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import { useAIGeneratorStore } from '@/stores/aiGenerator'
import { generateImages, regenerateImage as apiRegenerateImage, updateHistory, getImageUrl } from '@/api/ai'

// 获取后端基础 URL
const getBaseUrl = () => import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:5409'

// 将相对 URL 转为完整 URL
function toFullUrl(url: string): string {
  if (!url) return url
  if (url.startsWith('http://') || url.startsWith('https://')) return url
  return getBaseUrl() + url
}

const router = useRouter()
const store = useAIGeneratorStore()

const error = ref('')
const isRetrying = ref(false)

function getStatusType(status: string): string {
  const types: Record<string, string> = {
    done: 'success',
    generating: 'warning',
    retrying: 'warning',
    error: 'danger'
  }
  return types[status] || 'info'
}

function getStatusText(status: string): string {
  const texts: Record<string, string> = {
    done: '完成',
    generating: '生成中',
    retrying: '重试中',
    error: '失败'
  }
  return texts[status] || '等待'
}

async function regenerateImage(index: number) {
  if (!store.taskId) return

  const page = store.outline.pages.find(p => p.index === index)
  if (!page) return

  store.setImageRetrying(index)

  try {
    const result = await apiRegenerateImage(store.taskId, page, true, {
      fullOutline: store.outline.raw,
      userTopic: store.topic
    })

    if (result.success && result.image_url) {
      // 将相对 URL 转为完整 URL
      const fullUrl = toFullUrl(result.image_url)
      store.updateImage(index, fullUrl)
    } else {
      store.updateProgress(index, 'error', undefined, result.error)
    }
  } catch (e: any) {
    store.updateProgress(index, 'error', undefined, e.message)
  }
}

async function retryAllFailed() {
  const failedPages = store.getFailedPages()
  if (failedPages.length === 0) return

  isRetrying.value = true

  for (const page of failedPages) {
    await regenerateImage(page.index)
  }

  isRetrying.value = false
}

onMounted(async () => {
  if (store.outline.pages.length === 0) {
    router.push('/ai-create')
    return
  }

  // 如果还没开始生成，开始生成
  if (store.progress.status === 'idle') {
    store.startGeneration()

    await generateImages(
      store.outline.pages,
      null,
      store.outline.raw,
      {
        onProgress: (event) => {
          console.log('Progress:', event)
        },
        onComplete: (event) => {
          console.log('Complete:', event)
          if (event.image_url) {
            // 将相对 URL 转为完整 URL（Electron 生产环境需要）
            const fullUrl = toFullUrl(event.image_url)
            store.updateProgress(event.index, 'done', fullUrl)
          }
        },
        onError: (event) => {
          console.error('Error:', event)
          store.updateProgress(event.index, 'error', undefined, event.message)
        },
        onFinish: async (event) => {
          console.log('Finish:', event)
          store.finishGeneration(event.task_id)

          // 更新历史记录
          if (store.recordId) {
            try {
              // 将相对 URL 转为完整 URL
              const generatedImages = event.images
                .filter((img: string | null) => img !== null)
                .map((img: string) => toFullUrl(img))
              const status = store.hasFailedImages 
                ? (generatedImages.length > 0 ? 'partial' : 'draft') 
                : 'completed'
              const thumbnail = generatedImages.length > 0 ? generatedImages[0] : null

              await updateHistory(store.recordId, {
                images: {
                  task_id: event.task_id,
                  generated: generatedImages
                },
                status,
                thumbnail: thumbnail || undefined
              })
            } catch (e) {
              console.error('Failed to update history:', e)
            }
          }

          // 自动跳转到结果页
          if (!store.hasFailedImages) {
            setTimeout(() => {
              router.push('/ai-create/result')
            }, 1500)
          }
        },
        onStreamError: (err) => {
          console.error('Stream Error:', err)
          error.value = '生成失败: ' + err.message
        }
      },
      store.userImages.length > 0 ? store.userImages : undefined,
      store.topic
    )
  }
})
</script>

<style scoped>
.generate-container {
  padding: 20px;
  max-width: 1200px;
  margin: 0 auto;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.title {
  font-size: 18px;
  font-weight: 600;
}

.actions {
  display: flex;
  gap: 10px;
}

.progress-section {
  margin-bottom: 30px;
}

.progress-info {
  display: flex;
  justify-content: space-between;
  margin-bottom: 10px;
  color: #606266;
}

.images-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
  gap: 20px;
}

.image-card {
  border: 1px solid #ebeef5;
  border-radius: 8px;
  overflow: hidden;
  transition: all 0.3s;
}

.image-card:hover {
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
}

.image-preview {
  aspect-ratio: 3/4;
  position: relative;
  overflow: hidden;
}

.image-preview .el-image {
  width: 100%;
  height: 100%;
}

.image-overlay {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  opacity: 0;
  transition: opacity 0.3s;
}

.image-preview:hover .image-overlay {
  opacity: 1;
}

.image-placeholder {
  aspect-ratio: 3/4;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 10px;
  background: #f5f7fa;
  color: #909399;
}

.image-placeholder.loading {
  background: #ecf5ff;
  color: #409eff;
}

.image-placeholder.error {
  background: #fef0f0;
  color: #f56c6c;
}

.loading-icon {
  font-size: 32px;
  animation: rotate 1s linear infinite;
}

.error-icon {
  font-size: 32px;
}

@keyframes rotate {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

.image-footer {
  padding: 10px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  border-top: 1px solid #ebeef5;
  font-size: 13px;
  color: #606266;
}
</style>
