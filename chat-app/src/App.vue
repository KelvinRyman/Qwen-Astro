<template>
  <div class="app-container" :class="{ 'sidebar-collapsed': isSidebarCollapsed }">
    <AppSidebar
      :is-collapsed="isSidebarCollapsed"
      @toggle="toggleSidebar"
      @show-view="showView"
      @open-settings="openSettingsModal"
      @open-search="openSearchModal"
    />
    <main class="main-content">
      <router-view />
    </main>
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
import SettingsModal from './components/SettingsModal.vue'
import SearchModal from './components/SearchModal.vue'

type ViewName = 'chat' | 'knowledge'

const currentView = ref<ViewName>('chat')
const isSettingsModalVisible = ref(false)
const isSearchModalVisible = ref(false)
const isSidebarCollapsed = ref(false)

const showView = (viewName: ViewName) => {
  currentView.value = viewName
}

const toggleSidebar = () => {
  isSidebarCollapsed.value = !isSidebarCollapsed.value
}
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
}
.main-content {
  flex-grow: 1;
  height: 100vh;
  overflow: hidden;
}
</style>
