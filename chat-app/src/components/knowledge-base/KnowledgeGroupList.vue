<template>
  <div class="group-list-container">
    <div v-if="isLoading" class="loading">加载中...</div>
    <ul v-else class="group-list">
      <li
        v-for="group in groups"
        :key="group.id"
        class="group-item"
        :class="{ active: group.id === activeGroupId, 'menu-open': openMenuGroupId === group.id }"
        @click="handleSelectGroup(group.id)"
      >
        <div class="group-item-content">
          <Icon name="group" />
          <span class="group-name">{{ group.name }}</span>
        </div>
        <div class="group-item-actions" @click.stop>
          <ItemDropdownMenu
            :is-open="openMenuGroupId === group.id"
            @toggle="toggleMenu(group.id)"
            @close="openMenuGroupId = null"
            @rename="handleRename(group.id)"
            @delete="handleDelete(group.id)"
          />
        </div>
      </li>
    </ul>
    <button class="add-button" @click="$emit('add-group')">
      <Icon name="plus" />
      <span>添加</span>
    </button>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import type { KnowledgeGroup } from '@/stores/knowledgeBase'
import Icon from '@/components/AppIcon.vue'
import ItemDropdownMenu from '@/components/ItemDropdownMenu.vue'

defineProps<{
  groups: KnowledgeGroup[]
  activeGroupId: string | null
  isLoading: boolean
}>()

const emit = defineEmits(['select-group', 'add-group', 'rename-group', 'delete-group'])

const openMenuGroupId = ref<string | null>(null)

const handleSelectGroup = (groupId: string) => {
  if (openMenuGroupId.value) {
    // If a menu is open, the first click should close it, not switch groups.
    openMenuGroupId.value = null
  } else {
    emit('select-group', groupId)
  }
}

const toggleMenu = (groupId: string) => {
  openMenuGroupId.value = openMenuGroupId.value === groupId ? null : groupId
}

const handleRename = (groupId: string) => {
  openMenuGroupId.value = null
  emit('rename-group', groupId)
}

const handleDelete = (groupId: string) => {
  openMenuGroupId.value = null
  emit('delete-group', groupId)
}
</script>

<style scoped>
.loading {
  display: flex;
  align-items: center;
  justify-content: center;
  height: 100%;
  color: var(--text-secondary);
}
.group-list-container {
  width: 240px;
  background-color: var(--bg-mid);
  padding: 16px;
  display: flex;
  flex-direction: column;
  flex-shrink: 0;
  border-right: 1px solid var(--border-color);
  height: 100%;
}
.group-list {
  list-style: none;
  padding: 0;
  margin: 0;
  flex-grow: 1;
}
.group-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin: 2px 0;
  padding: 0;
  border-radius: 8px;
  cursor: pointer;
  color: var(--text-secondary);
  transition:
    background-color 0.2s,
    color 0.2s;
  height: 40px;
  box-sizing: border-box;
}
.group-item:hover {
  background-color: var(--bg-tertiary);
  color: var(--text-primary);
}
.group-item.active {
  background-color: var(--button-primary-bg);
  color: var(--text-primary);
}
.group-item-content {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 0 14px;
  height: 100%;
  pointer-events: none;
}
.group-item :deep(svg) {
  font-size: 18px;
}
.group-name {
  flex-grow: 1;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
.group-item-actions {
  opacity: 0;
  transition: opacity 0.2s ease;
  padding-right: 8px;
  display: flex;
  align-items: center;
  height: 100%;
}
.group-item:hover .group-item-actions,
.group-item.menu-open .group-item-actions {
  opacity: 1;
}
.add-button {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  width: 100%;
  padding: 10px;
  background: none;
  border: 1px dashed var(--border-color);
  color: var(--text-secondary);
  border-radius: 8px;
  cursor: pointer;
}
.add-button:hover {
  background-color: var(--bg-tertiary);
  color: var(--text-primary);
}
</style>
