<template>
  <div class="outline-container">
    <el-card>
      <template #header>
        <div class="card-header">
          <div>
            <span class="title">编辑大纲</span>
            <el-tag size="small" style="margin-left: 10px">{{ store.outline.pages.length }} 页</el-tag>
          </div>
          <div class="actions">
            <el-button @click="router.push('/ai-create')">返回</el-button>
            <el-button type="primary" @click="handleStartGenerate">
              开始生成图片
            </el-button>
          </div>
        </div>
      </template>

      <div class="topic-display">
        <strong>主题：</strong>{{ store.topic }}
      </div>

      <div class="pages-list">
        <el-card 
          v-for="page in store.outline.pages" 
          :key="page.index"
          class="page-card"
          shadow="hover"
        >
          <template #header>
            <div class="page-header">
              <div>
                <el-tag :type="getPageTypeColor(page.type)" size="small">
                  {{ getPageTypeLabel(page.type) }}
                </el-tag>
                <span class="page-number">第 {{ page.index + 1 }} 页</span>
              </div>
              <div>
                <el-button 
                  type="danger" 
                  size="small" 
                  text
                  @click="handleDeletePage(page.index)"
                  :disabled="store.outline.pages.length <= 1"
                >
                  删除
                </el-button>
              </div>
            </div>
          </template>

          <el-input
            v-model="page.content"
            type="textarea"
            :rows="4"
            placeholder="编辑页面内容..."
            @change="handleUpdatePage(page.index, page.content)"
          />
        </el-card>

        <!-- 添加页面按钮 -->
        <el-button 
          type="primary" 
          plain 
          class="add-page-btn"
          @click="handleAddPage"
        >
          + 添加页面
        </el-button>
      </div>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { useAIGeneratorStore } from '@/stores/aiGenerator'
import type { PageType } from '@/types/ai'

const router = useRouter()
const store = useAIGeneratorStore()

onMounted(() => {
  if (store.outline.pages.length === 0) {
    router.push('/ai-create')
  }
})

function getPageTypeLabel(type: PageType): string {
  const labels: Record<PageType, string> = {
    cover: '封面',
    content: '内容',
    summary: '总结'
  }
  return labels[type] || '内容'
}

function getPageTypeColor(type: PageType): string {
  const colors: Record<PageType, string> = {
    cover: 'warning',
    content: '',
    summary: 'success'
  }
  return colors[type] || ''
}

function handleUpdatePage(index: number, content: string) {
  store.updatePage(index, content)
}

function handleDeletePage(index: number) {
  ElMessageBox.confirm('确定要删除这一页吗？', '提示', {
    confirmButtonText: '确定',
    cancelButtonText: '取消',
    type: 'warning'
  }).then(() => {
    store.deletePage(index)
    ElMessage.success('删除成功')
  }).catch(() => {})
}

function handleAddPage() {
  store.addPage('content', '[内容]\n\n请输入页面内容...')
  ElMessage.success('添加成功')
}

function handleStartGenerate() {
  if (store.outline.pages.length === 0) {
    ElMessage.warning('请至少添加一页内容')
    return
  }
  router.push('/ai-create/generate')
}
</script>

<style scoped>
.outline-container {
  padding: 20px;
  max-width: 900px;
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

.topic-display {
  padding: 15px;
  background: #f5f7fa;
  border-radius: 8px;
  margin-bottom: 20px;
}

.pages-list {
  display: flex;
  flex-direction: column;
  gap: 15px;
}

.page-card {
  transition: all 0.3s;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.page-number {
  margin-left: 10px;
  color: #909399;
  font-size: 14px;
}

.add-page-btn {
  width: 100%;
  height: 50px;
  border-style: dashed;
}
</style>
