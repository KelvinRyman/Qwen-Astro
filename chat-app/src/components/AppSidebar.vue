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
        <a href="#" class="sidebar-link" @click.prevent="router.push('/')">
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
        <!-- 聊天历史记录为空 -->
      </div>
    </div>

    <div class="sidebar-footer">
      <button class="sidebar-link settings" @click="emit('open-settings')">
        <Icon name="settings" />
        <span class="link-text">设置</span>
      </button>
    </div>
  </div>
</template>

<script setup lang="ts">
import Icon from './AppIcon.vue'
import { useRouter } from 'vue-router';

defineProps<{
  isCollapsed: boolean;
}>()

const emit = defineEmits(['toggle', 'open-settings', 'open-search'])

const router = useRouter();

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
.sidebar-link, .settings {
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
}
.sidebar-link:hover, .settings:hover {
  background-color: var(--bg-tertiary);
}
.sidebar-link :deep(svg), .settings :deep(svg) {
  font-size: 20px;
  flex-shrink: 0;
}
.sidebar-link.active {
  background-color: var(--bg-active);
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
  max-width: 150px;
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
</style>