<template>
  <div class="image-upload-demo">
    <h1>图片上传功能演示</h1>
    
    <div class="demo-section">
      <h2>1. 图片选择和预览</h2>
      <div class="upload-area">
        <button 
          class="upload-button"
          :class="{ 'drag-over': isDragOver }"
          @click="openFileSelector"
          @dragover="onDragOver"
          @dragenter="onDragEnter"
          @dragleave="onDragLeave"
          @drop="onDrop"
        >
          <Icon name="plus" />
          <span>点击选择图片或拖拽到此处</span>
        </button>
      </div>
      
      <div v-if="hasImages" class="preview-section">
        <h3>已选择的图片 ({{ imageCount }}/5)</h3>
        <ImageThumbnail :images="selectedImages" @remove="removeImage" />
        
        <div class="actions">
          <button @click="clearImages" class="clear-button">清空所有</button>
          <button @click="testSendMessage" class="test-button" :disabled="!hasImages">
            测试发送消息
          </button>
        </div>
      </div>
    </div>

    <div class="demo-section">
      <h2>2. 工具互斥逻辑演示</h2>
      <div class="tools-demo">
        <div class="tool-item">
          <label>
            <input type="checkbox" v-model="mockKnowledgeBase" :disabled="hasImages">
            知识库模式
          </label>
          <span v-if="hasImages" class="disabled-hint">（图片模式下禁用）</span>
        </div>
        
        <div class="tool-item">
          <label>
            <input type="checkbox" v-model="mockDeepThinking">
            深度思考
          </label>
          <span class="enabled-hint">（可与图片模式共存）</span>
        </div>
        
        <div class="tool-item">
          <label>
            <input type="checkbox" v-model="mockWebSearch">
            网页搜索
          </label>
          <span class="enabled-hint">（可与图片模式共存）</span>
        </div>
      </div>
    </div>

    <div v-if="errors.length > 0" class="error-section">
      <h3>错误信息</h3>
      <ul>
        <li v-for="(error, index) in errors" :key="index" class="error-item">
          <strong>{{ error.file || '系统' }}:</strong> {{ error.error }}
        </li>
      </ul>
    </div>

    <div v-if="testResult" class="result-section">
      <h3>测试结果</h3>
      <pre>{{ testResult }}</pre>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, watch } from 'vue';
import Icon from '@/components/AppIcon.vue';
import ImageThumbnail from '@/components/ImageThumbnail.vue';
import { useImageUpload } from '@/composables/useImageUpload';

// 模拟工具状态
const mockKnowledgeBase = ref(false);
const mockDeepThinking = ref(false);
const mockWebSearch = ref(false);
const testResult = ref('');

// 错误处理
const errors = ref<{ file: string; error: string }[]>([]);

// 使用图片上传组合式函数
const {
  selectedImages,
  isUploading,
  isDragOver,
  hasImages,
  imageCount,
  openFileSelector,
  removeImage,
  clearImages,
  getImageBase64List,
  onDragOver,
  onDragEnter,
  onDragLeave,
  onDrop
} = useImageUpload({
  maxImages: 5,
  onError: (errorList) => {
    errors.value = errorList;
    setTimeout(() => {
      errors.value = [];
    }, 5000);
  },
  onSuccess: (images) => {
    console.log('成功上传图片:', images);
  }
});

// 监听图片选择状态，实现与知识库的互斥逻辑
watch(hasImages, (newValue) => {
  if (newValue) {
    mockKnowledgeBase.value = false;
  }
});

// 测试发送消息
const testSendMessage = () => {
  const imageBase64List = getImageBase64List();
  testResult.value = JSON.stringify({
    message: '这是一条包含图片的测试消息',
    images: imageBase64List.map(img => img.substring(0, 50) + '...'),
    imageCount: imageBase64List.length,
    tools: {
      knowledgeBase: mockKnowledgeBase.value,
      deepThinking: mockDeepThinking.value,
      webSearch: mockWebSearch.value
    }
  }, null, 2);
};
</script>

<style scoped>
.image-upload-demo {
  max-width: 800px;
  margin: 0 auto;
  padding: 20px;
}

.demo-section {
  margin-bottom: 32px;
  padding: 20px;
  border: 1px solid var(--border-color);
  border-radius: 8px;
  background: var(--bg-primary);
}

.upload-area {
  margin-bottom: 20px;
}

.upload-button {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 12px;
  width: 100%;
  padding: 40px 20px;
  border: 2px dashed var(--border-color);
  border-radius: 8px;
  background: var(--bg-secondary);
  color: var(--text-secondary);
  cursor: pointer;
  transition: all 0.3s ease;
}

.upload-button:hover,
.upload-button.drag-over {
  border-color: var(--accent-color);
  background: var(--bg-primary);
  color: var(--accent-color);
}

.preview-section {
  margin-top: 20px;
}

.actions {
  display: flex;
  gap: 12px;
  margin-top: 16px;
}

.clear-button,
.test-button {
  padding: 8px 16px;
  border: 1px solid var(--border-color);
  background: var(--bg-primary);
  color: var(--text-primary);
  border-radius: 6px;
  cursor: pointer;
  font-size: 14px;
}

.test-button {
  background: var(--accent-color);
  color: white;
  border-color: var(--accent-color);
}

.test-button:disabled {
  background: var(--text-tertiary);
  border-color: var(--text-tertiary);
  cursor: not-allowed;
}

.tools-demo {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.tool-item {
  display: flex;
  align-items: center;
  gap: 8px;
}

.tool-item label {
  display: flex;
  align-items: center;
  gap: 6px;
  cursor: pointer;
}

.tool-item input:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.disabled-hint {
  color: var(--text-tertiary);
  font-size: 12px;
}

.enabled-hint {
  color: var(--text-secondary);
  font-size: 12px;
}

.error-section {
  margin-top: 20px;
  padding: 16px;
  background: #fee;
  border: 1px solid #fcc;
  border-radius: 8px;
}

.error-item {
  margin-bottom: 8px;
  color: #c33;
}

.result-section {
  margin-top: 20px;
  padding: 16px;
  background: var(--bg-secondary);
  border-radius: 8px;
}

.result-section pre {
  background: var(--bg-primary);
  padding: 12px;
  border-radius: 4px;
  font-family: monospace;
  font-size: 12px;
  overflow-x: auto;
}
</style>
