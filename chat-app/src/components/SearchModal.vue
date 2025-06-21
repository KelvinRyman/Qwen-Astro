<template>
  <div class="search-overlay" @click.self="$emit('close')">
    <div class="search-modal-content">
      <div class="search-header">
        <input type="text" class="search-input" placeholder="搜索聊天..." />
        <button class="close-button" @click="$emit('close')">
          <Icon name="close" />
        </button>
      </div>
      <div class="search-body">
        <!-- 如果聊天记录为空 -->
        <div v-if="chatHistory.length === 0" class="empty-state">
          <a href="#" class="new-chat-link">
            <Icon name="new_chat" />
            <span>新聊天</span>
          </a>
        </div>

        <!-- 如果有聊天记录，则渲染列表 -->
        <div v-else class="history-list">
          <!-- “新聊天”按钮始终在顶部 -->
          <a href="#" class="new-chat-link">
            <Icon name="new_chat" />
            <span>新聊天</span>
          </a>

          <!-- 循环渲染分组 -->
          <div v-for="group in chatHistory" :key="group.title" class="history-group">
            <div class="group-title">{{ group.title }}</div>
            <!-- 循环渲染分组内的项目 -->
            <a v-for="item in group.items" :key="item.id" href="#" class="history-item">
              <Icon name="chat" />
              <span>{{ item.title }}</span>
            </a>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue';
import type { Ref } from 'vue';
import Icon from './AppIcon.vue';

defineEmits(['close']);

// 定义数据结构类型
interface ChatItem {
  id: number;
  title: string;
}

interface ChatGroup {
  title: string;
  items: ChatItem[];
}

// 填充示例聊天记录
const chatHistory: Ref<ChatGroup[]> = ref([
  {
    title: '今天',
    items: [
      { id: 1, title: 'TypeScript vs JavaScript in Vue' },
    ]
  },
  {
    title: '昨天',
    items: [
      { id: 2, title: 'ChatGPT 对话记录管理' },
    ]
  },
  {
    title: '前 7 天',
    items: [
      { id: 3, title: 'LLM Fine-Tuning in Space' },
      { id: 4, title: 'DeepSpeed MP Error' },
      { id: 5, title: '双卡 3090 微调 Qwen3' }
    ]
  }
]);

</script>

<style scoped>
.search-overlay {
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background-color: var(--search-overlay-bg, rgba(0, 0, 0, 0.5)); /* 添加了备用值 */
  display: flex;
  justify-content: center;
  align-items: flex-start; /* 从顶部开始对齐 */
  padding-top: 20vh; /* 距离顶部20%视窗高度 */
  z-index: 1000;
}

.search-modal-content {
  width: 100%;
  max-width: 700px;
  max-height: 70vh; /* 限制最大高度 */
  background-color: var(--bg-tertiary);
  border-radius: var(--border-radius-large);
  box-shadow: 0 10px 40px rgba(0, 0, 0, 0.5);
  overflow: hidden;
  display: flex;
  flex-direction: column;
}

.search-header {
  display: flex;
  align-items: center;
  padding: 12px;
  border-bottom: 1px solid var(--border-color);
  flex-shrink: 0;
}

.search-input {
  flex-grow: 1;
  background: transparent;
  border: none;
  outline: none;
  color: var(--text-primary);
  font-size: 16px;
  padding: 8px;
}
.search-input::placeholder {
  color: var(--text-placeholder);
}

.close-button {
  background: transparent;
  border: none;
  color: var(--text-secondary);
  cursor: pointer;
  padding: 8px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: background-color 0.2s;
}
.close-button:hover {
  background-color: #4f5058;
}
.close-button :deep(svg) {
  font-size: 16px;
}

.search-body {
  padding: 16px;
  overflow-y: auto;
}

.empty-state {
  display: flex;
  flex-direction: column;
}

.new-chat-link {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px;
  margin-bottom: 16px;
  border-radius: 8px;
  text-decoration: none;
  color: var(--text-primary);
  background-color: var(--button-primary-bg);
  transition: background-color 0.2s;
  flex-shrink: 0;
}
.new-chat-link:hover {
  background-color: #5b5c68;
}
.new-chat-link :deep(svg) {
  font-size: 20px;
}

.history-list {
  display: flex;
  flex-direction: column;
}

.history-group {
  margin-bottom: 16px;
}

.history-group:last-child {
  margin-bottom: 0;
}

.group-title {
  font-size: 12px;
  color: var(--text-secondary);
  padding: 0 12px 8px;
  text-transform: uppercase;
  user-select: none;
}

.history-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 10px 12px;
  border-radius: 8px;
  text-decoration: none;
  color: var(--text-primary);
  transition: background-color 0.2s;
}
.history-item:hover {
  background-color: var(--button-primary-bg);
}
.history-item :deep(svg) {
  font-size: 20px;
}
</style>