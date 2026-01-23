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

const testingText = ref(false)
const savingText = ref(false)
const savingImage = ref(false)

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
</style>
