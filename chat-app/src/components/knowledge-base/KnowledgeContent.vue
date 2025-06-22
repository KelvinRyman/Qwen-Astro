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
        <div v-if="processingCount > 0" class="processing-indicator">
          <Icon name="status-processing" class="status-loading" />
          <span>{{ processingCount }} 个资源处理中</span>
        </div>
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

    <!-- 添加网页URL的模态框 -->
    <div v-if="showAddUrl" class="modal-overlay" @click.self="showAddUrl = false">
      <div class="modal-content add-url-modal">
        <h3>添加网页</h3>
        <div class="form-item">
          <input 
            type="url" 
            v-model="newUrl" 
            placeholder="输入网页URL (例如: https://www.example.com)" 
            @keyup.enter="addWebpage"
          />
        </div>
        <div v-if="urlError" class="error-message">{{ urlError }}</div>
        <div class="modal-actions">
          <button class="cancel-btn" @click="showAddUrl = false" :disabled="isAddingUrl">取消</button>
          <button 
            class="confirm-btn" 
            @click="addWebpage" 
            :disabled="!isValidUrl || isAddingUrl"
          >
            <span v-if="isAddingUrl">添加中...</span>
            <span v-else>添加</span>
          </button>
        </div>
      </div>
    </div>

    <div class="content-body">
      <!-- 文件部分 -->
      <section class="content-section">
        <header class="section-header" @click="isFilesCollapsed = !isFilesCollapsed">
          <Icon name="chevron-down" class="chevron" :class="{ collapsed: isFilesCollapsed }" />
          <h2>文件</h2>
          <span class="count-badge">{{ fileCount }}</span>
          <input 
            type="file" 
            ref="fileInputRef" 
            style="display: none" 
            @change="handleFileUpload"
            multiple
          />
          <button class="add-action-btn" @click.stop="openFileDialog($event)">+ 添加文件</button>
        </header>
        <div v-if="!isFilesCollapsed" class="section-content">
          <div 
            class="drop-zone"
            @dragover.prevent="dragover = true"
            @dragleave.prevent="dragover = false"
            @drop.prevent="handleFileDrop"
            :class="{ 'drag-over': dragover }"
          >
            <p>拖拽文件到这里</p>
            <small>支持 TXT, MD, HTML, PDF, DOCX, PPTX, XLSX, EPUB... 格式</small>
          </div>
          <div v-if="fileError" class="error-message">{{ fileError }}</div>
          <div class="file-list">
            <FileItem
              v-for="file in files"
              :key="file.id" 
              :file="file"
              @delete="deleteFile(file.id)"
              @refresh="refreshFileStatus(file.id)"
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
          <button class="add-action-btn" @click.stop="showAddUrl = true">+ 添加网址</button>
        </header>
        <div v-if="!isUrlsCollapsed" class="section-content">
          <div v-if="urls.length === 0" class="empty-state">
            <p>暂无网页，点击"添加网址"按钮添加</p>
          </div>
          <WebpageItem
            v-for="url in urls"
            :key="url.id"
            :webpage="url"
            @delete="deleteWebpage(url.id)"
            @refresh="refreshWebpageStatus(url.id)"
          />
        </div>
      </section>
    </div>
    <div v-if="isLoading" class="loading-overlay">加载中...</div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch, onMounted, onBeforeUnmount } from 'vue'
import type { PropType } from 'vue'
import type { KnowledgeFile, KnowledgeUrl, KnowledgeGroup } from '@/stores/knowledgeBase'
import { useKnowledgeBaseStore } from '@/stores/knowledgeBase'
import Icon from '@/components/AppIcon.vue'
import FileItem from './FileItem.vue'
import WebpageItem from './WebpageItem.vue'
import KnowledgeSearchModal from './KnowledgeSearchModal.vue'

const props = defineProps({
  group: { type: Object as PropType<KnowledgeGroup>, required: true },
  files: { type: Array as PropType<KnowledgeFile[]>, required: true },
  urls: { type: Array as PropType<KnowledgeUrl[]>, required: true },
  fileCount: { type: Number, required: true },
  urlCount: { type: Number, required: true },
  isLoading: { type: Boolean, default: false },
})

const emit = defineEmits(['refresh'])

const knowledgeBaseStore = useKnowledgeBaseStore()

// 折叠状态
const isFilesCollapsed = ref(false)
const isUrlsCollapsed = ref(false)
const isAllExpanded = ref(true)
const showSearch = ref(false)

// 文件上传相关
const fileInputRef = ref<HTMLInputElement | null>(null)
const dragover = ref(false)
const fileError = ref('')

// 添加网页URL相关
const showAddUrl = ref(false)
const newUrl = ref('')
const urlError = ref('')
const isAddingUrl = ref(false)

// 状态更新相关
const processingFiles = computed(() => knowledgeBaseStore.processingFiles)
const processingWebpages = computed(() => knowledgeBaseStore.processingWebpages)
const hasProcessingResources = computed(() => knowledgeBaseStore.hasProcessingResources)

// 显示处理中的资源数量
const processingCount = computed(() => {
  return processingFiles.value.length + processingWebpages.value.length
})

// 监听处理中的资源，自动展开相关部分
watch(processingFiles, (newVal) => {
  if (newVal.length > 0 && isFilesCollapsed.value) {
    isFilesCollapsed.value = false
  }
}, { deep: true })

watch(processingWebpages, (newVal) => {
  if (newVal.length > 0 && isUrlsCollapsed.value) {
    isUrlsCollapsed.value = false
  }
}, { deep: true })

// 组件挂载时，确保轮询启动
onMounted(() => {
  if (hasProcessingResources.value) {
    knowledgeBaseStore.startPolling()
  }
})

// 组件卸载前，停止轮询
onBeforeUnmount(() => {
  knowledgeBaseStore.stopPolling()
})

const isValidUrl = computed(() => {
  if (!newUrl.value) return false
  try {
    new URL(newUrl.value)
    return true
  } catch (e) {
    return false
  }
})

const toggleAllSections = () => {
  isAllExpanded.value = !isAllExpanded.value
  isFilesCollapsed.value = !isAllExpanded.value
  isUrlsCollapsed.value = !isAllExpanded.value
}

// 打开文件选择对话框
function openFileDialog(event?: MouseEvent) {
  // 阻止事件冒泡
  if (event) {
    event.stopPropagation();
  }
  
  if (fileInputRef.value) {
    fileInputRef.value.click();
  }
}

// 处理文件上传
async function handleFileUpload(event: Event) {
  const input = event.target as HTMLInputElement
  if (!input.files || input.files.length === 0) return
  
  fileError.value = ''
  
  try {
    // 逐个上传文件
    for (let i = 0; i < input.files.length; i++) {
      const file = input.files[i]
      await knowledgeBaseStore.uploadFile(file)
    }
    
    // 重置文件输入
    if (fileInputRef.value) fileInputRef.value.value = ''
    
    // 通知父组件刷新
    emit('refresh')
  } catch (error) {
    console.error('文件上传失败:', error)
    fileError.value = '文件上传失败，请重试'
  }
}

// 处理文件拖放
async function handleFileDrop(event: DragEvent) {
  dragover.value = false
  fileError.value = ''
  
  if (!event.dataTransfer?.files || event.dataTransfer.files.length === 0) return
  
  try {
    // 逐个上传文件
    for (let i = 0; i < event.dataTransfer.files.length; i++) {
      const file = event.dataTransfer.files[i]
      await knowledgeBaseStore.uploadFile(file)
    }
    
    // 通知父组件刷新
    emit('refresh')
  } catch (error) {
    console.error('文件上传失败:', error)
    fileError.value = '文件上传失败，请重试'
  }
}

// 添加网页
async function addWebpage() {
  if (!isValidUrl.value || isAddingUrl.value) return
  
  isAddingUrl.value = true
  urlError.value = ''
  
  try {
    await knowledgeBaseStore.addWebpage(newUrl.value)
    showAddUrl.value = false
    newUrl.value = ''
    
    // 通知父组件刷新
    emit('refresh')
  } catch (error) {
    console.error('添加网页失败:', error)
    urlError.value = '添加网页失败，请重试'
  } finally {
    isAddingUrl.value = false
  }
}

// 删除文件
async function deleteFile(fileId: string) {
  try {
    await knowledgeBaseStore.deleteFile(fileId)
    // 通知父组件刷新
    emit('refresh')
  } catch (error) {
    console.error('删除文件失败:', error)
  }
}

// 删除网页
async function deleteWebpage(urlId: string) {
  try {
    await knowledgeBaseStore.deleteUrl(urlId)
    // 通知父组件刷新
    emit('refresh')
  } catch (error) {
    console.error('删除网页失败:', error)
  }
}

// 刷新文件状态
async function refreshFileStatus(fileId: string) {
  await knowledgeBaseStore.refreshFileStatus(fileId)
  // 通知父组件刷新
  emit('refresh')
}

// 刷新网页状态
async function refreshWebpageStatus(urlId: string) {
  await knowledgeBaseStore.refreshWebpageStatus(urlId)
  // 通知父组件刷新
  emit('refresh')
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
  background: var(--bg-tertiary);
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
  transition: background-color 0.2s;
}
.drop-zone.drag-over {
  background-color: rgba(0, 0, 0, 0.2);
  border-color: var(--button-primary-bg);
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

.empty-state {
  text-align: center;
  color: var(--text-secondary);
  padding: 20px 0;
}

.error-message {
  color: var(--text-danger);
  font-size: 0.9em;
  margin: 8px 0;
}

/* 添加URL模态框样式 */
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background-color: var(--bg-overlay);
  display: flex;
  justify-content: center;
  align-items: center;
  z-index: 1000;
  backdrop-filter: blur(8px);
}

.modal-content {
  background-color: var(--modal-bg);
  border-radius: var(--border-radius-large);
  padding: 24px;
  width: 100%;
  max-width: 500px;
  box-shadow: 0 10px 30px rgba(0, 0, 0, 0.5);
}

.add-url-modal h3 {
  margin-top: 0;
  margin-bottom: 16px;
}

.form-item {
  margin-bottom: 16px;
}

.form-item input {
  width: 100%;
  padding: 10px 12px;
  border-radius: 8px;
  background-color: var(--bg-secondary);
  border: 1px solid var(--border-color);
  color: var(--text-primary);
  font-size: 1em;
}

.form-item input:focus {
  outline: none;
  border-color: var(--button-primary-bg);
  box-shadow: 0 0 0 2px var(--button-primary-bg-light);
}

.modal-actions {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
  margin-top: 16px;
}

.cancel-btn,
.confirm-btn {
  border: none;
  padding: 8px 16px;
  border-radius: 8px;
  cursor: pointer;
  font-size: 0.9em;
  font-weight: 500;
}

.cancel-btn {
  background-color: var(--button-secondary-bg);
  color: var(--text-primary);
}

.confirm-btn {
  background-color: var(--button-primary-bg);
  color: var(--button-primary-text);
}

.confirm-btn:disabled {
  background-color: var(--button-disabled-bg);
  color: var(--text-disabled);
  cursor: not-allowed;
}

.header-actions {
  display: flex;
  align-items: center;
  gap: 8px;
}

.processing-indicator {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 0.9em;
  color: var(--text-secondary);
  background-color: var(--bg-tertiary);
  padding: 4px 10px;
  border-radius: 16px;
}

.processing-indicator .status-loading {
  font-size: 14px;
  animation: spin 1s linear infinite;
}

@keyframes spin {
  100% { transform: rotate(360deg); }
}
</style>
