<template>
  <div class="webpage-item">
    <div class="webpage-info">
      <Icon name="webpage" class="webpage-icon" />
      <div class="webpage-details">
        <a :href="webpage.url" target="_blank" rel="noopener noreferrer" class="webpage-name">
          {{ webpage.url }}
        </a>
        <span class="webpage-meta">{{ webpage.date }}</span>
      </div>
    </div>
    <div class="webpage-actions">
      <button class="action-btn" @click="$emit('refresh')"><Icon name="refresh" /></button>
      <div class="status-indicator">
        <Icon
          v-if="webpage.status === 'completed'"
          name="status-completed"
          class="status-completed"
        />
        <Icon
          v-else-if="webpage.status === 'processing'"
          name="status-processing"
          class="status-loading"
        />
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
import type { KnowledgeUrl } from '@/stores/knowledgeBase'
import Icon from '@/components/AppIcon.vue'

defineProps({
  webpage: { type: Object as PropType<KnowledgeUrl>, required: true },
})

defineEmits(['delete', 'refresh'])
</script>

<style scoped>
.webpage-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 0;
  border-bottom: 1px solid var(--border-color);
}
.webpage-item:last-child {
  border-bottom: none;
}
.webpage-info {
  display: flex;
  align-items: center;
  gap: 12px;
}
.webpage-icon {
  font-size: 24px;
  color: var(--text-secondary);
}
.webpage-details {
  display: flex;
  flex-direction: column;
}
.webpage-name {
  color: var(--text-primary);
  text-decoration: none;
  white-space: normal;     /* 允许换行 */
  /* overflow: hidden;
  text-overflow: ellipsis;
  display: block; */
}
.webpage-name:hover {
  text-decoration: underline;
}
.webpage-meta {
  color: var(--text-secondary);
  font-size: 0.9em;
}

.webpage-actions {
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
  font-size: 20px;
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
