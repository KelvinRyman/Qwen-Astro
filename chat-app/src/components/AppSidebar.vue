<template>
  <div class="sidebar">
    <div class="sidebar-header"> 
      <button class="sidebar-button icon-only">
        <Icon name="sidebar" />
      </button>
    </div>
    <div class="sidebar-content">
      <div class="sidebar-section">
        <a href="#" class="sidebar-link">
          <Icon name="new_chat" />
          <span>新聊天</span>
        </a>
        <a href="#" class="sidebar-link" @click.prevent="$emit('open-search')">
          <Icon name="search" />
          <span>搜索</span>
        </a>
        <a href="#" class="sidebar-link">
          <Icon name="knowledge" />
          <span>知识库</span>
        </a>
        <a href="#" class="sidebar-link">
          <Icon name="agent" />
          <span>Agent</span>
        </a>
      </div>
      <div class="sidebar-section">
        <div class="section-title">聊天</div>
        <!-- 聊天历史记录为空 -->
      </div>
    </div>
    <div class="sidebar-footer">
      <button class="sidebar-button settings" @click="emit('open-settings')">
        <Icon name="settings" />
        <span>设置</span>
      </button>
    </div>
  </div>
</template>

<script setup lang="ts">
import Icon from './AppIcon.vue'

const emit = defineEmits(['open-settings', 'open-search'])
</script>

<style scoped>
.sidebar {
  width: var(--sidebar-width);
  background-color: var(--bg-primary);
  display: flex;
  flex-direction: column;
  height: 100vh;
  padding: 8px;
  color: var(--text-primary);
}

.sidebar-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 8px 4px;
}

.sidebar-content {
  flex-grow: 1;
  overflow-y: auto;
  padding: 8px 4px;
}

.sidebar-footer {
  padding: 8px 4px;
}

.sidebar-button {
  display: flex;
  align-items: center;
  gap: 12px;
  background-color: transparent;
  border: none;
  color: var(--text-primary);
  padding: 10px 12px;
  border-radius: 8px;
  cursor: pointer;
  font-size: 1em;
  width: 100%;
  text-align: left;
}

.sidebar-button:hover {
  background-color: var(--bg-tertiary);
}

.sidebar-button.icon-only {
  width: auto;
  flex-grow: 0;
  margin-left: auto;
}
.sidebar-button.icon-only :deep(svg) {
  font-size: 20px;
}

.sidebar-section {
  margin-bottom: 24px;
}

.section-title {
  padding: 0 12px 8px;
  font-size: 14px;
  color: var(--text-secondary);
  font-weight: 500;
  user-select: none;
}

.sidebar-link {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 10px 12px;
  border-radius: 8px;
  text-decoration: none;
  color: var(--text-primary);
  font-size: 1em;
}

.sidebar-link:hover {
  background-color: var(--bg-tertiary);
}

.sidebar-link :deep(svg) {
  font-size: 20px;
}

.settings {
  font-size: 1.1em;
}

.settings :deep(svg) {
  font-size: 20px;
}
</style>
