<template>
  <div class="ai-create-container">
    <el-card class="main-card">
      <template #header>
        <div class="card-header">
          <span>AI 内容创作</span>
          <el-tag type="info">一句话生成小红书图文</el-tag>
        </div>
      </template>

      <div class="input-section">
        <el-input
          v-model="topic"
          type="textarea"
          :rows="4"
          placeholder="输入你想创作的主题，例如：分享一款超好用的护肤品..."
          :disabled="loading"
          maxlength="500"
          show-word-limit
        />

        <div class="upload-section">
          <el-upload
            v-model:file-list="fileList"
            :auto-upload="false"
            :limit="3"
            accept="image/*"
            list-type="picture-card"
            :on-exceed="handleExceed"
          >
            <el-icon><Plus /></el-icon>
            <template #tip>
              <div class="el-upload__tip">
                可选：上传参考图片（最多3张）
              </div>
            </template>
          </el-upload>
        </div>

        <el-button
          type="primary"
          size="large"
          :loading="loading"
          :disabled="!topic.trim()"
          @click="handleGenerate"
          class="generate-btn"
        >
          {{ loading ? '生成中...' : '生成大纲' }}
        </el-button>
      </div>

      <el-alert
        v-if="error"
        :title="error"
        type="error"
        show-icon
        closable
        @close="error = ''"
        style="margin-top: 20px"
      />
    </el-card>

    <!-- 使用说明 -->
    <el-card class="tips-card">
      <template #header>
        <span>使用说明</span>
      </template>
      <el-steps direction="vertical" :active="0">
        <el-step title="输入主题" description="描述你想创作的内容主题" />
        <el-step title="生成大纲" description="AI 自动生成图文大纲" />
        <el-step title="编辑大纲" description="调整修改大纲内容" />
        <el-step title="生成图片" description="AI 根据大纲生成配图" />
        <el-step title="生成文案" description="AI 生成标题、文案、标签" />
        <el-step title="一键发布" description="发布到小红书等平台" />
      </el-steps>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { Plus } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import type { UploadProps, UploadUserFile } from 'element-plus'
import { useAIGeneratorStore } from '@/stores/aiGenerator'
import { generateOutline, createHistory } from '@/api/ai'

const router = useRouter()
const store = useAIGeneratorStore()

const topic = ref('')
const loading = ref(false)
const error = ref('')
const fileList = ref<UploadUserFile[]>([])

const handleExceed: UploadProps['onExceed'] = () => {
  ElMessage.warning('最多只能上传 3 张图片')
}

async function handleGenerate() {
  if (!topic.value.trim()) return

  loading.value = true
  error.value = ''

  try {
    // 获取上传的图片
    const images = fileList.value
      .filter(f => f.raw)
      .map(f => f.raw as File)

    const result = await generateOutline(topic.value.trim(), images.length > 0 ? images : undefined)

    if (result.success && result.pages) {
      // 设置主题和大纲
      store.setTopic(topic.value.trim())
      store.setOutline(result.outline || '', result.pages)

      // 创建历史记录
      try {
        const historyResult = await createHistory(
          topic.value.trim(),
          { raw: result.outline || '', pages: result.pages }
        )
        if (historyResult.success && historyResult.record_id) {
          store.setRecordId(historyResult.record_id)
        }
      } catch (e) {
        console.error('Failed to create history:', e)
      }

      // 保存用户图片
      if (images.length > 0) {
        store.userImages = images
      }

      // 清空输入
      topic.value = ''
      fileList.value = []

      // 跳转到大纲编辑页
      router.push('/ai-create/outline')
    } else {
      error.value = result.error || '生成大纲失败'
    }
  } catch (e: any) {
    error.value = e.message || '网络错误，请重试'
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.ai-create-container {
  padding: 20px;
  max-width: 800px;
  margin: 0 auto;
}

.main-card {
  margin-bottom: 20px;
}

.card-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.input-section {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.upload-section {
  margin-top: 10px;
}

.generate-btn {
  width: 100%;
  height: 48px;
  font-size: 16px;
}

.tips-card {
  background: #f5f7fa;
}

:deep(.el-upload--picture-card) {
  width: 100px;
  height: 100px;
}

:deep(.el-upload-list--picture-card .el-upload-list__item) {
  width: 100px;
  height: 100px;
}
</style>
