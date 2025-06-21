<template>
  <div class="content-container">
    <header class="content-header">
      <div class="model-tags">
        <span class="header-label">嵌入模型</span>
        <span class="tag active">{{ group.embedding_model }}</span>
        <span class="header-label" style="margin-left: 16px">重排模型</span>
        <span class="tag" v-if="group.rerank_model">{{ group.rerank_model }}</span>
      </div>
      <div class="header-actions">
        <button class="action-btn" @click="showSearch = true"><Icon name="search" /></button>
        <button class="action-btn" @click="toggleAllSections">
          <Icon :name="isAllExpanded ? 'collapse' : 'expand'" />
        </button>
      </div>
    </header>

    <Transition name="modal-fade-up">
      <KnowledgeSearchModal
        v-if="showSearch"
        @close="showSearch = false"
      />
    </Transition>

    <div class="content-body">
      <!-- 文件部分 -->
      <section class="content-section">
        <header class="section-header" @click="isFilesCollapsed = !isFilesCollapsed">
          <Icon name="chevron-down" class="chevron" :class="{ collapsed: isFilesCollapsed }" />
          <h2>文件</h2>
          <span class="count-badge">{{ fileCount }}</span>
          <button class="add-action-btn">+ 添加文件</button>
        </header>
        <div v-if="!isFilesCollapsed" class="section-content">
          <div class="drop-zone">
            <p>拖拽文件到这里</p>
            <small>支持 TXT, MD, HTML, PDF, DOCX, PPTX, XLSX, EPUB... 格式</small>
          </div>
          <div class="file-list">
              <FileItem
                v-for="file in files"
                :key="file.id" 
                :file="file"
                @delete="$emit('delete-file', file.id)"
                @refresh="$emit('refresh-file', file.id)"
              />
          </div>
        </div>
      </section>

      <!-- 网址部分 -->
      <section class="content-section">
        <header class="section-header" @click="isUrlsCollapsed = !isUrlsCollapsed">
          <Icon name="chevron-down" class="chevron" :class="{ collapsed: isUrlsCollapsed }" />
          <h2>网址</h2>
          <span class="count-badge">{{ urlCount }}</span>
          <button class="add-action-btn">+ 添加网址</button>
        </header>
        <div v-if="!isUrlsCollapsed" class="section-content">
          <WebpageItem
            v-for="url in urls"
            :key="url.id"
            :webpage="url"
            @delete="$emit('delete-file', url.id)"
            @refresh="$emit('refresh-file', url.id)"
          />
        </div>
      </section>
    </div>
    <div v-if="isLoading" class="loading-overlay">加载中...</div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import type { PropType } from 'vue'
import type { KnowledgeFile, KnowledgeUrl, KnowledgeGroup } from '@/stores/knowledgeBase'
import Icon from '@/components/AppIcon.vue'
import FileItem from './FileItem.vue'
import WebpageItem from './WebpageItem.vue'
import KnowledgeSearchModal from './KnowledgeSearchModal.vue'

defineProps({
  group: { type: Object as PropType<KnowledgeGroup>, required: true },
  files: { type: Array as PropType<KnowledgeFile[]>, required: true },
  urls: { type: Array as PropType<KnowledgeUrl[]>, required: true },
  fileCount: { type: Number, required: true },
  urlCount: { type: Number, required: true },
  isLoading: { type: Boolean, default: false },
})

defineEmits(['delete-file', 'refresh-file'])

const isFilesCollapsed = ref(false)
const isUrlsCollapsed = ref(false)
const isAllExpanded = ref(true)
const showSearch = ref(false)

const toggleAllSections = () => {
  isAllExpanded.value = !isAllExpanded.value
  isFilesCollapsed.value = !isAllExpanded.value
  isUrlsCollapsed.value = !isAllExpanded.value
}
</script>

<style scoped>
/* 样式非常多，这里只列出关键部分 */
.content-container {
  position: relative;
  flex-grow: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}
.content-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 24px;
  border-bottom: 1px solid var(--border-color);
  flex-shrink: 0;
}
.content-section {
  margin: 16px 0;
  border-radius: 8px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.5);
  padding: 16px;
}
.model-tags,
.header-actions {
  display: flex;
  align-items: center;
  gap: 8px;
}
.header-label {
  color: var(--text-secondary);
  margin-right: 8px;
}
.tag {
  background: var(--bg-tertiary);
  border: 1px solid var(--border-color);
  color: var(--text-secondary);
  padding: 4px 12px;
  border-radius: 8px;
  cursor: pointer;
}
.tag.active {
  background: var(--button-primary-bg);
  color: var(--text-primary);
  border-color: var(--button-primary-bg);
}
.action-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  background-color: transparent;
  border: none;
  color: var(--text-primary);
  border-radius: 8px;
  cursor: pointer;
  width: 40px;
  height: 40px;
  padding: 0;
  flex-shrink: 0;
  transition:
    background-color 0.2s,
    color 0.2s;
}
.action-btn:hover {
  background-color: var(--bg-tertiary);
}
.action-btn :deep(svg) {
  font-size: 20px;
}

.content-body {
  flex-grow: 1;
  overflow-y: auto;
  padding: 24px;
}
.section-header {
  display: flex;
  align-items: center;
  gap: 8px;
  cursor: pointer;
  margin-bottom: 16px;
}
.section-header h2 {
  font-size: 1em;
  margin: 0;
}
.chevron {
  transition: transform 0.2s;
}
.chevron.collapsed {
  transform: rotate(-90deg);
}
.count-badge {
  background-color: var(--bg-tertiary);
  color: var(--text-secondary);
  font-size: 0.8em;
  padding: 2px 6px;
  border-radius: 6px;
}
.add-action-btn {
  margin-left: auto;
  color: var(--text-secondary);
  background: none;
  border: none;
  cursor: pointer;
}
.add-action-btn:hover {
  color: var(--text-primary);
}

.drop-zone {
  border: 1px dashed var(--border-color);
  border-radius: 8px;
  padding: 32px;
  text-align: center;
  margin-bottom: 16px;
  background-color: rgba(0, 0, 0, 0.1);
}
.drop-zone p {
  margin: 0 0 8px 0;
  font-size: 1.1em;
}
.drop-zone small {
  color: var(--text-secondary);
}

.loading-overlay {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 10;
}
</style>
