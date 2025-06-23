<template>
  <div class="sidebar" :class="{ 'is-collapsed': isCollapsed }">
    <div class="sidebar-header">
      <!-- 左侧按钮: 始终存在，但图标和功能会根据状态改变 -->
      <button class="header-button logo-button" @click="emit('toggle')">
        <Icon :name="isCollapsed ? 'sidebar' : 'logo'" />
      </button>

      <!-- 右侧按钮: 仅在展开时显示，并带有动画 -->
      <Transition name="fade-slide">
        <button v-if="!isCollapsed" class="header-button toggle-button" @click="emit('toggle')">
          <Icon name="sidebar" />
        </button>
      </Transition>
    </div>

    <div class="sidebar-content">
      <div class="sidebar-section">
        <a href="#" class="sidebar-link" @click.prevent="createNewChat">
          <Icon name="new_chat" />
          <span class="link-text">新聊天</span>
        </a>
        <a href="#" class="sidebar-link" @click.prevent="$emit('open-search')">
          <Icon name="search" />
          <span class="link-text">搜索</span>
        </a>
        <a href="#" class="sidebar-link" @click.prevent="router.push('/knowledge')">
          <Icon name="knowledge" />
          <span class="link-text">知识库</span>
        </a>
        <a href="#" class="sidebar-link">
          <Icon name="agent" />
          <span class="link-text">Agent</span>
        </a>
      </div>
      <div class="sidebar-section">
        <div class="section-title">
          <span class="link-text">聊天</span>
        </div>
        <!-- 加载状态 -->
        <div v-if="isLoading" class="loading-indicator">
          <span class="link-text">加载中...</span>
        </div>
        <!-- 空状态 -->
        <div v-else-if="allChats.length === 0" class="empty-state">
          <span class="link-text">暂无聊天记录</span>
        </div>
        <!-- 聊天历史记录 -->
        <div
          v-else
          v-for="item in allChats"
          :key="item.id"
          class="chat-item-wrapper"
          :class="{ 'menu-open': openMenuId === item.id }"
          @click="selectChat(item.id)"
        >
          <a href="#" class="sidebar-link chat-item" @click.prevent>
            <span class="link-text chat-title">{{ item.title }}</span>
          </a>
          <div v-if="!isCollapsed" class="chat-item-actions" @click.stop>
            <ItemDropdownMenu
              :is-open="openMenuId === item.id"
              @toggle="toggleMenu(item.id)"
              @close="openMenuId = null"
              @rename="handleRenameChat(item.id)"
              @delete="handleDeleteChat(item.id)"
            />
          </div>
        </div>
      </div>
    </div>

    <div class="sidebar-footer">
      <button class="sidebar-link settings" @click="emit('open-settings')">
        <Icon name="settings" />
        <span class="link-text">设置</span>
      </button>
    </div>

    <!-- 重命名聊天对话框 -->
    <div v-if="isRenameModalVisible" class="modal-overlay" @click.self="isRenameModalVisible = false">
      <div class="rename-modal">
        <h3>重命名对话</h3>
        <input 
          v-model="newChatTitle" 
          type="text" 
          class="rename-input" 
          placeholder="输入新名称"
          @keyup.enter="confirmRenameChat"
        />
        <div class="modal-actions">
          <button class="cancel-btn" @click="isRenameModalVisible = false">取消</button>
          <button class="confirm-btn" @click="confirmRenameChat">确认</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import Icon from './AppIcon.vue'
import ItemDropdownMenu from './ItemDropdownMenu.vue'
import { useRouter } from 'vue-router';
import { useChatStore, type ChatGroup } from '@/stores/chat';
import { computed, ref, onMounted } from 'vue';

defineProps<{
  isCollapsed: boolean;
}>()

const emit = defineEmits(['toggle', 'open-settings', 'open-search'])

const router = useRouter();
const chatStore = useChatStore();
const isRenameModalVisible = ref(false);
const newChatTitle = ref('');
const currentChatId = ref<string | null>(null);
const openMenuId = ref<string | null>(null);
const isLoading = computed(() => chatStore.isLoading);

// 获取所有聊天
const allChats = computed(() => {
  return chatStore.chatHistory.flatMap((group: ChatGroup) => group.items);
});

// 在组件挂载时加载对话列表
onMounted(async () => {
  await chatStore.loadConversations();
});

// 选择聊天
const selectChat = (chatId: string) => {
  if (openMenuId.value === chatId) {
    return;
  }
  router.push(`/chat/${chatId}`);
};

const toggleMenu = (chatId: string) => {
  openMenuId.value = openMenuId.value === chatId ? null : chatId;
};

// 重命名聊天
const handleRenameChat = (chatId: string) => {
  openMenuId.value = null; // Close dropdown menu
  const chat = allChats.value.find(item => item.id === chatId);
  if (chat) {
    newChatTitle.value = chat.title;
    currentChatId.value = chatId;
    isRenameModalVisible.value = true;
  }
};

// 确认重命名
const confirmRenameChat = async () => {
  if (currentChatId.value !== null && newChatTitle.value.trim()) {
    await chatStore.renameChat(currentChatId.value, newChatTitle.value);
    isRenameModalVisible.value = false;
  }
};

// 删除聊天
const handleDeleteChat = async (chatId: string) => {
  openMenuId.value = null; // Close dropdown menu
  if (confirm('确定要删除这个对话吗？此操作不可恢复。')) {
    await chatStore.deleteChat(chatId);
  }
};

// 创建新对话
const createNewChat = async () => {
  chatStore.prepareNewChat();
  router.push('/chat');
};
</script>

<style scoped>
/* 侧边栏主体过渡 */
.sidebar {
  width: var(--sidebar-width);
  background-color: var(--bg-primary);
  display: flex;
  flex-direction: column;
  height: 100vh;
  padding: 8px;
  color: var(--text-primary);
  transition: width 0.3s ease;
  flex-shrink: 0;
}
.sidebar.is-collapsed {
  width: var(--sidebar-width-collapsed);
}
.sidebar-section {
  margin-bottom: 24px;
}

/* 头部布局 */
.sidebar-header {
  display: flex;
  justify-content: space-between; /* 始终两端对齐 */
  align-items: center;
  padding: 8px 4px;
  height: 52px;
  box-sizing: border-box;
}

/* 头部按钮统一样式 (正方形) */
.header-button {
  display: flex;
  align-items: center;
  justify-content: center;
  background-color: transparent;
  border: none;
  color: var(--text-primary);
  border-radius: 8px;
  cursor: pointer;
  width: 40px;
  height: 40px;
  padding: 0;
  flex-shrink: 0;
}
.header-button:hover {
  background-color: var(--bg-tertiary);
}
.header-button :deep(svg) {
  font-size: 20px;
}

/* 链接和页脚按钮的基础样式 */
.sidebar-link,
.settings {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 10px 12px;
  border-radius: 8px;
  text-decoration: none;
  overflow: hidden;
  background-color: transparent;
  border: none;
  color: var(--text-primary);
  cursor: pointer;
  font-size: 1em;
  width: 100%;
  text-align: left;
  transition: background-color 0.2s; /* Ensure transition exists */
}

.sidebar-link:hover,
.settings:hover {
  background-color: var(--bg-tertiary);
}
.sidebar-link :deep(svg),
.settings :deep(svg) {
  font-size: 20px;
  flex-shrink: 0;
}
.sidebar-link.active {
  background-color: var(--bg-active);
}

/* 聊天项包装器，用于布局聊天项和操作按钮 */
.chat-item-wrapper {
  position: relative;
  display: flex;
  align-items: center;
  border-radius: 8px;
  margin: 2px 0;
  cursor: pointer;
  transition: background-color 0.2s ease;
}

/* Key Fix: Apply background on hover OR when the menu is open */
.chat-item-wrapper:hover,
.chat-item-wrapper.menu-open {
  background-color: var(--bg-tertiary);
}

/* The actual link inside should not have its own background effect */
.chat-item-wrapper .chat-item,
.chat-item-wrapper:hover .chat-item {
  background-color: transparent !important;
  cursor: inherit;
  padding: 10px 12px;
  height: 40px;
  box-sizing: border-box;
}

.chat-item {
  flex-grow: 1;
  display: flex;
  align-items: center;
}

.chat-title {
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  transition: max-width 0.2s ease-in-out;
}

.chat-item-wrapper:hover .chat-title,
.chat-item-wrapper.menu-open .chat-title {
  max-width: 180px;
}

.chat-item-actions {
  position: absolute;
  right: 8px;
  opacity: 0;
  transition: opacity 0.2s ease;
  pointer-events: none;
  display: flex;
  align-items: center;
  height: 100%;
}

.chat-item-wrapper:hover .chat-item-actions,
.chat-item-wrapper.menu-open .chat-item-actions {
  opacity: 1;
  pointer-events: auto;
}

/* 当收起时，链接和页脚按钮的内容靠左对齐 */
.sidebar.is-collapsed .sidebar-link,
.sidebar.is-collapsed .settings {
  justify-content: flex-start;
  padding: 10px; /* 调整内边距使其与头部按钮在视觉上居中对齐 */
}

/* 文字标签的动画 */
.link-text {
  white-space: nowrap;
  opacity: 1;
  transition: opacity 0.2s ease, max-width 0.3s ease;
}
.sidebar.is-collapsed .link-text {
  opacity: 0;
  max-width: 0;
}

/* 章节标题动画 */
.section-title {
  padding: 0 12px 8px;
  font-size: 14px;
  color: var(--text-secondary);
  font-weight: 500;
  user-select: none;
  overflow: hidden;
  height: 29px;
  transition: opacity 0.2s, height 0.3s, padding 0.3s;
}
.sidebar.is-collapsed .section-title {
  height: 0;
  padding-top: 0;
  padding-bottom: 0;
  opacity: 0;
}

/* 右侧切换按钮的进入/离开动画 */
.fade-slide-enter-active,
.fade-slide-leave-active {
  transition: all 0.3s ease;
}
.fade-slide-enter-from,
.fade-slide-leave-to {
  opacity: 0;
  transform: translateX(10px);
}
.fade-slide-enter-to,
.fade-slide-leave-from {
  opacity: 1;
  transform: translateX(0);
}

.sidebar-content {
  flex-grow: 1;
  overflow-y: auto;
  overflow-x: hidden;
  padding: 8px 4px;
}
.sidebar-footer {
  padding: 8px 4px;
}

/* 加载指示器和空状态 */
.loading-indicator, .empty-state {
  padding: 10px 12px;
  color: var(--text-secondary);
  font-size: 14px;
  text-align: center;
  margin: 8px 0;
}

.empty-state {
  font-style: italic;
}

/* 模态框样式 */
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background-color: var(--bg-overlay);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}

.rename-modal {
  background-color: var(--modal-bg);
  border-radius: var(--border-radius-medium);
  padding: 24px;
  width: 400px;
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.2);
}

.rename-modal h3 {
  margin-top: 0;
  margin-bottom: 16px;
  font-size: 18px;
  color: var(--text-primary);
}

.rename-input {
  width: 100%;
  padding: 10px 12px;
  border-radius: 6px;
  border: 1px solid var(--border-color);
  background-color: var(--bg-input);
  color: var(--text-primary);
  font-size: 14px;
  margin-bottom: 16px;
}

.modal-actions {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
}

.cancel-btn {
  padding: 8px 16px;
  border-radius: 6px;
  border: 1px solid var(--border-color);
  background-color: transparent;
  color: var(--text-secondary);
  cursor: pointer;
}

.confirm-btn {
  padding: 8px 16px;
  border-radius: 6px;
  border: none;
  background-color: var(--button-primary-bg);
  color: var(--text-primary);
  cursor: pointer;
}

.confirm-btn:hover {
  filter: brightness(1.1);
}
</style>