<template>
  <div class="search-overlay" @click.self="$emit('close')">
    <div class="search-modal-content">
      <div class="search-header">
        <input 
          v-model="searchQuery" 
          type="text" 
          class="search-input" 
          placeholder="搜索知识库..." 
          @keyup.enter="handleSearch"
        />
        <button class="search-button" @click="handleSearch">
          <Icon name="search" />
        </button>
        <button class="close-button" @click="$emit('close')">
          <Icon name="close" />
        </button>
      </div>
      <div class="search-body">
        <div v-if="isLoading" class="loading-state">
          搜索中...
        </div>
        <div v-else-if="searchResults.length === 0 && hasSearched" class="empty-state">
          未找到相关结果
        </div>
        <div v-else-if="searchResults.length > 0" class="results-list">
          <div v-for="result in searchResults" :key="result.id" class="result-item">
            <div class="result-title">
              <Icon :name="result.type === 'file' ? 'file' : 'webpage'" />
              <span>{{ result.title }}</span>
            </div>
            <p class="result-content">{{ result.content }}</p>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue';
import Icon from '@/components/AppIcon.vue';

interface SearchResult {
  id: string;
  type: 'file' | 'webpage';
  title: string;
  content: string;
}

const searchQuery = ref('');
const searchResults = ref<SearchResult[]>([]);
const isLoading = ref(false);
const hasSearched = ref(false);

// 预留的API请求函数
const searchKnowledgeBase = async (query: string) => {
  // TODO: 实现实际的API调用
  // 这里是API调用的示例结构
  try {
    const response = await fetch('/api/knowledge/search', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ query }),
    });
    return await response.json();
  } catch (error) {
    console.error('搜索请求失败:', error);
    return [];
  }
};

const handleSearch = async () => {
  if (!searchQuery.value.trim()) return;
  
  isLoading.value = true;
  hasSearched.value = true;
  
  try {
    const results = await searchKnowledgeBase(searchQuery.value);
    searchResults.value = results;
  } catch (error) {
    console.error('搜索失败:', error);
    searchResults.value = [];
  } finally {
    isLoading.value = false;
  }
};

defineEmits(['close']);
</script>

<style scoped>
.search-overlay {
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background-color: transparent;
  display: flex;
  justify-content: center;
  align-items: flex-start;
  padding-top: 20vh;
  z-index: 1000;
}

.search-modal-content {
  width: 100%;
  max-width: 700px;
  max-height: 70vh;
  background-color: var(--bg-tertiary);
  border-radius: var(--border-radius-large);
  box-shadow: 0 10px 40px rgba(0, 0, 0, 0.5);
  overflow: hidden;
  display: flex;
  flex-direction: column;
  transition: transform 0.3s ease, opacity 0.3s ease;
}

.search-header {
  display: flex;
  align-items: center;
  padding: 12px;
  border-bottom: 1px solid var(--border-color);
  flex-shrink: 0;
  gap: 8px;
}

.search-input {
  flex-grow: 1;
  background: transparent;
  border: none;
  outline: none;
  color: var(--text-primary);
  font-size: 16px;
  padding: 8px;
}

.search-input::placeholder {
  color: var(--text-placeholder);
}

.search-button,
.close-button {
  background: transparent;
  border: none;
  color: var(--text-secondary);
  cursor: pointer;
  padding: 8px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: background-color 0.2s;
}

.search-button:hover,
.close-button:hover {
  background-color: #4f5058;
}

.search-button :deep(svg),
.close-button :deep(svg) {
  font-size: 16px;
}

.search-body {
  padding: 16px;
  overflow-y: auto;
}

.loading-state,
.empty-state {
  text-align: center;
  padding: 24px;
  color: var(--text-secondary);
}

.results-list {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.result-item {
  padding: 16px;
  border-radius: 8px;
  background-color: var(--bg-secondary);
  cursor: pointer;
  transition: background-color 0.2s;
}

.result-item:hover {
  background-color: var(--button-primary-bg);
}

.result-title {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 8px;
  color: var(--text-primary);
}

.result-title :deep(svg) {
  font-size: 16px;
}

.result-content {
  color: var(--text-secondary);
  font-size: 14px;
  margin: 0;
  line-height: 1.5;
}
</style> 