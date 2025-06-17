<template>
  <div class="home-container">
    <StarBackground />
    <el-row :gutter="20">
      <!-- 左侧问答区域 -->
      <el-col :span="16">
        <el-card class="qa-card">
          <template #header>
            <div class="card-header">
              <span class="section-title">智能问答</span>
            </div>
          </template>

          <div class="chat-container">
            <div v-for="(message, index) in chatHistory" :key="index" class="message" :class="message.type">
              <!-- <el-avatar :icon="message.type === 'user' ? 'User' : 'Assistant'" /> -->
              <!-- 用户消息头像 -->
              <el-avatar v-if="message.type === 'user'" src="/user.png" class="custom-avatar" />
              <!-- 助手消息头像 -->
              <el-avatar v-else src="/assistant.png" class="custom-avatar" />
              <div class="message-content">{{ message.content }}</div>
            </div>
          </div>

          <div class="input-area">
            <el-input v-model="userInput" type="textarea" :rows="3" placeholder="请输入您的问题..."
              @keyup.enter.ctrl="sendQuestion" class="space-input" />
            <el-button type="primary" @click="sendQuestion" :loading="loading" class="space-button">
              发送问题
            </el-button>
          </div>
        </el-card>
      </el-col>

      <!-- 右侧知识库管理区域 -->
      <el-col :span="8">
        <el-card class="kb-card">
          <template #header>
            <div class="card-header">
              <span class="section-title">知识库管理</span>
            </div>
          </template>

          <el-tabs class="space-tabs">
            <el-tab-pane label="网页导入">
              <el-form>
                <el-form-item label="URL">
                  <el-input v-model="webUrl" placeholder="请输入网页URL" class="space-input" />
                </el-form-item>
                <el-button type="primary" @click="importWebPage" class="space-button">导入网页</el-button>
              </el-form>
            </el-tab-pane>

            <el-tab-pane label="文件导入">
              <el-upload class="upload-demo space-upload" drag action="/api/upload" :on-success="handleUploadSuccess"
                :on-error="handleUploadError" :before-upload="beforeUpload">
                <el-icon class="el-icon--upload"><upload-filled /></el-icon>
                <div class="el-upload__text">
                  拖拽文件到此处或 <em>点击上传</em>
                </div>
                <template #tip>
                  <div class="el-upload__tip">
                    支持 .txt, .md, .pdf 格式文件
                  </div>
                </template>
              </el-upload>
            </el-tab-pane>

            <el-tab-pane label="知识库列表">
              <el-table :data="knowledgeBase" style="width: 100%" class="space-table">
                <el-table-column prop="name" label="名称" />
                <el-table-column prop="type" label="类型" />
                <el-table-column prop="date" label="导入时间" />
                <el-table-column label="操作">
                  <template #default="scope">
                    <el-button type="danger" size="small" @click="deleteKnowledge(scope.row)" class="space-button">
                      删除
                    </el-button>
                  </template>
                </el-table-column>
              </el-table>
            </el-tab-pane>
          </el-tabs>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { ElMessage } from 'element-plus'
import { UploadFilled } from '@element-plus/icons-vue'
import axios from 'axios'
import StarBackground from '@/components/StarBackground.vue'

const userInput = ref('')
const loading = ref(false)
const webUrl = ref('')
const chatHistory = ref([])
const knowledgeBase = ref([])

const sendQuestion = async () => {
  if (!userInput.value.trim()) return

  chatHistory.value.push({
    type: 'user',
    content: userInput.value
  })

  loading.value = true
  try {
    const response = await axios.post('/api/ask', {
      question: userInput.value
    })

    chatHistory.value.push({
      type: 'assistant',
      content: response.data.answer
    })
  } catch (error) {
    ElMessage.error('获取答案失败，请稍后重试')
  } finally {
    loading.value = false
    userInput.value = ''
  }
}

const importWebPage = async () => {
  if (!webUrl.value) {
    ElMessage.warning('请输入有效的URL')
    return
  }

  try {
    await axios.post('/api/import/web', {
      url: webUrl.value
    })
    ElMessage.success('网页导入成功')
    webUrl.value = ''
    loadKnowledgeBase()
  } catch (error) {
    ElMessage.error('网页导入失败')
  }
}

const handleUploadSuccess = (response) => {
  ElMessage.success('文件上传成功')
  loadKnowledgeBase()
}

const handleUploadError = () => {
  ElMessage.error('文件上传失败')
}

const beforeUpload = (file) => {
  const validTypes = ['.txt', '.md', '.pdf']
  const extension = file.name.substring(file.name.lastIndexOf('.')).toLowerCase()
  if (!validTypes.includes(extension)) {
    ElMessage.error('只支持 .txt, .md, .pdf 格式文件')
    return false
  }
  return true
}

const deleteKnowledge = async (row) => {
  try {
    await axios.delete(`/api/knowledge/${row.id}`)
    ElMessage.success('删除成功')
    loadKnowledgeBase()
  } catch (error) {
    ElMessage.error('删除失败')
  }
}

const loadKnowledgeBase = async () => {
  try {
    const response = await axios.get('/api/knowledge')
    knowledgeBase.value = response.data
  } catch (error) {
    ElMessage.error('获取知识库列表失败')
  }
}

// 初始加载知识库列表
loadKnowledgeBase()
</script>

<style scoped>
.home-container {
  padding: 20px;
  position: relative;
  min-height: calc(100vh - 60px);
  background: transparent;
  border-radius: var(--border-radius);
  box-shadow: none;
}

.qa-card {
  margin-bottom: 20px;
  background: rgba(135, 206, 235, 0.1);
  /* 浅蓝色，更低透明度 */
  backdrop-filter: blur(10px);
  border: var(--border-glow);
  box-shadow: var(--shadow-card);
}

.kb-card {
  margin-bottom: 20px;
  background: rgba(10, 25, 47, 0.4);
  /* 深蓝色，更低透明度 */
  backdrop-filter: blur(10px);
  border: var(--border-glow);
  box-shadow: var(--shadow-card);
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.section-title {
  font-family: var(--font-title);
  color: var(--text-white);
  font-size: 1.2rem;
}

.chat-container {
  height: 400px;
  overflow-y: auto;
  padding: 20px;
  /* background: rgba(0, 0, 51, 0.2); 深空蓝，带透明度 */
  background: rgba(10, 25, 47, 0.4);
  border-radius: var(--border-radius);
  margin-bottom: 20px;
  border: 1px solid rgba(255, 255, 255, 0.1);
}

.message {
  display: flex;
  margin-bottom: 20px;
  align-items: flex-start;
}

.message.user {
  flex-direction: row-reverse;
}

.message-content {
  margin: 0 10px;
  padding: 10px;
  border-radius: var(--border-radius);
  max-width: 70%;
  background: rgba(255, 255, 255, 0.1);
  backdrop-filter: blur(5px);
}

.user .message-content {
  background: var(--primary-light);
  color: var(--primary-dark);
}

.assistant .message-content {
  background: var(--accent-purple);
  color: var(--text-white);
}

.input-area {
  display: flex;
  gap: 10px;
}

.space-input {
  background: rgba(255, 255, 255, 0.1);
  border: 1px solid rgba(255, 255, 255, 0.2);
}

.space-input :deep(.el-input__inner) {
  background: rgba(255, 255, 255, 0.1);
  border: 1px solid rgba(255, 255, 255, 0.2);
  color: var(--primary-dark);
}

.space-input :deep(.el-input__inner)::placeholder {
  color: var(--primary-dark);
}

.space-input :deep(.el-textarea__inner)::placeholder {
  color: var(--text-light);
}

.space-input :deep(.el-textarea__inner) {
  background: rgba(255, 255, 255, 0.1);
  border: 1px solid rgba(255, 255, 255, 0.2);
  color: var(--text-white);
}

.space-button {
  background: linear-gradient(45deg, var(--primary-light), var(--accent-purple));
  border: none;
  transition: transform var(--transition-fast), box-shadow var(--transition-fast);
}

.space-button:hover {
  transform: translateY(-2px);
  box-shadow: var(--shadow-glow);
}

.space-tabs :deep(.el-tabs__item) {
  color: var(--text-light);
}

.space-tabs :deep(.el-tabs__item.is-active) {
  color: var(--accent-gold);
}

.space-upload {
  border: 2px dashed rgba(255, 255, 255, 0.2);
  background: rgba(10, 25, 47, 0.5);
  border-radius: var(--border-radius);
}

.space-upload :deep(.el-upload-dragger) {
  background: rgba(10, 25, 47, 0.5);
  border: 2px dashed rgba(255, 255, 255, 0.3);
  border-radius: var(--border-radius);
  transition: border-color var(--transition-fast);
}

.space-upload :deep(.el-upload__tip) {
  text-align: center;
  color: var(--text-light);
}

.space-table {
  background: transparent;
  color: var(--text-white);
}

.space-table :deep(th) {
  background: rgba(255, 255, 255, 0.1);
  color: var(--text-white);
}

.space-table :deep(td) {
  background: transparent;
  color: var(--text-light);
}

.kb-card .el-form {
  display: flex;
  flex-direction: column;
}

.kb-card .el-form .space-button {
  align-self: center;
  margin-top: 10px;
}

/* 自定义滚动条 */
.chat-container::-webkit-scrollbar {
  width: 6px;
}

.chat-container::-webkit-scrollbar-track {
  background: rgba(255, 255, 255, 0.1);
}

.chat-container::-webkit-scrollbar-thumb {
  background: var(--accent-purple);
  border-radius: 3px;
}

.chat-container::-webkit-scrollbar-thumb:hover {
  background: var(--accent-gold);
}
</style>