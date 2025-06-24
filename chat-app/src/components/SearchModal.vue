<template>
  <div class="search-overlay" @click.self="$emit('close')">
    <div class="search-modal-content">
      <div class="search-header">
        <input 
          type="text" 
          class="search-input" 
          placeholder="搜索聊天..." 
          v-model="searchQuery" 
          @input="handleSearch"
          ref="searchInput"
        />
        <button class="close-button" @click="$emit('close'), clearSearch">
          <Icon name="close" />
        </button>
      </div>
      <div class="search-body">
        <!-- 加载状态 -->
        <div v-if="isLoading" class="loading-state">
          <span>正在搜索...</span>
        </div>
        <!-- 如果聊天记录为空 -->
        <div v-else-if="chatHistory.length === 0" class="empty-state">
          <a href="#" class="new-chat-link" @click.prevent="createNewChat">
            <Icon name="new_chat" />
            <span>新聊天</span>
          </a>
        </div>

        <!-- 如果有聊天记录，则渲染列表 -->
        <div v-else class="history-list">
          <!-- "新聊天"按钮始终在顶部 -->
          <a href="#" class="new-chat-link" @click.prevent="createNewChat">
            <Icon name="new_chat" />
            <span>新聊天</span>
          </a>

          <!-- 循环渲染分组 -->
          <div v-for="group in chatHistory" :key="group.title" class="history-group">
            <div class="group-title">{{ group.title }}</div>
            <!-- 循环渲染分组内的项目 -->
            <a 
              v-for="item in group.items" 
              :key="item.id" 
              href="#" 
              class="history-item"
              @click.prevent="selectChat(item.id)"
            >
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
import Icon from './AppIcon.vue';
import { useChatStore } from '@/stores/chat';
import { ref, computed, onMounted, nextTick } from 'vue';
import { useRouter } from 'vue-router';
import { chatApi, type ConversationSummary } from '@/api/chatApi';

const emit = defineEmits(['close']);

const router = useRouter();
const chatStore = useChatStore();
const searchQuery = ref('');
const searchInput = ref<HTMLInputElement | null>(null);
const isLoading = ref(false);
const searchResults = ref<ConversationSummary[]>([]);
const searchResultGroups = ref<{ title: string; items: ConversationSummary[] }[]>([]);

// 计算属性 - 根据当前状态决定显示搜索结果还是全部会话
const chatHistory = computed(() => {
  if (searchQuery.value.trim() && searchResultGroups.value.length > 0) {
    return searchResultGroups.value;
  }
  return chatStore.chatHistory;
});

// 在组件挂载时加载对话列表并聚焦搜索框
onMounted(async () => {
  if (!chatStore.chatHistory.length) {
    await chatStore.loadConversations();
  }
  nextTick(() => {
    if (searchInput.value) {
      searchInput.value.focus();
    }
  });
});

// 防抖处理搜索
let searchTimeout: number | null = null;
const handleSearch = () => {
  if (searchTimeout) {
    clearTimeout(searchTimeout);
  }
  
  searchTimeout = setTimeout(async () => {
    if (searchQuery.value.trim()) {
      isLoading.value = true;
      try {
        // 直接调用API而不是通过chatStore
        searchResults.value = await chatApi.searchConversations(searchQuery.value);
        searchResultGroups.value = chatApi.groupConversationsByDate(searchResults.value);
      } catch (err) {
        console.error('搜索对话失败:', err);
      } finally {
        isLoading.value = false;
      }
    } else {
      // 清空搜索结果，显示全部会话
      searchResults.value = [];
      searchResultGroups.value = [];
    }
  }, 300) as unknown as number;
};

// 选择聊天
const selectChat = (chatId: string) => {
  router.push(`/chat/${chatId}`);
  resetSearch();
  emit('close');
};

// 创建新对话
const createNewChat = async () => {
  chatStore.prepareNewChat();
  router.push('/chat');
  resetSearch();
  emit('close');
};

// 重置搜索状态
const resetSearch = () => {
  searchQuery.value = '';
  searchResults.value = [];
  searchResultGroups.value = [];
};

// 添加清除搜索按钮
const clearSearch = () => {
  resetSearch();
};
</script>

<style scoped>
.search-overlay {
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background-color: transparent;
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

.loading-state {
  display: flex;
  justify-content: center;
  align-items: center;
  height: 100px;
  color: var(--text-secondary);
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