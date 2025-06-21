<template>
  <div class="file-item">
    <div class="file-info">
      <Icon name="file" class="file-icon" />
      <!-- 以后可以根据 file.type 动态切换 -->
      <div class="file-details">
        <span class="file-name">{{ file.name }}</span>
        <span class="file-meta">{{ file.date }} · {{ file.size }}</span>
      </div>
    </div>
    <div class="file-actions">
      <button class="action-btn" @click="$emit('refresh')"><Icon name="refresh" /></button>
      <div class="status-indicator">
        <Icon v-if="file.status === 'completed'" name="status-completed" class="status-completed" />
        <Icon v-else-if="file.status === 'processing'" name="status-processing" class="status-loading" />
        <Icon v-else name="status-failed" class="status-failed" />
      </div>
      <button class="action-btn delete-btn" @click="$emit('delete')">
        <Icon name="delete" />
      </button>
    </div>
  </div>
</template>

<script setup lang="ts">
import type { PropType } from 'vue'
import type { KnowledgeFile } from '@/stores/knowledgeBase'
import Icon from '@/components/AppIcon.vue'

defineProps({
  file: { type: Object as PropType<KnowledgeFile>, required: true },
})

defineEmits(['delete', 'refresh'])
</script>

<style scoped>
.file-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 0;
  border-bottom: 1px solid var(--border-color);
}
.file-item:last-child {
  border-bottom: none;
}
.file-info {
  display: flex;
  align-items: center;
  gap: 12px;
}
.file-icon {
  font-size: 24px;
  color: var(--text-secondary);
}
.file-details {
  display: flex;
  flex-direction: column;
}
.file-name {
  color: var(--text-primary);
}
.file-meta {
  color: var(--text-secondary);
  font-size: 0.9em;
}

.file-actions {
  display: flex;
  align-items: center;
  gap: 16px;
}
.action-btn {
  background: none;
  border: none;
  color: var(--text-secondary);
  cursor: pointer;
  padding: 4px;
  font-size: 20px
}
.action-btn:hover {
  color: var(--text-primary);
}
.delete-btn:hover {
  color: var(--text-danger);
}
.status-indicator .status-completed {
  color: #4caf50; /* Green */
  font-size: 18px;
}
.status-indicator .status-loading {
  color: var(--text-secondary);
  font-size: 18px;
  animation: spin 1s linear infinite;
}
@keyframes spin {
  100% { transform: rotate(360deg); }
}
.status-indicator .status-failed {
  color: var(--text-danger);
  font-size: 18px;
}
</style>
