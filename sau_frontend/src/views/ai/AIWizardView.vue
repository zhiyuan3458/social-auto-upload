<template>
  <div class="ai-wizard">
    <el-card class="card">
      <template #header>
        <div class="header">
          <div class="title">
            <span>AI 内容向导</span>
            <el-tag :type="contentMode === 'image' ? 'success' : 'primary'" style="margin-left: 10px">
              {{ contentMode === 'image' ? '图文模式' : '视频模式' }}
            </el-tag>
          </div>
          <div class="actions" v-if="contentMode === 'video' && resultReady">
            <el-button type="primary" @click="goToPublish" :disabled="!selectedTitle || !tagsText">
              带标题/话题去发布
            </el-button>
          </div>
        </div>
      </template>

      <!-- 步骤条 -->
      <el-steps :active="activeStep" align-center finish-status="success" style="margin-bottom: 16px">
        <el-step title="填写需求" />
        <el-step :title="contentMode === 'image' ? '生成大纲 + 文案' : '生成大纲 + 文案 + 视频提示词'" />
        <el-step :title="contentMode === 'image' ? '编辑大纲 / 生成图片' : '复制提示词 / 发布'" />
      </el-steps>

      <!-- ========== Step 1: 表单 ========== -->
      <div v-show="activeStep === 0" class="step">
        <el-form :model="form" label-width="110px">

          <!-- 内容类型选择（最显眼的位置） -->
          <el-form-item label="内容类型" required>
            <el-radio-group v-model="contentMode" size="large">
              <el-radio-button value="image">
                <el-icon style="margin-right: 4px"><Picture /></el-icon>图文
              </el-radio-button>
              <el-radio-button value="video">
                <el-icon style="margin-right: 4px"><VideoCamera /></el-icon>视频
              </el-radio-button>
            </el-radio-group>
            <div class="mode-hint">
              {{ contentMode === 'image'
                ? '将生成大纲 + 标题/文案/标签 → 跳到图文编辑页生成图片 → 发布'
                : '将生成大纲 + 标题/文案/标签 + 视频提示词包 → 复制提示词去可灵/即梦生成视频 → 发布'
              }}
            </div>
          </el-form-item>

          <el-divider />

          <el-form-item label="活动主题" required>
            <el-input v-model="form.topic" type="textarea" :rows="3" placeholder="例如：中秋节电商线上活动文案宣传" maxlength="500" show-word-limit />
          </el-form-item>

          <el-form-item label="产品/活动信息">
            <el-input v-model="form.product_info" type="textarea" :rows="3" placeholder="品牌/品类/活动机制（满减、券、赠品）、关键规则等" />
          </el-form-item>

          <el-form-item label="目标人群">
            <el-input v-model="form.target_audience" placeholder="例如：25-35 一二线宝妈/送礼人群/办公室白领" />
          </el-form-item>

          <el-form-item label="核心卖点">
            <el-input v-model="form.selling_points" type="textarea" :rows="3" placeholder="用要点列出来，例如：低糖/国风礼盒/48小时发货/买二送一..." />
          </el-form-item>

          <el-form-item label="内容风格">
            <el-select v-model="form.style" placeholder="选择风格" style="width: 260px">
              <el-option label="小红书种草（口语化+强场景）" value="小红书种草（口语化+强场景）" />
              <el-option label="国风中秋（红金/灯笼/团圆氛围）" value="国风中秋（红金/灯笼/团圆氛围）" />
              <el-option label="电商促销硬广（强利益点）" value="电商促销硬广（强利益点）" />
              <el-option label="极简高级（干净留白）" value="极简高级（干净留白）" />
            </el-select>
          </el-form-item>

          <!-- 仅视频模式显示 -->
          <template v-if="contentMode === 'video'">
            <el-form-item label="视频时长">
              <el-radio-group v-model="form.duration_seconds">
                <el-radio-button :value="10">10s</el-radio-button>
                <el-radio-button :value="15">15s</el-radio-button>
                <el-radio-button :value="20">20s</el-radio-button>
              </el-radio-group>
            </el-form-item>

            <el-form-item label="画幅比例">
              <el-radio-group v-model="form.aspect_ratio">
                <el-radio-button value="9:16">9:16</el-radio-button>
                <el-radio-button value="1:1">1:1</el-radio-button>
                <el-radio-button value="16:9">16:9</el-radio-button>
              </el-radio-group>
            </el-form-item>
          </template>

          <el-form-item label="必须包含">
            <el-input v-model="form.must_include" placeholder="例如：活动时间/优惠力度/店铺名/售后信息" />
          </el-form-item>

          <el-form-item label="禁用词">
            <el-input v-model="form.forbidden" placeholder="例如：最/第一/治愈/100%..." />
          </el-form-item>

          <el-form-item>
            <el-button type="primary" :disabled="!form.topic.trim()" @click="activeStep = 1">
              下一步
            </el-button>
          </el-form-item>
        </el-form>
      </div>

      <!-- ========== Step 2: 一键生成 ========== -->
      <div v-show="activeStep === 1" class="step">
        <el-alert
          v-if="error"
          :title="error"
          type="error"
          show-icon
          closable
          @close="error = ''"
          style="margin-bottom: 12px"
        />

        <div class="generate-actions">
          <el-button type="primary" :loading="loading" :disabled="!form.topic.trim()" @click="runAll">
            {{ contentMode === 'image' ? '一键生成（大纲 + 文案）' : '一键生成（大纲 + 文案 + 视频提示词包）' }}
          </el-button>
          <el-button :disabled="loading" @click="activeStep = 0">返回修改</el-button>
          
          <!-- 视频模式：生成视频按钮 -->
          <el-button 
            v-if="contentMode === 'video' && videoPlan" 
            type="warning" 
            :loading="videoGenerating" 
            :disabled="!universalPromptText"
            @click="callVideoGenerate"
          >
            {{ videoGenerating ? '生成视频中...' : '调用 API 生成视频' }}
          </el-button>
          
          <el-button type="success" :disabled="!resultReady" @click="handleNextAfterGenerate">
            {{ contentMode === 'image' ? '去编辑大纲 & 生成图片' : '下一步' }}
          </el-button>
        </div>

        <!-- 视频生成进度提示 -->
        <el-alert 
          v-if="videoGenerating" 
          type="info" 
          :closable="false" 
          style="margin-top: 12px"
        >
          <template #title>
            正在调用视频生成 API，请耐心等待...（可能需要 1-3 分钟）
          </template>
        </el-alert>

        <el-alert 
          v-if="generatedVideoPath" 
          type="success" 
          :closable="false" 
          style="margin-top: 12px"
        >
          <template #title>
            视频已生成并下载到素材库：{{ generatedVideoFilename }}
          </template>
        </el-alert>

        <el-divider />

        <el-collapse v-model="openPanels">
          <el-collapse-item title="大纲（可编辑）" name="outline">
            <el-input v-model="outlineText" type="textarea" :rows="10" />
          </el-collapse-item>

          <el-collapse-item title="文案/标题/标签（可编辑）" name="content">
            <el-form label-width="90px">
              <el-form-item label="标题">
                <el-select v-model="selectedTitle" placeholder="选择一个标题" style="width: 100%">
                  <el-option v-for="t in titles" :key="t" :label="t" :value="t" />
                </el-select>
              </el-form-item>
              <el-form-item label="正文">
                <el-input v-model="copywriting" type="textarea" :rows="8" />
              </el-form-item>
              <el-form-item label="标签">
                <el-input v-model="tagsText" placeholder="逗号分隔，如：中秋礼盒,送礼,电商活动" />
              </el-form-item>
            </el-form>
          </el-collapse-item>

          <!-- 仅视频模式显示视频提示词面板 -->
          <el-collapse-item v-if="contentMode === 'video'" title="视频提示词包（可灵/即梦通用）" name="video">
            <div v-if="videoPlanJson" class="video-plan">
              <div class="copy-row">
                <el-button size="small" @click="copyText(universalPromptText)">复制【通用版提示词】</el-button>
                <el-button size="small" @click="copyText(kelingPromptText)">复制【可灵版提示词】</el-button>
                <el-button size="small" @click="copyText(jimengPromptText)">复制【即梦版提示词】</el-button>
                <el-button size="small" @click="copyText(videoPlanJson)">复制【完整JSON】</el-button>
              </div>
              <el-input :model-value="videoPlanJson" type="textarea" :rows="14" readonly />
            </div>
            <el-empty v-else description="还没有生成视频提示词包" />
          </el-collapse-item>
        </el-collapse>
      </div>

      <!-- ========== Step 3: 引导后续 ========== -->
      <div v-show="activeStep === 2" class="step">

        <!-- ====== 图文模式: 直接跳到图文编辑流程 ====== -->
        <template v-if="contentMode === 'image'">
          <el-result icon="success" title="大纲 & 文案已生成" sub-title="点击下方按钮进入图文编辑页面，可编辑大纲后一键生成图片">
            <template #extra>
              <el-button type="primary" size="large" @click="jumpToImageFlow">
                进入图文编辑 & 生成图片
              </el-button>
              <el-button @click="activeStep = 1">返回修改</el-button>
            </template>
          </el-result>

          <el-divider />

          <el-descriptions title="已生成的文案参数" :column="1" border>
            <el-descriptions-item label="标题">{{ selectedTitle || '（未选择）' }}</el-descriptions-item>
            <el-descriptions-item label="正文">
              <div style="white-space: pre-wrap; max-height: 200px; overflow: auto">{{ copywriting || '（空）' }}</div>
            </el-descriptions-item>
            <el-descriptions-item label="标签">{{ tagsText || '（空）' }}</el-descriptions-item>
          </el-descriptions>
        </template>

        <!-- ====== 视频模式: 引导复制提示词 + 发布 ====== -->
        <template v-else>
          <el-alert type="info" show-icon :closable="false">
            <template #title>
              你可以把"通用/可灵/即梦提示词"复制到对应生视频模型生成视频；生成完成后，点击上方【带标题/话题去发布】按钮，或手动到发布中心上传视频并发布。
            </template>
          </el-alert>

          <div class="publish-actions">
            <el-button type="primary" @click="goToPublish" :disabled="!selectedTitle || !tagsText">
              带标题/话题去发布
            </el-button>
            <el-button @click="activeStep = 1">返回</el-button>
          </div>

          <el-divider />

          <el-descriptions title="建议发布参数（可复制）" :column="1" border>
            <el-descriptions-item label="标题">{{ selectedTitle || '（未选择）' }}</el-descriptions-item>
            <el-descriptions-item label="标签">{{ tagsText || '（空）' }}</el-descriptions-item>
          </el-descriptions>

          <!-- 快捷复制提示词 -->
          <el-divider content-position="left">视频提示词快捷复制</el-divider>
          <div class="copy-row">
            <el-button @click="copyText(universalPromptText)" :disabled="!universalPromptText">复制通用版</el-button>
            <el-button @click="copyText(kelingPromptText)" :disabled="!kelingPromptText">复制可灵版</el-button>
            <el-button @click="copyText(jimengPromptText)" :disabled="!jimengPromptText">复制即梦版</el-button>
          </div>
        </template>
      </div>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { computed, ref } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { Picture, VideoCamera } from '@element-plus/icons-vue'
import { generateOutline, generateContent, generateVideoPlan, generateVideo } from '@/api/ai'
import { usePublishPresetStore } from '@/stores/publishPreset'
import { useAIGeneratorStore } from '@/stores/aiGenerator'

const router = useRouter()
const publishPresetStore = usePublishPresetStore()
const aiGeneratorStore = useAIGeneratorStore()

// ===== 状态 =====
const contentMode = ref<'image' | 'video'>('video')
const activeStep = ref(0)
const loading = ref(false)
const error = ref('')
const openPanels = ref(['outline', 'content', 'video'])

// 视频生成相关状态
const videoGenerating = ref(false)
const generatedVideoPath = ref('')
const generatedVideoFilename = ref('')
const generatedVideoUrl = ref('')

const form = ref({
  topic: '',
  product_info: '',
  target_audience: '',
  selling_points: '',
  style: '小红书种草（口语化+强场景）',
  duration_seconds: 15,
  aspect_ratio: '9:16',
  must_include: '',
  forbidden: ''
})

// 生成结果
const outlineText = ref('')
const outlinePages = ref<any[]>([]) // 存储解析出的页面结构
const titles = ref<string[]>([])
const selectedTitle = ref('')
const copywriting = ref('')
const tagsText = ref('')
const videoPlan = ref<any | null>(null)

// ===== 计算属性 =====
const resultReady = computed(() => {
  return !!outlineText.value || titles.value.length > 0 || !!videoPlan.value
})

const videoPlanJson = computed(() => {
  if (!videoPlan.value) return ''
  try {
    return JSON.stringify(videoPlan.value, null, 2)
  } catch {
    return String(videoPlan.value)
  }
})

const universalPromptText = computed(() => {
  const pack = videoPlan.value?.prompt_pack?.universal
  if (!pack) return ''
  const shotLines = (pack.shots || []).map((s: any) => `镜头${s.shot}: ${s.prompt}${s.negative_prompt ? `\n负面: ${s.negative_prompt}` : ''}`).join('\n\n')
  return `【全局】\n${pack.global_prompt || ''}\n\n【分镜】\n${shotLines}`.trim()
})

const kelingPromptText = computed(() => {
  const pack = videoPlan.value?.prompt_pack?.keling
  if (!pack) return universalPromptText.value
  const shotLines = (pack.shots || []).map((s: any) => `镜头${s.shot}: ${s.prompt}${s.negative_prompt ? `\n负面: ${s.negative_prompt}` : ''}`).join('\n\n')
  return `【全局】\n${pack.global_prompt || ''}\n\n【分镜】\n${shotLines}`.trim()
})

const jimengPromptText = computed(() => {
  const pack = videoPlan.value?.prompt_pack?.jimeng
  if (!pack) return universalPromptText.value
  const shotLines = (pack.shots || []).map((s: any) => `镜头${s.shot}: ${s.prompt}${s.negative_prompt ? `\n负面: ${s.negative_prompt}` : ''}`).join('\n\n')
  return `【全局】\n${pack.global_prompt || ''}\n\n【分镜】\n${shotLines}`.trim()
})

// ===== 核心方法 =====

/**
 * 一键生成（根据模式走不同流程）
 */
async function runAll() {
  if (!form.value.topic.trim()) return
  loading.value = true
  error.value = ''

  try {
    // 1) 生成大纲（两种模式都需要）
    const outlineRes = await generateOutline(form.value.topic.trim())
    if (!outlineRes.success) throw new Error(outlineRes.error || '生成大纲失败')
    outlineText.value = outlineRes.outline || ''
    outlinePages.value = outlineRes.pages || []

    // 2) 生成文案（两种模式都需要）
    const contentRes = await generateContent(form.value.topic.trim(), outlineText.value)
    if (!contentRes.success) throw new Error(contentRes.error || '生成文案失败')
    titles.value = contentRes.titles || []
    selectedTitle.value = titles.value[0] || ''
    copywriting.value = contentRes.copywriting || ''
    tagsText.value = (contentRes.tags || []).join(',')

    // 3) 视频模式才生成视频提示词包
    if (contentMode.value === 'video') {
      const videoRes = await generateVideoPlan({
        topic: form.value.topic.trim(),
        outline: outlineText.value,
        platform: 'xiaohongshu',
        aspect_ratio: form.value.aspect_ratio,
        duration_seconds: form.value.duration_seconds,
        product_info: form.value.product_info,
        target_audience: form.value.target_audience,
        selling_points: form.value.selling_points,
        style: form.value.style,
        must_include: form.value.must_include,
        forbidden: form.value.forbidden
      })
      if (!videoRes.success) throw new Error(videoRes.error || '生成视频提示词包失败')
      videoPlan.value = videoRes.video_plan || null
    }

    ElMessage.success('生成完成')
  } catch (e: any) {
    error.value = e?.message || '生成失败'
  } finally {
    loading.value = false
  }
}

/**
 * 生成后"下一步"按钮
 */
function handleNextAfterGenerate() {
  if (contentMode.value === 'image') {
    // 图文模式 → 先展示确认页，再跳图文编辑流程
    activeStep.value = 2
  } else {
    // 视频模式 → 跳到提示词/发布页
    activeStep.value = 2
  }
}

/**
 * 图文模式：把大纲 + 文案存到 aiGeneratorStore，跳到图文编辑流程
 */
function jumpToImageFlow() {
  // 1) 重置 aiGenerator store
  aiGeneratorStore.reset()

  // 2) 设置主题 + 大纲
  aiGeneratorStore.setTopic(form.value.topic.trim())

  // 如果有解析出的 pages 就用，否则从大纲文本拆分
  const pages = outlinePages.value.length > 0
    ? outlinePages.value
    : outlineText.value.split(/\n\n<page>\n\n|\n---\n/).map((text: string, idx: number) => ({
        index: idx,
        type: idx === 0 ? 'cover' : 'content',
        content: text.trim()
      })).filter((p: any) => p.content)

  aiGeneratorStore.setOutline(outlineText.value, pages)

  // 3) 设置文案内容
  const tags = tagsText.value
    .split(/[,，、]/)
    .map(t => t.trim().replace(/^#/, ''))
    .filter(t => t.length > 0)
  aiGeneratorStore.setContent(titles.value, copywriting.value, tags)

  // 4) 跳到大纲编辑页（用户可编辑后点"生成图片"进入图片生成流程）
  router.push('/ai-create/outline')
}

/**
 * 视频模式：带标题/话题/视频去发布中心
 */
function goToPublish() {
  if (!selectedTitle.value || !tagsText.value) {
    ElMessage.warning('请先生成标题和话题')
    return
  }

  const tags = tagsText.value
    .split(/[,，、]/)
    .map(t => t.trim().replace(/^#/, ''))
    .filter(t => t.length > 0)

  // 如果已生成视频，自动带上视频文件
  const videoFiles = []
  if (generatedVideoPath.value && generatedVideoFilename.value) {
    const apiBaseUrl = import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:5409'
    videoFiles.push({
      name: generatedVideoFilename.value,
      path: generatedVideoPath.value,
      url: `${apiBaseUrl}/${generatedVideoPath.value}`
    })
  }

  publishPresetStore.setPreset({
    title: selectedTitle.value,
    tags,
    videoFiles,
    platform: 1, // 小红书
    contentType: 'video'
  })

  if (videoFiles.length > 0) {
    ElMessage.success('已带标题/话题/视频到发布中心，请选择账号后发布')
  } else {
    ElMessage.success('已带标题/话题到发布中心，请上传视频后发布')
  }
  
  router.push('/publish-center')
}

/**
 * 复制文本
 */
async function copyText(text: string) {
  if (!text) {
    ElMessage.warning('没有可复制内容')
    return
  }
  try {
    await navigator.clipboard.writeText(text)
    ElMessage.success('已复制')
  } catch {
    ElMessage.error('复制失败（可能需要 HTTPS 或浏览器权限）')
  }
}

/**
 * 调用视频生成 API
 */
async function callVideoGenerate() {
  if (!universalPromptText.value) {
    ElMessage.warning('请先生成视频提示词')
    return
  }

  videoGenerating.value = true
  generatedVideoPath.value = ''
  generatedVideoFilename.value = ''
  generatedVideoUrl.value = ''

  try {
    const result = await generateVideo({
      prompt: universalPromptText.value,
      duration: form.value.duration_seconds,
      aspect_ratio: form.value.aspect_ratio,
      download: true
    })

    if (!result.success) {
      throw new Error(result.error || '视频生成失败')
    }

    generatedVideoPath.value = result.local_path || ''
    generatedVideoFilename.value = result.filename || ''
    generatedVideoUrl.value = result.video_url || ''

    ElMessage.success('视频生成成功！')
  } catch (e: any) {
    ElMessage.error(e?.message || '视频生成失败')
  } finally {
    videoGenerating.value = false
  }
}
</script>

<style scoped lang="scss">
.ai-wizard {
  max-width: 980px;
  margin: 0 auto;
}

.card {
  width: 100%;
}

.header {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.title {
  display: flex;
  align-items: center;
}

.step {
  padding-top: 8px;
}

.mode-hint {
  margin-top: 6px;
  font-size: 12px;
  color: #909399;
  line-height: 1.6;
}

.generate-actions {
  display: flex;
  gap: 10px;
  align-items: center;
}

.copy-row {
  display: flex;
  gap: 8px;
  margin-bottom: 10px;
  flex-wrap: wrap;
}

.publish-actions {
  margin-top: 12px;
  display: flex;
  gap: 10px;
}
</style>
