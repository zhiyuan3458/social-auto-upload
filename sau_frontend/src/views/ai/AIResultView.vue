<template>
  <div class="result-container">
    <!-- 图片预览 -->
    <el-card class="images-card">
      <template #header>
        <div class="card-header">
          <span class="title">图片预览</span>
          <el-button @click="router.push('/ai-create/generate')">返回</el-button>
        </div>
      </template>

      <div class="images-scroll">
        <div 
          v-for="image in store.images.filter(i => i.status === 'done')" 
          :key="image.index"
          class="image-item"
        >
          <el-image 
            :src="image.url" 
            fit="cover"
            :preview-src-list="previewList"
            :initial-index="image.index"
          />
          <div class="image-label">第 {{ image.index + 1 }} 页</div>
        </div>
      </div>
    </el-card>

    <!-- 内容生成 -->
    <el-card class="content-card">
      <template #header>
        <div class="card-header">
          <span class="title">文案内容</span>
          <el-button 
            type="primary" 
            @click="handleGenerateContent"
            :loading="contentLoading"
            :disabled="store.content.status === 'done'"
          >
            {{ store.content.status === 'done' ? '已生成' : '生成文案' }}
          </el-button>
        </div>
      </template>

      <!-- 生成中 -->
      <div v-if="contentLoading" class="content-loading">
        <el-icon class="loading-icon"><Loading /></el-icon>
        <span>正在生成文案...</span>
      </div>

      <!-- 已生成内容 -->
      <div v-else-if="store.content.status === 'done'" class="content-display">
        <!-- 标题选择 -->
        <div class="section">
          <div class="section-header">
            <span>标题（点击选择）</span>
          </div>
          <div class="titles-list">
            <div 
              v-for="(title, index) in store.content.titles" 
              :key="index"
              class="title-item"
              :class="{ active: selectedTitle === index }"
              @click="selectedTitle = index"
            >
              {{ title }}
            </div>
          </div>
        </div>

        <!-- 文案 -->
        <div class="section">
          <div class="section-header">
            <span>正文</span>
            <el-button size="small" text @click="copyText(store.content.copywriting)">复制</el-button>
          </div>
          <el-input
            v-model="editableCopywriting"
            type="textarea"
            :rows="6"
            placeholder="文案内容..."
          />
        </div>

        <!-- 标签 -->
        <div class="section">
          <div class="section-header">
            <span>标签</span>
          </div>
          <div class="tags-list">
            <el-tag 
              v-for="(tag, index) in store.content.tags" 
              :key="index"
              closable
              @close="handleRemoveTag(index)"
            >
              #{{ tag }}
            </el-tag>
          </div>
        </div>
      </div>

      <!-- 未生成 -->
      <div v-else class="content-empty">
        <p>点击"生成文案"按钮，AI 将根据图文内容生成标题、正文和标签</p>
      </div>
    </el-card>

    <!-- 发布按钮 -->
    <el-card class="publish-card">
      <template #header>
        <span class="title">发布到平台</span>
      </template>

      <div class="publish-actions">
        <el-button 
          type="danger" 
          size="large"
          @click="handlePublishToXHS"
          :disabled="store.content.status !== 'done'"
        >
          去往发布中心发布
        </el-button>
        <el-button 
          size="large"
          @click="handleSaveToMaterial"
        >
          保存到素材库
        </el-button>
        <el-button 
          size="large"
          @click="handleNewCreate"
        >
          新建创作
        </el-button>
      </div>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { Loading } from '@element-plus/icons-vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { useAIGeneratorStore } from '@/stores/aiGenerator'
import { generateContent } from '@/api/ai'
import request from '@/utils/request'

const router = useRouter()
const store = useAIGeneratorStore()

const contentLoading = ref(false)
const selectedTitle = ref(0)
const editableCopywriting = ref('')

const previewList = computed(() => {
  return store.images
    .filter(i => i.status === 'done')
    .map(i => i.url.replace('?thumbnail=true', '?thumbnail=false'))
})

onMounted(() => {
  if (store.images.length === 0 || store.completedCount === 0) {
    router.push('/ai-create')
    return
  }
  editableCopywriting.value = store.content.copywriting
})

async function handleGenerateContent() {
  contentLoading.value = true
  store.startContentGeneration()

  try {
    const result = await generateContent(store.topic, store.outline.raw)

    if (result.success) {
      store.setContent(
        result.titles || [],
        result.copywriting || '',
        result.tags || []
      )
      editableCopywriting.value = result.copywriting || ''
      ElMessage.success('文案生成成功')
    } else {
      store.setContentError(result.error || '生成失败')
      ElMessage.error(result.error || '生成失败')
    }
  } catch (e: any) {
    store.setContentError(e.message)
    ElMessage.error(e.message || '网络错误')
  } finally {
    contentLoading.value = false
  }
}

function copyText(text: string) {
  navigator.clipboard.writeText(text)
  ElMessage.success('已复制到剪贴板')
}

function handleRemoveTag(index: number) {
  store.content.tags.splice(index, 1)
}

async function handlePublishToXHS() {
  if (store.content.status !== 'done') {
    ElMessage.warning('请先生成文案')
    return
  }

  // 先保存到素材库
  const saved = await doSaveToMaterial()
  if (!saved) return

  // 存储 AI 数据到 sessionStorage
  const aiData = {
    title: store.content.titles[selectedTitle.value] || store.topic,
    copywriting: editableCopywriting.value,
    tags: store.content.tags,
    taskId: store.taskId,
    images: store.images.filter(i => i.status === 'done').map(i => `ai_${store.taskId}_${i.index}.png`)
  }
  sessionStorage.setItem('ai-publish-data', JSON.stringify(aiData))

  ElMessage.success('即将跳转到发布中心...')
  setTimeout(() => {
    router.push({
      path: '/publish-center',
      query: { from: 'ai' }
    })
  }, 500)
}

const savingMaterial = ref(false)

async function doSaveToMaterial(): Promise<boolean> {
  if (!store.taskId) {
    ElMessage.error('任务信息丢失')
    return false
  }

  savingMaterial.value = true
  try {
    const images = store.images
      .filter(i => i.status === 'done')
      .map(i => `${i.index}.png`)

    const result = await request.post('/api/ai/transfer-to-material', {
      task_id: store.taskId,
      images,
      title: store.topic
    })

    if (result.code === 200) {
      return true
    } else {
      ElMessage.error(result.msg || '保存失败')
      return false
    }
  } catch (e: any) {
    ElMessage.error(e.message || '网络错误')
    return false
  } finally {
    savingMaterial.value = false
  }
}

async function handleSaveToMaterial() {
  const saved = await doSaveToMaterial()
  if (saved) {
    ElMessage.success('已保存到素材库')
  }
}

function handleNewCreate() {
  ElMessageBox.confirm('确定要新建创作吗？当前内容将被清空。', '提示', {
    confirmButtonText: '确定',
    cancelButtonText: '取消',
    type: 'warning'
  }).then(() => {
    store.reset()
    router.push('/ai-create')
  }).catch(() => {})
}
</script>

<style scoped>
.result-container {
  padding: 20px;
  max-width: 1200px;
  margin: 0 auto;
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.title {
  font-size: 16px;
  font-weight: 600;
}

.images-scroll {
  display: flex;
  gap: 15px;
  overflow-x: auto;
  padding: 10px 0;
}

.image-item {
  flex-shrink: 0;
  width: 150px;
  text-align: center;
}

.image-item .el-image {
  width: 150px;
  height: 200px;
  border-radius: 8px;
  cursor: pointer;
}

.image-label {
  margin-top: 8px;
  font-size: 13px;
  color: #606266;
}

.content-loading {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 60px 0;
  color: #409eff;
}

.loading-icon {
  font-size: 40px;
  margin-bottom: 15px;
  animation: rotate 1s linear infinite;
}

@keyframes rotate {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

.content-empty {
  text-align: center;
  padding: 40px;
  color: #909399;
}

.content-display {
  display: flex;
  flex-direction: column;
  gap: 25px;
}

.section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 10px;
  font-weight: 500;
}

.titles-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.title-item {
  padding: 12px 15px;
  background: #f5f7fa;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.3s;
  border: 2px solid transparent;
}

.title-item:hover {
  background: #ecf5ff;
}

.title-item.active {
  background: #ecf5ff;
  border-color: #409eff;
}

.tags-list {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
}

.publish-actions {
  display: flex;
  gap: 15px;
  justify-content: center;
}
</style>
