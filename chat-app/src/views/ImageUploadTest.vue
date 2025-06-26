<template>
  <div class="image-upload-test">
    <h2>图片上传功能测试</h2>
    
    <!-- 上传区域 -->
    <div 
      class="upload-area"
      :class="{ 'drag-over': isDragOver }"
      @dragover="onDragOver"
      @dragenter="onDragEnter"
      @dragleave="onDragLeave"
      @drop="onDrop"
    >
      <div class="upload-content">
        <Icon name="plus" class="upload-icon" />
        <p>点击选择图片或拖拽图片到此处</p>
        <p class="upload-hint">支持 JPG, PNG, GIF, WebP 格式，最大 10MB</p>
        <button class="upload-button" @click="openFileSelector" :disabled="isUploading">
          {{ isUploading ? '上传中...' : '选择图片' }}
        </button>
      </div>
    </div>

    <!-- 图片预览 -->
    <div v-if="hasImages" class="preview-section">
      <h3>已选择的图片 ({{ imageCount }}/10)</h3>
      <ImageThumbnail :images="selectedImages" @remove="removeImage" />
      
      <div class="actions">
        <button @click="clearImages" class="clear-button">清空所有</button>
        <button @click="showBase64Data" class="show-data-button">显示Base64数据</button>
      </div>
    </div>

    <!-- 错误信息 -->
    <div v-if="errors.length > 0" class="error-section">
      <h3>错误信息</h3>
      <ul>
        <li v-for="(error, index) in errors" :key="index" class="error-item">
          <strong>{{ error.file || '系统' }}:</strong> {{ error.error }}
        </li>
      </ul>
      <button @click="clearErrors" class="clear-errors-button">清除错误</button>
    </div>

    <!-- Base64数据显示 -->
    <div v-if="showData && hasImages" class="data-section">
      <h3>Base64数据</h3>
      <div class="data-content">
        <pre>{{ JSON.stringify(getImageBase64List(), null, 2) }}</pre>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue';
import Icon from '@/components/AppIcon.vue';
import ImageThumbnail from '@/components/ImageThumbnail.vue';
import { useImageUpload } from '@/composables/useImageUpload';

// 错误处理
const errors = ref<{ file: string; error: string }[]>([]);
const showData = ref(false);

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
  maxImages: 10,
  onError: (errorList) => {
    errors.value.push(...errorList);
  },
  onSuccess: (images) => {
    console.log('成功上传图片:', images);
  }
});

const clearErrors = () => {
  errors.value = [];
};

const showBase64Data = () => {
  showData.value = !showData.value;
};
</script>

<style scoped>
.image-upload-test {
  max-width: 800px;
  margin: 0 auto;
  padding: 20px;
}

.upload-area {
  border: 2px dashed var(--border-color);
  border-radius: 12px;
  padding: 40px 20px;
  text-align: center;
  background: var(--bg-primary);
  transition: all 0.3s ease;
  cursor: pointer;
}

.upload-area:hover,
.upload-area.drag-over {
  border-color: var(--accent-color);
  background: var(--bg-secondary);
}

.upload-content {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 12px;
}

.upload-icon {
  font-size: 48px;
  color: var(--text-secondary);
}

.upload-hint {
  font-size: 14px;
  color: var(--text-tertiary);
  margin: 0;
}

.upload-button {
  padding: 8px 16px;
  background: var(--accent-color);
  color: white;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  font-size: 14px;
}

.upload-button:hover {
  background: var(--accent-color-hover);
}

.upload-button:disabled {
  background: var(--text-tertiary);
  cursor: not-allowed;
}

.preview-section {
  margin-top: 24px;
}

.actions {
  display: flex;
  gap: 12px;
  margin-top: 16px;
}

.clear-button,
.show-data-button {
  padding: 8px 16px;
  border: 1px solid var(--border-color);
  background: var(--bg-primary);
  color: var(--text-primary);
  border-radius: 6px;
  cursor: pointer;
  font-size: 14px;
}

.clear-button:hover,
.show-data-button:hover {
  background: var(--bg-secondary);
}

.error-section {
  margin-top: 24px;
  padding: 16px;
  background: #fee;
  border: 1px solid #fcc;
  border-radius: 8px;
}

.error-item {
  margin-bottom: 8px;
  color: #c33;
}

.clear-errors-button {
  padding: 6px 12px;
  background: #c33;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-size: 12px;
  margin-top: 8px;
}

.data-section {
  margin-top: 24px;
  padding: 16px;
  background: var(--bg-secondary);
  border-radius: 8px;
}

.data-content {
  max-height: 300px;
  overflow-y: auto;
  background: var(--bg-primary);
  padding: 12px;
  border-radius: 4px;
  font-family: monospace;
  font-size: 12px;
}
</style>
