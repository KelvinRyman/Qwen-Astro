<template>
  <div class="app-container" :class="{ 'modal-open': isSettingsModalVisible }">
    <AppSidebar @open-settings="openSettingsModal" @open-search="openSearchModal" />
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
import ChatView from './components/ChatView.vue'
import SettingsModal from './components/SettingsModal.vue'
import SearchModal from './components/SearchModal.vue' // 引入新组件

const isSettingsModalVisible = ref(false)
const isSearchModalVisible = ref(false) // 新增状态

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
