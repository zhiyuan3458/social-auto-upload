<template>
  <div class="settings-container">
    <el-card>
      <template #header>
        <span class="title">AI 服务配置</span>
      </template>

      <el-tabs v-model="activeTab">
        <!-- 文本生成配置 -->
        <el-tab-pane label="文本生成" name="text">
          <el-form 
            :model="textConfig" 
            label-width="120px"
            label-position="left"
          >
            <el-form-item label="API 地址">
              <el-input 
                v-model="textConfig.base_url" 
                placeholder="例如：https://api.openai.com/v1"
              />
            </el-form-item>
            <el-form-item label="API Key">
              <el-input 
                v-model="textConfig.api_key" 
                type="password"
                show-password
                placeholder="输入 API Key"
              />
            </el-form-item>
            <el-form-item label="模型">
              <el-input 
                v-model="textConfig.model" 
                placeholder="例如：gpt-4, gpt-3.5-turbo"
              />
            </el-form-item>
            <el-form-item label="温度">
              <el-slider 
                v-model="textConfig.temperature" 
                :min="0" 
                :max="1" 
                :step="0.1"
                show-input
              />
            </el-form-item>
            <el-form-item>
              <el-button type="primary" @click="testTextConnection" :loading="testingText">
                测试连接
              </el-button>
              <el-button @click="saveTextConfig" :loading="savingText">
                保存配置
              </el-button>
            </el-form-item>
          </el-form>
        </el-tab-pane>

        <!-- 图片生成配置 -->
        <el-tab-pane label="图片生成" name="image">
          <el-form 
            :model="imageConfig" 
            label-width="120px"
            label-position="left"
          >
            <el-form-item label="API 地址">
              <el-input 
                v-model="imageConfig.base_url" 
                placeholder="例如：https://api.openai.com/v1"
              />
            </el-form-item>
            <el-form-item label="API Key">
              <el-input 
                v-model="imageConfig.api_key" 
                type="password"
                show-password
                placeholder="输入 API Key"
              />
            </el-form-item>
            <el-form-item label="模型">
              <el-input 
                v-model="imageConfig.model" 
                placeholder="例如：dall-e-3"
              />
            </el-form-item>
            <el-form-item label="默认尺寸">
              <el-select v-model="imageConfig.default_size">
                <el-option label="1024x1024" value="1024x1024" />
                <el-option label="1024x1792" value="1024x1792" />
                <el-option label="1792x1024" value="1792x1024" />
              </el-select>
            </el-form-item>
            <el-form-item label="质量">
              <el-select v-model="imageConfig.quality">
                <el-option label="标准" value="standard" />
                <el-option label="高清" value="hd" />
              </el-select>
            </el-form-item>
            <el-form-item>
              <el-button @click="saveImageConfig" :loading="savingImage">
                保存配置
              </el-button>
            </el-form-item>
          </el-form>
        </el-tab-pane>

        <!-- 视频生成配置（新增） -->
        <el-tab-pane label="视频生成 API" name="video">
          <el-alert type="info" :closable="false" style="margin-bottom: 20px">
            <template #title>
              配置可灵/即梦等视频生成 API，系统将自动调用并下载视频到素材库
            </template>
          </el-alert>

          <el-form 
            :model="videoConfig" 
            label-width="140px"
            label-position="left"
          >
            <el-form-item label="API 地址" required>
              <el-input 
                v-model="videoConfig.api_url" 
                placeholder="例如：https://api.keling.com/v1/generate"
              />
            </el-form-item>

            <el-form-item label="请求方法">
              <el-select v-model="videoConfig.method" style="width: 200px">
                <el-option label="POST" value="POST" />
                <el-option label="GET" value="GET" />
              </el-select>
            </el-form-item>

            <el-form-item label="请求头（JSON）">
              <el-input 
                v-model="videoConfig.headers" 
                type="textarea"
                :rows="5"
                placeholder='{"Authorization": "Bearer YOUR_API_KEY", "Content-Type": "application/json"}'
              />
              <div class="hint">每行一个键值对，格式为 JSON 对象</div>
            </el-form-item>

            <el-form-item label="请求体模板（JSON）">
              <el-input 
                v-model="videoConfig.body_template" 
                type="textarea"
                :rows="8"
                placeholder='{"prompt": "{{prompt}}", "duration": {{duration}}, "aspect_ratio": "{{aspect_ratio}}"}'
              />
              <div class="hint">
                支持变量：{{prompt}}（提示词）、{{duration}}（时长）、{{aspect_ratio}}（画幅）
              </div>
            </el-form-item>

            <el-form-item label="响应视频URL路径">
              <el-input 
                v-model="videoConfig.response_video_path" 
                placeholder="例如：data.video_url 或 result.url"
              />
              <div class="hint">用 . 分隔嵌套路径，如：data.result.video_url</div>
            </el-form-item>

            <el-form-item label="是否需要轮询">
              <el-switch v-model="videoConfig.need_polling" />
              <div class="hint">某些 API 返回任务ID，需要轮询获取结果</div>
            </el-form-item>

            <template v-if="videoConfig.need_polling">
              <el-form-item label="任务ID路径">
                <el-input 
                  v-model="videoConfig.task_id_path" 
                  placeholder="例如：data.task_id"
                />
              </el-form-item>

              <el-form-item label="查询地址">
                <el-input 
                  v-model="videoConfig.poll_url" 
                  placeholder="例如：https://api.keling.com/v1/task/{{task_id}}"
                />
                <div class="hint">支持变量：{{task_id}}</div>
              </el-form-item>

              <el-form-item label="轮询间隔（秒）">
                <el-input-number v-model="videoConfig.poll_interval" :min="1" :max="60" />
              </el-form-item>

              <el-form-item label="最大轮询次数">
                <el-input-number v-model="videoConfig.max_poll_count" :min="5" :max="100" />
              </el-form-item>

              <el-form-item label="完成状态值">
                <el-input 
                  v-model="videoConfig.success_status" 
                  placeholder="例如：completed 或 success"
                />
                <div class="hint">响应中表示任务完成的状态值</div>
              </el-form-item>

              <el-form-item label="状态字段路径">
                <el-input 
                  v-model="videoConfig.status_path" 
                  placeholder="例如：data.status"
                />
              </el-form-item>
            </template>

            <el-form-item>
              <el-button type="primary" @click="saveVideoConfig" :loading="savingVideo">
                保存配置
              </el-button>
              <el-button @click="testVideoConfig" :loading="testingVideo">
                测试配置
              </el-button>
            </el-form-item>
          </el-form>
        </el-tab-pane>
      </el-tabs>
    </el-card>

    <!-- 使用说明 -->
    <el-card style="margin-top: 20px">
      <template #header>
        <span>配置说明</span>
      </template>
      <div class="tips">
        <p><strong>支持的 API 类型：</strong></p>
        <ul>
          <li>OpenAI 官方 API</li>
          <li>OpenAI 兼容的第三方 API</li>
          <li>公司内部 AI 服务（需要符合 OpenAI API 格式）</li>
        </ul>
        <p><strong>配置步骤：</strong></p>
        <ol>
          <li>输入 API 地址（不含 /chat/completions 后缀）</li>
          <li>输入 API Key</li>
          <li>选择或输入模型名称</li>
          <li>点击"测试连接"验证配置</li>
          <li>点击"保存配置"完成设置</li>
        </ol>
      </div>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { getAIConfig, updateAIConfig, testAIConnection } from '@/api/ai'

const activeTab = ref('text')

const textConfig = reactive({
  type: 'openai_compatible',
  base_url: '',
  api_key: '',
  model: 'gpt-4',
  temperature: 0.7
})

const imageConfig = reactive({
  type: 'openai_compatible',
  base_url: '',
  api_key: '',
  model: 'dall-e-3',
  default_size: '1024x1024',
  quality: 'standard'
})

const videoConfig = reactive({
  api_url: '',
  method: 'POST',
  headers: '{"Authorization": "Bearer YOUR_API_KEY", "Content-Type": "application/json"}',
  body_template: '{"prompt": "{{prompt}}", "duration": {{duration}}, "aspect_ratio": "{{aspect_ratio}}"}',
  response_video_path: 'data.video_url',
  need_polling: false,
  task_id_path: 'data.task_id',
  poll_url: '',
  poll_interval: 5,
  max_poll_count: 30,
  success_status: 'completed',
  status_path: 'data.status'
})

const testingText = ref(false)
const savingText = ref(false)
const savingImage = ref(false)
const savingVideo = ref(false)
const testingVideo = ref(false)

onMounted(async () => {
  try {
    const result = await getAIConfig()
    if (result.success && result.config) {
      // 加载文本配置
      const textProviders = result.config.text_generation?.providers || {}
      const activeTextProvider = result.config.text_generation?.active_provider || 'custom'
      const textProviderConfig = textProviders[activeTextProvider] || {}
      
      textConfig.base_url = textProviderConfig.base_url || ''
      textConfig.api_key = textProviderConfig.api_key || ''
      textConfig.model = textProviderConfig.model || 'gpt-4'
      textConfig.temperature = textProviderConfig.temperature || 0.7

      // 加载图片配置
      const imageProviders = result.config.image_generation?.providers || {}
      const activeImageProvider = result.config.image_generation?.active_provider || 'custom'
      const imageProviderConfig = imageProviders[activeImageProvider] || {}
      
      imageConfig.base_url = imageProviderConfig.base_url || ''
      imageConfig.api_key = imageProviderConfig.api_key || ''
      imageConfig.model = imageProviderConfig.model || 'dall-e-3'
      imageConfig.default_size = imageProviderConfig.default_size || '1024x1024'
      imageConfig.quality = imageProviderConfig.quality || 'standard'

      // 加载视频生成配置
      const videoGenConfig = result.config.video_generation || {}
      if (videoGenConfig.api_url) {
        videoConfig.api_url = videoGenConfig.api_url
        videoConfig.method = videoGenConfig.method || 'POST'
        videoConfig.headers = JSON.stringify(videoGenConfig.headers || {}, null, 2)
        videoConfig.body_template = JSON.stringify(videoGenConfig.body_template || {}, null, 2)
        videoConfig.response_video_path = videoGenConfig.response_video_path || 'data.video_url'
        videoConfig.need_polling = videoGenConfig.need_polling || false
        videoConfig.task_id_path = videoGenConfig.task_id_path || 'data.task_id'
        videoConfig.poll_url = videoGenConfig.poll_url || ''
        videoConfig.poll_interval = videoGenConfig.poll_interval || 5
        videoConfig.max_poll_count = videoGenConfig.max_poll_count || 30
        videoConfig.success_status = videoGenConfig.success_status || 'completed'
        videoConfig.status_path = videoGenConfig.status_path || 'data.status'
      }
    }
  } catch (e) {
    console.error('Failed to load config:', e)
  }
})

async function testTextConnection() {
  if (!textConfig.base_url || !textConfig.api_key) {
    ElMessage.warning('请先填写 API 地址和 API Key')
    return
  }

  testingText.value = true
  try {
    const result = await testAIConnection({
      type: 'openai_compatible',
      api_key: textConfig.api_key,
      base_url: textConfig.base_url,
      model: textConfig.model
    })

    if (result.success) {
      ElMessage.success('连接成功')
    } else {
      ElMessage.error(result.error || '连接失败')
    }
  } catch (e: any) {
    ElMessage.error(e.message || '连接失败')
  } finally {
    testingText.value = false
  }
}

async function saveTextConfig() {
  savingText.value = true
  try {
    const result = await updateAIConfig({
      text_generation: {
        active_provider: 'custom',
        providers: {
          custom: {
            type: 'openai_compatible',
            name: '自定义 API',
            base_url: textConfig.base_url,
            api_key: textConfig.api_key,
            model: textConfig.model,
            temperature: textConfig.temperature,
            max_output_tokens: 4096
          }
        }
      }
    })

    if (result.success) {
      ElMessage.success('保存成功')
    } else {
      ElMessage.error(result.error || '保存失败')
    }
  } catch (e: any) {
    ElMessage.error(e.message || '保存失败')
  } finally {
    savingText.value = false
  }
}

async function saveImageConfig() {
  savingImage.value = true
  try {
    const result = await updateAIConfig({
      image_generation: {
        active_provider: 'custom',
        providers: {
          custom: {
            type: 'openai_compatible',
            name: '自定义图片 API',
            base_url: imageConfig.base_url,
            api_key: imageConfig.api_key,
            model: imageConfig.model,
            default_size: imageConfig.default_size,
            quality: imageConfig.quality
          }
        }
      }
    })

    if (result.success) {
      ElMessage.success('保存成功')
    } else {
      ElMessage.error(result.error || '保存失败')
    }
  } catch (e: any) {
    ElMessage.error(e.message || '保存失败')
  } finally {
    savingImage.value = false
  }
}

async function saveVideoConfig() {
  if (!videoConfig.api_url.trim()) {
    ElMessage.warning('请填写 API 地址')
    return
  }

  savingVideo.value = true
  try {
    // 解析 JSON 字符串
    let headers = {}
    let bodyTemplate = {}
    
    try {
      headers = JSON.parse(videoConfig.headers || '{}')
    } catch {
      ElMessage.error('请求头 JSON 格式错误')
      return
    }
    
    try {
      bodyTemplate = JSON.parse(videoConfig.body_template || '{}')
    } catch {
      ElMessage.error('请求体模板 JSON 格式错误')
      return
    }

    const result = await updateAIConfig({
      video_generation: {
        api_url: videoConfig.api_url,
        method: videoConfig.method,
        headers,
        body_template: bodyTemplate,
        response_video_path: videoConfig.response_video_path,
        need_polling: videoConfig.need_polling,
        task_id_path: videoConfig.task_id_path,
        poll_url: videoConfig.poll_url,
        poll_interval: videoConfig.poll_interval,
        max_poll_count: videoConfig.max_poll_count,
        success_status: videoConfig.success_status,
        status_path: videoConfig.status_path
      }
    })

    if (result.success) {
      ElMessage.success('保存成功')
    } else {
      ElMessage.error(result.error || '保存失败')
    }
  } catch (e: any) {
    ElMessage.error(e.message || '保存失败')
  } finally {
    savingVideo.value = false
  }
}

async function testVideoConfig() {
  ElMessage.info('测试功能待实现，请先保存配置后在向导页实际调用')
}
</script>

<style scoped>
.settings-container {
  padding: 20px;
  max-width: 800px;
  margin: 0 auto;
}

.title {
  font-size: 18px;
  font-weight: 600;
}

.tips {
  line-height: 1.8;
  color: #606266;
}

.tips ul, .tips ol {
  padding-left: 20px;
}

.tips li {
  margin: 5px 0;
}

.hint {
  font-size: 12px;
  color: #909399;
  margin-top: 4px;
}
</style>
