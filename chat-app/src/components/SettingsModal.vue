<template>
  <div class="modal-overlay" @click.self="emit('close')">
    <div class="modal-content">
      <button class="close-button" @click="emit('close')">
        <Icon name="close" />
      </button>
      <div class="modal-layout">
        <div class="modal-nav">
          <button
            :class="['nav-item', { active: activeTab === 'general' }]"
            @click="activeTab = 'general'"
          >
            <Icon name="settings" />
            <span>通用设置</span>
          </button>
          <button
            :class="['nav-item', { active: activeTab === 'data' }]"
            @click="activeTab = 'data'"
          >
            <Icon name="data_management" />
            <span>数据管理</span>
          </button>
        </div>
        <div class="modal-main">
          <!-- 通用设置面板 -->
          <div v-if="activeTab === 'general'" class="settings-panel">
            <div class="setting-item">
              <label>主题</label>
              <select class="settings-dropdown">
                <option>系统</option>
              </select>
            </div>
            <div class="separator"></div>
            <div class="setting-item">
              <label>在聊天中显示路标建议</label>
              <div class="switch-container">
                <input type="checkbox" id="suggestions-toggle" class="switch-input" checked />
                <label for="suggestions-toggle" class="switch-label"></label>
              </div>
            </div>
            <div class="separator"></div>
            <div class="setting-item">
              <label>语言</label>
              <select class="settings-dropdown">
                <option>自动检测</option>
              </select>
            </div>
            <div class="separator"></div>
            <div class="setting-item">
              <label>已归档的聊天</label>
              <button class="settings-button">管理</button>
            </div>
            <div class="separator"></div>
            <div class="setting-item">
              <label>归档所有聊天</label>
              <button class="settings-button">全部归档</button>
            </div>
            <div class="separator"></div>
            <div class="setting-item">
              <label>删除所有聊天</label>
              <button class="settings-button danger">全部删除</button>
            </div>
            <div class="separator"></div>
            <div class="setting-item">
              <label>注销设备</label>
              <button class="settings-button">注销</button>
            </div>
          </div>

          <!-- 数据管理面板 -->
          <div v-if="activeTab === 'data'" class="settings-panel">
            <div class="setting-item">
              <label>为所有用户改进模型</label>
              <a href="#" class="toggle-link">开 ></a>
            </div>
            <div class="separator"></div>
            <div class="setting-item">
              <label>共享链接</label>
              <button class="settings-button">管理</button>
            </div>
            <div class="separator"></div>
            <div class="setting-item">
              <label>导出数据</label>
              <button class="settings-button">导出</button>
            </div>
            <div class="separator"></div>
            <div class="setting-item">
              <label>删除帐户</label>
              <button class="settings-button danger">删除</button>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import Icon from './AppIcon.vue'

const emit = defineEmits(['close'])
const activeTab = ref('general')
</script>

<style scoped>
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background-color: var(--bg-overlay);
  display: flex;
  justify-content: center;
  align-items: center;
  z-index: 1000;
  backdrop-filter: blur(8px);
}

.modal-content {
  background-color: var(--modal-bg);
  border-radius: var(--border-radius-large);
  width: 800px;
  height: 600px;
  position: relative;
  overflow: hidden;
  box-shadow: 0 10px 30px rgba(0, 0, 0, 0.5);
}

.close-button {
  position: absolute;
  top: 16px;
  left: 16px;
  background: none;
  border: none;
  color: var(--text-secondary);
  cursor: pointer;
  padding: 8px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 10;
  transition: background-color 0.2s, color 0.2s;
}
.close-button:hover {
  background-color: var(--bg-tertiary);
  color: var(--text-primary);
}
.close-button :deep(svg) {
  font-size: 20px;
}

.modal-layout {
  display: flex;
  height: 100%;
}

.modal-nav {
  width: 240px;
  background-color: var(--modal-nav-bg);
  padding: 60px 16px 16px;
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.nav-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px;
  border-radius: 8px;
  background: none;
  border: none;
  color: var(--text-secondary);
  cursor: pointer;
  font-size: 1em;
  text-align: left;
  width: 100%;
}

.nav-item:hover {
  background-color: var(--bg-tertiary);
  color: var(--text-primary);
}

.nav-item.active {
  background-color: var(--button-primary-bg);
  color: var(--text-primary);
}

.nav-item :deep(svg) {
  font-size: 18px;
}

.modal-main {
  flex-grow: 1;
  padding: 24px 32px;
  overflow-y: auto;
}

.settings-panel {
  display: flex;
  flex-direction: column;
}

.setting-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 20px 0;
  font-size: 1em;
}

.setting-item label {
  color: var(--text-primary);
}

.separator {
  height: 1px;
  background-color: var(--border-color);
  width: 100%;
}

.settings-button {
  background-color: var(--button-secondary-bg);
  color: var(--text-primary);
  border: none;
  padding: 8px 16px;
  border-radius: 8px;
  cursor: pointer;
  font-size: 0.9em;
}
.settings-button:hover {
  filter: brightness(1.2);
}

.settings-button.danger {
  background-color: transparent;
  color: var(--text-danger);
  border: 1px solid var(--text-danger);
}
.settings-button.danger:hover {
  background-color: var(--text-danger);
  color: var(--button-danger-text);
}

.settings-dropdown {
  background-color: var(--button-secondary-bg);
  color: var(--text-primary);
  border: 1px solid var(--border-color);
  padding: 8px 12px;
  border-radius: 8px;
}

.toggle-link {
  color: var(--link-color);
  text-decoration: none;
  font-weight: 500;
}

.switch-container {
  position: relative;
  width: 44px;
  height: 24px;
}

.switch-input {
  opacity: 0;
  width: 0;
  height: 0;
}

.switch-label {
  position: absolute;
  cursor: pointer;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background-color: var(--switch-bg-off);
  transition: 0.4s;
  border-radius: 34px;
}

.switch-label:before {
  position: absolute;
  content: '';
  height: 20px;
  width: 20px;
  left: 2px;
  bottom: 2px;
  background-color: white;
  transition: 0.4s;
  border-radius: 50%;
}

.switch-input:checked + .switch-label {
  background-color: var(--switch-bg-on);
}

.switch-input:checked + .switch-label:before {
  transform: translateX(20px);
}
</style>
