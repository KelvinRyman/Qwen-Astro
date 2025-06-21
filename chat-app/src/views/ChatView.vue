<template>
  <div class="chat-view">
    <div class="welcome-container">
      <h1>{{ currentWelcomeMessage }}</h1>
    </div>
    <div class="input-container">
      <div class="input-box-wrapper">
        <textarea
          ref="textareaRef"
          v-model="chatInputText"
          class="chat-input"
          placeholder="询问任何问题"
          rows="1"
          @input="handleInput"
        ></textarea>
        <div class="input-actions">
          <div class="actions-left">
            <button class="input-icon-button">
              <AppIcon name="plus" />
            </button>
            <button class="input-icon-button">
              <AppIcon name="tool" />
            </button>
          </div>
          <div class="actions-right">
            <button class="input-icon-button">
              <AppIcon name="microphone" />
            </button>
            <button
              class="input-icon-button send-button"
              :class="{ 'has-text': chatInputText.trim() !== '' }"
            >
              <AppIcon name="send" />
            </button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import AppIcon from '../components/AppIcon.vue'

const welcomeMessages = [
  '今天有什么议程？',
  '有什么可以帮你的吗？',
  '你好，今天想聊点什么？',
  '请输入您的问题...',
]

const currentWelcomeMessage = ref('')
const textareaRef = ref<HTMLTextAreaElement | null>(null)
const chatInputText = ref('') // 用于绑定 textarea 内容

const handleInput = () => {
  const textarea = textareaRef.value
  if (textarea) {
    textarea.style.height = 'auto' // 重置高度以获取正确的 scrollHeight
    textarea.style.height = `${textarea.scrollHeight}px`
  }
}

onMounted(() => {
  const randomIndex = Math.floor(Math.random() * welcomeMessages.length)
  currentWelcomeMessage.value = welcomeMessages[randomIndex]
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
  border: 1px solid var(--border-color);
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
  color: var(--text-secondary); /* 默认状态下图标为灰色 */
}
.send-button:hover {
  background-color: #5b5c68;
}

/* 当输入框有内容时应用的样式 */
.send-button.has-text {
  background-color: var(--send-button-active-bg);
  color: var(--send-button-active-icon);
}
.send-button.has-text:hover {
  filter: brightness(0.9);
}
</style>
