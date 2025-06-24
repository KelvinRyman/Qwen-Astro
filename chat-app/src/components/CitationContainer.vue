<template>
  <div v-if="sources && sources.length > 0" class="citation-container">
    <div class="citation-list">
      <CitationCard 
        v-for="source in sources" 
        :key="source.id" 
        :source="source" 
      />
    </div>
  </div>
</template>

<script setup lang="ts">
import type { PropType } from 'vue'
import type { SourceNode } from '@/api/chatApi'
import CitationCard from './CitationCard.vue'

defineProps({
  sources: { 
    type: Array as PropType<SourceNode[]>, 
    required: true 
  }
})
</script>

<style scoped>
.citation-container {
  margin-bottom: 16px;
}

.citation-list {
  display: flex;
  gap: 12px;
  overflow-x: auto;
  padding: 4px 0;
  scrollbar-width: thin;
  scrollbar-color: var(--text-secondary) transparent;
}

.citation-list::-webkit-scrollbar {
  height: 6px;
}

.citation-list::-webkit-scrollbar-track {
  background: transparent;
}

.citation-list::-webkit-scrollbar-thumb {
  background-color: var(--text-secondary);
  border-radius: 3px;
}

.citation-list::-webkit-scrollbar-thumb:hover {
  background-color: var(--text-primary);
}

/* 确保卡片不会被压缩 */
.citation-list > * {
  flex-shrink: 0;
}
</style>
