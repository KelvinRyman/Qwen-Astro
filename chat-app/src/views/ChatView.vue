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
          <div v-if="message.role === 'user'" class="user-message">
            {{ message.content }}
          </div>
          
          <!-- 助手消息 -->
          <div v-else class="assistant-message-wrapper">
            <div class="assistant-message">
              {{ message.content }}
              <span v-if="message.isGenerating" class="generating-cursor"></span>
            </div>
            <!-- 只在消息生成完毕后显示操作按钮 -->
            <div v-if="!message.isGenerating" class="message-actions">
              <button class="message-action-button">
                <Icon name="copy" />
              </button>
              <button class="message-action-button">
                <Icon name="refresh" />
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
    
    <!-- 输入区域：始终显示 -->
    <div class="input-container">
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
            <button class="input-icon-button">
              <Icon name="plus" />
            </button>
            <div ref="toolMenuContainerRef" class="tool-button-wrapper">
              <button class="input-icon-button" @click="isToolMenuOpen = !isToolMenuOpen">
                <Icon name="tool" />
              </button>
              <div v-if="isToolMenuOpen" class="tool-menu">
                <button class="tool-menu-item">
                  <Icon name="think" />
                  <span>深度思考</span>
                </button>
                <button class="tool-menu-item">
                  <Icon name="web" />
                  <span>搜索网页</span>
                </button>
              </div>
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
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted, computed, nextTick, watch } from 'vue'
import { useRoute } from 'vue-router'
import Icon from '../components/AppIcon.vue'
import { useChatStore } from '@/stores/chat'

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

// 监听消息变化，自动滚动到底部
watch(() => currentConversation.value?.messages, () => {
  scrollToBottom()
}, { deep: true })

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
  await chatStore.sendMessage(message)
  
  // 滚动到底部
  scrollToBottom()
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

/* 用户消息样式 */
.user-message {
  align-self: flex-end;
  background-color: var(--bg-input);
  color: var(--text-primary);
  padding: 14px;
  border-radius: var(--border-radius-large);
  max-width: 80%;
  word-break: break-word;
  line-height: 1.5;
  font-size: 16px;
}

/* 助手消息容器 */
.assistant-message-wrapper {
  align-self: flex-start;
  max-width: 80%;
  position: relative;
}

/* 助手消息样式 */
.assistant-message {
  color: var(--text-primary);
  line-height: 1.5;
  font-size: 16px;
  margin-bottom: 8px;
}

/* 生成中的光标效果 */
.generating-cursor {
  display: inline-block;
  width: 8px;
  height: 16px;
  background-color: var(--text-primary);
  margin-left: 2px;
  animation: blink 1s infinite;
  vertical-align: middle;
}

@keyframes blink {
  0%, 100% { opacity: 1; }
  50% { opacity: 0; }
}

/* 消息操作按钮 */
.message-actions {
  display: flex;
  gap: 8px;
  margin-top: 8px;
  opacity: 0;
  transition: opacity 0.2s ease;
}

.assistant-message-wrapper:hover .message-actions {
  opacity: 1;
}

.message-action-button {
  background: transparent;
  border: none;
  color: var(--text-secondary);
  cursor: pointer;
  padding: 6px;
  border-radius: 50%;
  width: 32px;
  height: 32px;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: background-color 0.2s, color 0.2s;
}

.message-action-button:hover {
  background-color: var(--bg-tertiary);
  color: var(--text-primary);
}

.message-action-button :deep(svg) {
  font-size: 18px;
}

.input-container {
  padding: 0 24px 24px;
  width: 100%;
  max-width: 800px;
  margin: 0 auto;
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

.tool-button-wrapper {
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
  width: max-content;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.3);
}

.tool-menu-item {
  display: flex;
  align-items: center;
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
}

.tool-menu-item:hover {
  background-color: #4f5058;
}

.tool-menu-item :deep(svg) {
  font-size: 20px;
}
</style>
