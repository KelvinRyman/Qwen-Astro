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
import { ref, onMounted, onUnmounted } from 'vue'
import Icon from '../components/AppIcon.vue'

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

const isToolMenuOpen = ref(false)
const toolMenuContainerRef = ref<HTMLElement | null>(null)

const handleClickOutside = (event: MouseEvent) => {
  if (toolMenuContainerRef.value && !toolMenuContainerRef.value.contains(event.target as Node)) {
    isToolMenuOpen.value = false
  }
}

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
  document.addEventListener('click', handleClickOutside)
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
