<template>
  <div class="app-container" :class="{ 'sidebar-collapsed': isSidebarCollapsed }">
    <AppSidebar
      :is-collapsed="isSidebarCollapsed"
      @toggle="toggleSidebar"
      @open-settings="openSettingsModal"
      @open-search="openSearchModal"
    />
    <ChatView />
  </div>

  <Teleport to="body">
    <SettingsModal v-if="isSettingsModalVisible" @close="closeSettingsModal" />

    <Transition name="modal-fade-up">
      <SearchModal v-if="isSearchModalVisible" @close="closeSearchModal" />
    </Transition>
  </Teleport>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import AppSidebar from './components/AppSidebar.vue'
import ChatView from './views/ChatView.vue'
import SettingsModal from './components/SettingsModal.vue'
import SearchModal from './components/SearchModal.vue'

const isSettingsModalVisible = ref(false)
const isSearchModalVisible = ref(false)
const isSidebarCollapsed = ref(false) // 新增状态：控制侧边栏

const openSettingsModal = () => {
  isSettingsModalVisible.value = true
}
const closeSettingsModal = () => {
  isSettingsModalVisible.value = false
}

const openSearchModal = () => {
  isSearchModalVisible.value = true
}
const closeSearchModal = () => {
  isSearchModalVisible.value = false
}

const toggleSidebar = () => {
  isSidebarCollapsed.value = !isSidebarCollapsed.value
}
</script>

<style scoped>
.app-container {
  display: flex;
  width: 100%;
  height: 100%;
  transition: filter 0.3s ease-in-out;
}

/* 当设置模态框打开时，给背景应用模糊效果 */
.app-container.modal-open {
  filter: blur(4px);
}
</style>
