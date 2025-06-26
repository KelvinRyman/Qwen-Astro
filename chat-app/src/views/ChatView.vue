<template>
  <div class="chat-view">
    <!-- 欢迎界面：只在新对话模式且没有消息时显示 -->
    <div v-if="isNewChatMode && !hasMessages" class="welcome-container">
      <h1>{{ currentWelcomeMessage }}</h1>
    </div>
    
    <!-- 消息列表：当有消息或非新对话模式时显示 -->
    <div v-else ref="messagesContainerRef" class="messages-container">
      <div v-if="isLoading" class="loading-message">加载中...</div>
      <div v-else-if="currentConversation">
        <div v-for="(message, index) in currentConversation.messages" :key="index" class="message-wrapper">
          <!-- 用户消息 -->
          <div v-if="message.role === 'user'" class="user-message-wrapper">
            <div class="user-message">
              <MessageContent :content="message.content" message-type="user" />
            </div>
            <!-- 用户消息操作按钮 -->
            <div class="message-actions user-message-actions">
              <button class="message-action-button" title="复制" @click="copyToClipboard(message.content)">
                <Icon name="copy" />
                <span class="tooltip">复制</span>
              </button>
              <button class="message-action-button" title="重新生成">
                <Icon name="refresh" />
                <span class="tooltip">重新生成</span>
              </button>
            </div>
          </div>
          
          <!-- 助手消息 -->
          <div v-else class="assistant-message-wrapper">
            <!-- 引用卡片：在消息内容上方显示 -->
            <CitationContainer
              v-if="message.sources && message.sources.length > 0"
              :sources="message.sources"
            />
            <div class="assistant-message">
              <MessageContent
                :content="message.content"
                :is-generating="message.isGenerating"
                message-type="assistant"
              />
            </div>
            <!-- 只在消息生成完毕后显示操作按钮 -->
            <div v-if="!message.isGenerating" class="message-actions">
              <button class="message-action-button" title="复制" @click="copyToClipboard(message.content)">
                <Icon name="copy" />
                <span class="tooltip">复制</span>
              </button>
              <button class="message-action-button" title="重新生成" @click="regenerateMessage(index)">
                <Icon name="refresh" />
                <span class="tooltip">重新生成</span>
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
    
    <!-- 输入区域：始终显示 -->
    <div class="input-container">
      <!-- 图片预览区域 -->
      <div v-if="hasImages" class="image-preview-container">
        <ImageThumbnail :images="selectedImages" @remove="removeImage" />
      </div>

      <!-- 错误提示 -->
      <div v-if="imageUploadErrors.length > 0" class="error-toast">
        <div v-for="(error, index) in imageUploadErrors" :key="index" class="error-message">
          {{ error.file ? `${error.file}: ` : '' }}{{ error.error }}
        </div>
      </div>

      <div class="input-box-wrapper">
        <textarea
          ref="textareaRef"
          v-model="chatInputText"
          class="chat-input"
          placeholder="询问任何问题"
          rows="1"
          @input="handleInput"
          @keydown.enter.prevent="handleEnterKey"
        ></textarea>
        <div class="input-actions">
          <div class="actions-left">
            <button
              class="input-icon-button"
              :class="{ 'image-selected': hasImages, 'drag-over': isDragOver }"
              @click="openFileSelector"
              @dragover="onDragOver"
              @dragenter="onDragEnter"
              @dragleave="onDragLeave"
              @drop="onDrop"
              title="上传图片"
            >
              <Icon name="plus" />
            </button>
            <div ref="toolMenuContainerRef" class="tool-button-wrapper">
              <button
                class="input-icon-button"
                :class="{ 'tool-selected': hasSelectedTool }"
                @click="isToolMenuOpen = !isToolMenuOpen"
              >
                <Icon name="tool" />
              </button>
              <div v-if="isToolMenuOpen" class="tool-menu">
                <button
                  class="tool-menu-item"
                  :class="{ 'selected': isDeepThinkingEnabled }"
                  @click="toggleDeepThinking"
                >
                  <div class="left-content">
                    <Icon name="think" />
                    <span>深度思考</span>
                  </div>
                  <Icon v-if="isDeepThinkingEnabled" name="check" class="check-icon" />
                </button>
                <button
                  class="tool-menu-item"
                  :class="{ 'selected': isWebSearchEnabled }"
                  @click="toggleWebSearch"
                >
                  <div class="left-content">
                    <Icon name="web" />
                    <span>搜索网页</span>
                  </div>
                  <Icon v-if="isWebSearchEnabled" name="check" class="check-icon" />
                </button>
              </div>
            </div>
            <div ref="knowledgeMenuContainerRef" class="knowledge-button-wrapper">
              <button
                class="input-icon-button"
                :class="{
                  'knowledge-selected': hasSelectedKnowledgeBase,
                  'disabled': !canSelectKnowledgeBase
                }"
                :disabled="!canSelectKnowledgeBase"
                @click="toggleKnowledgeBaseModal"
                :title="!canSelectKnowledgeBase ? '图片模式下无法使用知识库' : '选择知识库'"
              >
                <Icon name="knowledge" />
              </button>
            </div>
            <div ref="agentMenuContainerRef" class="agent-button-wrapper">
              <button
                class="input-icon-button"
                :class="{ 'agent-selected': hasSelectedAgent }"
                @click="toggleAgentModal"
              >
                <Icon name="agent" />
              </button>
            </div>
          </div>
          <div class="actions-right">
            <button class="input-icon-button">
              <Icon name="microphone" />
            </button>
            <button
              class="input-icon-button send-button"
              :class="{ 'has-text': chatInputText.trim() !== '' }"
              @click="sendMessage"
              :disabled="isGenerating || !chatInputText.trim()"
            >
              <Icon name="send" />
            </button>
          </div>
        </div>
      </div>
    </div>
    
    <!-- 知识库选择弹窗 -->
    <KnowledgeBaseSelectModal
      v-if="isKnowledgeBaseModalOpen"
      :conversation-id="currentConversationId"
      :selected-group-ids="currentConversation?.group_ids || []"
      @close="isKnowledgeBaseModalOpen = false"
      @update="handleKnowledgeBaseUpdate"
    />

    <!-- Agent选择弹窗 -->
    <AgentSelectModal
      v-if="isAgentModalOpen"
      :current-agent-id="currentConversation?.agent_id || null"
      @close="isAgentModalOpen = false"
      @select="handleAgentSelect"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted, computed, nextTick, watch } from 'vue'
import { useRoute } from 'vue-router'
import Icon from '@/components/AppIcon.vue'
import { useChatStore } from '@/stores/chat'
import KnowledgeBaseSelectModal from '@/components/KnowledgeBaseSelectModal.vue'
import AgentSelectModal from '@/components/AgentSelectModal.vue'
import CitationContainer from '@/components/CitationContainer.vue'
import MessageContent from '@/components/MessageContent.vue'
import ImageThumbnail from '@/components/ImageThumbnail.vue'
import { useImageUpload } from '@/composables/useImageUpload'
import { extractTextFromMessageContent } from '@/utils/messageUtils'

const welcomeMessages = [
  '一小步和一大步。',
  '天空即为极限！',
  '宇宙没有义务向你解释一切，而我们有。',
  '太空探索本身就是一种自然力量。',
  '地球是人类的摇篮，但人类不能永远停留在摇篮里。',
  '一些不可思议的事情正等待着我们去探索。',
  '直抵群星。',
  '要么我们在宇宙中是孤独的，要么我们并非孤独的。',
]

const currentWelcomeMessage = ref('')
const textareaRef = ref<HTMLTextAreaElement | null>(null)
const chatInputText = ref('') // 用于绑定 textarea 内容
const messagesContainerRef = ref<HTMLElement | null>(null)

const isToolMenuOpen = ref(false)
const toolMenuContainerRef = ref<HTMLElement | null>(null)
const isDeepThinkingEnabled = ref(false)
const isWebSearchEnabled = ref(false)
const knowledgeMenuContainerRef = ref<HTMLElement | null>(null)
const isKnowledgeBaseModalOpen = ref(false)
const agentMenuContainerRef = ref<HTMLElement | null>(null)
const isAgentModalOpen = ref(false)

// 图片上传相关状态
const imageUploadErrors = ref<{ file: string; error: string }[]>([])
const {
  selectedImages,
  isUploading: isImageUploading,
  isDragOver,
  hasImages,
  imageCount,
  openFileSelector,
  removeImage,
  clearImages,
  getImageBase64List,
  onDragOver,
  onDragEnter,
  onDragLeave,
  onDrop
} = useImageUpload({
  maxImages: 5, // 限制最多5张图片
  onError: (errors) => {
    imageUploadErrors.value.push(...errors)
    // 3秒后自动清除错误信息
    setTimeout(() => {
      imageUploadErrors.value = []
    }, 3000)
  },
  onSuccess: (images) => {
    console.log('成功添加图片:', images)
  }
})

// 获取路由和聊天存储
const route = useRoute()
const chatStore = useChatStore()

// 计算属性
const isNewChatMode = computed(() => chatStore.isNewChatMode)
const isLoading = computed(() => chatStore.isLoading)
const isGenerating = computed(() => chatStore.isGeneratingMessage)
const currentConversation = computed(() => chatStore.currentConversation)
const hasMessages = computed(() => 
  currentConversation.value && currentConversation.value.messages.length > 0
)
const currentConversationId = computed(() =>
  currentConversation.value ? currentConversation.value.id : ''
)

// 计算是否选择了知识库
const hasSelectedKnowledgeBase = computed(() => {
  const groupIds = getKnowledgeBaseGroupIds()
  return groupIds.length > 0
})

// 计算是否选择了Agent
const hasSelectedAgent = computed(() => {
  return currentConversation.value?.agent_id != null
})

// 计算是否选择了工具
const hasSelectedTool = computed(() => {
  return isDeepThinkingEnabled.value || isWebSearchEnabled.value || hasImages.value
})

// 图片模式与知识库互斥
const canSelectKnowledgeBase = computed(() => {
  return !hasImages.value
})

// 复制文本到剪贴板
const copyToClipboard = async (content: any) => {
  try {
    const textToCopy = extractTextFromMessageContent(content);
    await navigator.clipboard.writeText(textToCopy);
    // 可以添加一个临时提示，表示复制成功
    console.log('文本已复制到剪贴板');
  } catch (err) {
    console.error('复制失败:', err);
  }
}

// 重新生成消息
const regenerateMessage = async (messageIndex: number) => {
  if (!currentConversation.value) return;
  
  // 直接调用store中的重新生成方法，只传递助手消息的索引
  await chatStore.regenerateResponse(messageIndex);
  
  // 滚动到底部
  scrollToBottom();
}

// 监听消息变化，自动滚动到底部
watch(() => currentConversation.value?.messages, () => {
  scrollToBottom()
}, { deep: true })

// 监听图片选择状态，实现与知识库的互斥逻辑
watch(hasImages, (newValue) => {
  if (newValue && currentConversation.value?.group_ids?.length) {
    // 当选择图片时，清除知识库选择
    handleKnowledgeBaseUpdate([])
  }
})

// 监听路由参数变化
watch(() => route.params.id, async (newId) => {
  if (newId) {
    // 如果有新的conversationId，加载该对话
    await chatStore.loadConversation(newId as string)
    scrollToBottom()
  } else {
    // 如果没有conversationId，准备新对话模式
    chatStore.prepareNewChat()
  }
})

// 滚动到底部
const scrollToBottom = () => {
  nextTick(() => {
    const container = messagesContainerRef.value
    if (container) {
      container.scrollTop = container.scrollHeight
    }
  })
}

// 处理点击外部关闭工具菜单
const handleClickOutside = (event: MouseEvent) => {
  if (toolMenuContainerRef.value && !toolMenuContainerRef.value.contains(event.target as Node)) {
    isToolMenuOpen.value = false
  }
}

// 切换深度思考功能
const toggleDeepThinking = () => {
  isDeepThinkingEnabled.value = !isDeepThinkingEnabled.value

  // 如果启用深度思考，自动关闭RAG（清除选中的知识库）
  if (isDeepThinkingEnabled.value && currentConversation.value) {
    // 清除知识库选择
    if (currentConversation.value.id) {
      chatStore.updateConversationGroups(currentConversation.value.id, [])
    } else {
      currentConversation.value.group_ids = []
    }
  }
}

// 切换网页搜索功能
const toggleWebSearch = () => {
  isWebSearchEnabled.value = !isWebSearchEnabled.value

  // 如果启用网页搜索，自动关闭RAG（清除选中的知识库）
  if (isWebSearchEnabled.value && currentConversation.value) {
    // 清除知识库选择
    if (currentConversation.value.id) {
      chatStore.updateConversationGroups(currentConversation.value.id, [])
    } else {
      currentConversation.value.group_ids = []
    }
  }
}

// 处理输入框高度自适应
const handleInput = () => {
  const textarea = textareaRef.value
  if (textarea) {
    textarea.style.height = 'auto' // 重置高度以获取正确的 scrollHeight
    textarea.style.height = `${textarea.scrollHeight}px`
  }
}

// 处理回车键发送消息
const handleEnterKey = (event: KeyboardEvent) => {
  // 如果按下Shift+Enter，则插入换行符
  if (event.shiftKey) {
    return
  }
  // 否则发送消息
  sendMessage()
}

// 发送消息
const sendMessage = async () => {
  const message = chatInputText.value.trim()
  if (!message || isGenerating.value) return

  // 立即清空输入框
  chatInputText.value = ''

  // 重置输入框高度
  if (textareaRef.value) {
    textareaRef.value.style.height = 'auto'
  }

  // 发送消息
  // 获取要使用的知识库组ID和Agent ID
  // 根据互斥逻辑，如果启用了联网、深度思考或图片模式，则不使用知识库
  const groupIdsToUse = (isWebSearchEnabled.value || isDeepThinkingEnabled.value || hasImages.value) ? [] : getKnowledgeBaseGroupIds()
  const agentIdToUse = currentConversation.value?.agent_id || undefined
  const imagesToUse = hasImages.value ? getImageBase64List() : []
  await chatStore.sendMessage(message, groupIdsToUse, agentIdToUse, isDeepThinkingEnabled.value, isWebSearchEnabled.value, imagesToUse)

  // 发送后清空图片
  if (hasImages.value) {
    clearImages()
  }

  // 滚动到底部
  scrollToBottom()
}

// 获取要使用的知识库组ID（实现继承逻辑）
const getKnowledgeBaseGroupIds = (): string[] => {
  // 如果当前对话已经有关联的知识库组，直接使用
  if (currentConversation.value?.group_ids && currentConversation.value.group_ids.length > 0) {
    return currentConversation.value.group_ids
  }

  // 如果当前对话没有关联知识库，但有消息历史，尝试从最后一个用户消息继承
  if (currentConversation.value?.messages && currentConversation.value.messages.length > 0) {
    // 从后往前查找最后一个用户消息，看是否有关联的知识库
    for (let i = currentConversation.value.messages.length - 1; i >= 0; i--) {
      const message = currentConversation.value.messages[i]
      if (message.role === 'user' && message.group_ids && message.group_ids.length > 0) {
        return message.group_ids
      }
    }
  }

  // 如果都没有，返回空数组
  return []
}

// 切换知识库选择弹窗
const toggleKnowledgeBaseModal = () => {
  isKnowledgeBaseModalOpen.value = !isKnowledgeBaseModalOpen.value
}

// 切换Agent选择弹窗
const toggleAgentModal = () => {
  isAgentModalOpen.value = !isAgentModalOpen.value
}

// 处理知识库更新
const handleKnowledgeBaseUpdate = (selectedGroupIds: string[]) => {
  if (currentConversation.value) {
    // 如果选择了知识库，自动关闭工具选项（互斥逻辑）
    if (selectedGroupIds.length > 0) {
      isDeepThinkingEnabled.value = false
      isWebSearchEnabled.value = false
    }

    // 如果是已存在的对话，更新对话关联的知识库组
    if (currentConversation.value.id) {
      chatStore.updateConversationGroups(currentConversation.value.id, selectedGroupIds)
    } else {
      // 如果是新对话模式，直接更新本地状态
      currentConversation.value.group_ids = selectedGroupIds
    }
  }
}

// 处理Agent选择
const handleAgentSelect = (agentId: string | null) => {
  if (currentConversation.value) {
    // 如果是新对话模式，直接更新本地状态
    if (!currentConversation.value.id) {
      currentConversation.value.agent_id = agentId
    }
    // 注意：已存在的对话不允许更改Agent，因为这会影响对话的一致性
  }
}

// 组件挂载时
onMounted(async () => {
  // 设置随机欢迎消息
  const randomIndex = Math.floor(Math.random() * welcomeMessages.length)
  currentWelcomeMessage.value = welcomeMessages[randomIndex]
  
  // 添加点击外部关闭菜单的事件监听
  document.addEventListener('click', handleClickOutside)
  
  // 如果路由中有conversationId，加载该对话
  const conversationId = route.params.id as string
  if (conversationId) {
    await chatStore.loadConversation(conversationId)
    scrollToBottom()
  } else {
    // 如果没有conversationId，准备新对话模式
    chatStore.prepareNewChat()
  }
})

onUnmounted(() => {
  document.removeEventListener('click', handleClickOutside)
})
</script>

<style scoped>
.chat-view {
  flex-grow: 1;
  display: flex;
  flex-direction: column;
  height: 100vh;
  background-color: var(--bg-secondary);
  position: relative;
  overflow-x: hidden; /* 防止水平滚动 */
}

.welcome-container {
  flex-grow: 1;
  display: flex;
  justify-content: center;
  align-items: center;
}

.welcome-container h1 {
  font-size: 2.5em;
  font-weight: 600;
  color: var(--text-secondary);
}

.messages-container {
  flex-grow: 1;
  overflow-y: auto;
  padding: 24px;
  display: flex;
  flex-direction: column;
  width: 100%;
}

.loading-message {
  text-align: center;
  padding: 20px;
  color: var(--text-secondary);
  font-size: 16px;
}

.message-wrapper {
  margin-bottom: 24px;
  display: flex;
  flex-direction: column;
  max-width: 800px;
  margin-left: auto;
  margin-right: auto;
  width: 100%;
}

/* 用户消息容器 */
.user-message-wrapper {
  align-self: flex-end;
  max-width: 80%;
  position: relative;
}

/* 用户消息样式 */
.user-message {
  align-self: flex-end;
  background-color: var(--bg-input);
  color: var(--text-primary);
  padding: 14px;
  border-radius: var(--border-radius-large);
  word-break: break-word;
  line-height: 1.5;
  font-size: 16px;
}

/* 助手消息容器 */
.assistant-message-wrapper {
  align-self: flex-start;
  max-width: 100%;
  position: relative;
}

/* 助手消息样式 */
.assistant-message {
  color: var(--text-primary);
  line-height: 1.5;
  font-size: 16px;
  margin-bottom: 8px;
}



/* 消息操作按钮 */
.message-actions {
  display: flex;
  gap: 4px;
  margin-top: 10px;
  opacity: 0;
  transition: opacity 0.2s ease;
}

/* 用户消息操作按钮仍然需要hover才显示 */
.user-message-wrapper:hover .message-actions {
  opacity: 1;
}

/* 助手消息操作按钮常驻显示 */
.assistant-message-wrapper .message-actions {
  opacity: 1;
  margin-left: -10px; /* 向左移动 */
}

.message-action-button {
  background: transparent;
  border: none;
  color: var(--text-secondary);
  cursor: pointer;
  padding: 6px;
  border-radius: 8px;
  width: 32px;
  height: 32px;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: background-color 0.2s, color 0.2s;
  position: relative; /* 为tooltip定位 */
}

.message-action-button:hover {
  background-color: var(--bg-tertiary);
  color: var(--text-primary);
}

.message-action-button .tooltip {
  position: absolute;
  bottom: -30px;
  left: 50%;
  transform: translateX(-50%);
  background-color: #000;
  color: #fff;
  padding: 4px 8px;
  border-radius: 8px;
  font-size: 12px;
  white-space: nowrap;
  opacity: 0;
  visibility: hidden;
  transition: opacity 0.2s, visibility 0.2s;
  z-index: 10;
}

.message-action-button:hover .tooltip {
  opacity: 1;
  visibility: visible;
}

.message-action-button :deep(svg) {
  font-size: 18px;
  font-weight: 1000; /* 加粗图标 */
}

/* 用户消息操作按钮特殊样式 */
.user-message-actions {
  justify-content: flex-end;
}

.input-container {
  padding: 0 24px 24px;
  width: 100%;
  max-width: 800px;
  margin: 0 auto;
}

.image-preview-container {
  margin-bottom: 12px;
}

.error-toast {
  background: #fee;
  border: 1px solid #fcc;
  border-radius: 6px;
  padding: 8px 12px;
  margin-bottom: 12px;
  font-size: 14px;
}

.error-message {
  color: #c33;
  margin-bottom: 4px;
}

.error-message:last-child {
  margin-bottom: 0;
}

.input-box-wrapper {
  display: flex;
  flex-direction: column;
  background-color: var(--bg-input);
  border-radius: var(--border-radius-large);
  /* border: 1px solid var(--border-color); */
  padding: 16px;
}

.chat-input {
  width: 100%;
  background: transparent;
  border: none;
  outline: none;
  color: var(--text-primary);
  font-size: 16px;
  resize: none;
  font-family: inherit;
  line-height: 1.5;
  margin-bottom: 12px;
  max-height: calc(16px * 1.5 * 5);
  overflow-y: auto;
}

.chat-input::placeholder {
  color: var(--text-placeholder);
}

.input-actions {
  display: flex;
  justify-content: space-between;
  align-items: center;
  width: 100%;
}

.actions-left,
.actions-right {
  display: flex;
  align-items: center;
  gap: 8px;
}

.input-icon-button {
  background: transparent;
  border: none;
  color: var(--text-secondary);
  cursor: pointer;
  padding: 8px;
  border-radius: 50%;
  width: 36px;
  height: 36px;
  display: flex;
  align-items: center;
  justify-content: center;
  transition:
    background-color 0.2s,
    color 0.2s;
}
.input-icon-button:hover {
  background-color: #4f5058;
}

.input-icon-button.image-selected {
  background-color: var(--accent-color);
  color: white;
}

.input-icon-button.drag-over {
  background-color: var(--accent-color);
  color: white;
  transform: scale(1.05);
}

.input-icon-button.disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.input-icon-button.disabled:hover {
  background-color: transparent;
}

.input-icon-button.with-text {
  border-radius: 8px;
  padding: 6px 12px;
  gap: 6px;
  width: auto;
  height: auto;
}
.input-icon-button.with-text:hover {
  color: var(--text-primary);
}

.input-icon-button :deep(svg) {
  font-size: 20px;
}

.send-button {
  background-color: var(--button-primary-bg);
  cursor: not-allowed;
  color: var(--text-secondary); /* 默认状态下图标为灰色 */
}

/* 当输入框有内容时应用的样式 */
.send-button.has-text {
  background-color: var(--send-button-active-bg);
  color: var(--send-button-active-icon);
}
.send-button.has-text:hover {
  filter: brightness(0.9);
  cursor: pointer;
}

.tool-button-wrapper,
.knowledge-button-wrapper,
.agent-button-wrapper {
  position: relative;
}

.tool-menu {
  position: absolute;
  bottom: calc(100% + 8px);
  left: 50%;
  transform: translateX(-50%);
  background-color: #2c2d30;
  border-radius: var(--border-radius-medium);
  padding: 8px;
  display: flex;
  flex-direction: column;
  gap: 4px;
  z-index: 10;
  width: 180px; /* 固定宽度确保布局一致性 */
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.3);
}

.tool-menu-item {
  display: flex;
  align-items: center;
  justify-content: space-between; /* 确保check图标在右侧 */
  gap: 8px;
  background: transparent;
  border: none;
  color: var(--text-primary);
  padding: 8px 12px;
  border-radius: var(--border-radius-medium);
  cursor: pointer;
  width: 100%;
  text-align: left;
  font-size: 14px;
  transition: all 0.2s ease;
}

.tool-menu-item:hover {
  background-color: #4f5058;
}

/* 选中状态样式 */
.tool-menu-item.selected {
  background-color: var(--interactive-label-background-default);
  color: var(--interactive-label-accent-default);
}

.tool-menu-item.selected:hover {
  background-color: var(--interactive-label-background-hover); /* 使用蓝色的半透明背景 */
}

/* 左侧内容容器 */
.tool-menu-item .left-content {
  display: flex;
  align-items: center;
  gap: 8px;
}

/* check图标样式 */
.check-icon {
  color: var(--interactive-label-accent-default);
  flex-shrink: 0;
}

.tool-menu-item :deep(svg) {
  font-size: 20px;
}

/* 工具按钮选中状态样式 */
.input-icon-button.tool-selected {
  background-color: var(--interactive-label-background-default); /* 蓝色背景 */
  color: var(--interactive-label-accent-default);
}

.input-icon-button.tool-selected:hover {
  background-color: var(--interactive-label-background-hover); /* 悬停时稍微深一点的蓝色 */
}

/* 知识库按钮选中状态样式 */
.input-icon-button.knowledge-selected {
  background-color: var(--interactive-label-background-default); /* 蓝色背景 */
  color: var(--interactive-label-accent-default);
}

.input-icon-button.knowledge-selected:hover {
  background-color: var(--interactive-label-background-hover); /* 悬停时稍微深一点的蓝色 */
}

/* Agent按钮选中状态样式 */
.input-icon-button.agent-selected {
  background-color: var(--interactive-label-background-default);
  color: var(--interactive-label-accent-default);
}

.input-icon-button.agent-selected:hover {
  background-color: var(--interactive-label-background-hover);
}
</style>
