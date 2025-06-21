<template>
  <div class="group-list-container">
    <div v-if="isLoading" class="loading">加载中...</div>
    <ul v-else class="group-list">
      <li
        v-for="group in groups"
        :key="group.id"
        class="group-item"
        :class="{ active: group.id === activeGroupId }"
        @click="$emit('select-group', group.id)"
      >
        <Icon name="group" />
        <span>{{ group.name }}</span>
      </li>
    </ul>
    <button class="add-button" @click="$emit('add-group')">
      <Icon name="plus" />
      <span>添加</span>
    </button>
  </div>
</template>

<script setup lang="ts">
import type { KnowledgeGroup } from '@/stores/knowledgeBase'
import Icon from '@/components/AppIcon.vue'

defineProps<{
  groups: KnowledgeGroup[]
  activeGroupId: string | null
  isLoading: boolean
}>()

defineEmits(['select-group', 'add-group'])
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
  gap: 12px;
  margin: 8px 0;
  padding: 10px 14px;
  border-radius: 8px;
  cursor: pointer;
  color: var(--text-secondary);
  transition:
    background-color 0.2s,
    color 0.2s;
}
.group-item:hover {
  background-color: var(--bg-tertiary);
  color: var(--text-primary);
}
.group-item.active {
  background-color: var(--button-primary-bg);
  color: var(--text-primary);
}
.group-item :deep(svg) {
  font-size: 18px;
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
