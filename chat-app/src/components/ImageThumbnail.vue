<template>
  <div class="image-thumbnail-container">
    <div v-for="(image, index) in images" :key="index" class="image-thumbnail">
      <img :src="image.url" :alt="image.name" class="thumbnail-image" />
      <button class="remove-button" @click="removeImage(index)" title="删除图片">
        <Icon name="close" />
      </button>
      <div class="image-info">
        <span class="image-name">{{ image.name }}</span>
        <span class="image-size">{{ formatFileSize(image.size) }}</span>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import Icon from '@/components/AppIcon.vue';

export interface ImageItem {
  url: string;      // base64 data URL for display
  name: string;     // original filename
  size: number;     // file size in bytes
  base64: string;   // pure base64 string (without data: prefix)
  type: string;     // MIME type
}

defineProps<{
  images: ImageItem[];
}>();

const emit = defineEmits<{
  remove: [index: number];
}>();

const removeImage = (index: number) => {
  emit('remove', index);
};

const formatFileSize = (bytes: number): string => {
  if (bytes === 0) return '0 Bytes';
  const k = 1024;
  const sizes = ['Bytes', 'KB', 'MB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
};
</script>

<style scoped>
.image-thumbnail-container {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-bottom: 8px;
  padding: 8px 0;
}

.image-thumbnail {
  position: relative;
  width: 120px;
  height: 120px;
  border-radius: 8px;
  overflow: hidden;
  border: 1px solid var(--border-color);
  background: var(--bg-primary);
  transition: all 0.2s ease;
}

.image-thumbnail:hover {
  border-color: var(--accent-color);
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.thumbnail-image {
  width: 100%;
  height: 80px;
  object-fit: cover;
  background: var(--bg-secondary);
}

.remove-button {
  position: absolute;
  top: 4px;
  right: 4px;
  width: 20px;
  height: 20px;
  border-radius: 50%;
  background: rgba(0, 0, 0, 0.7);
  border: none;
  color: white;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  opacity: 0;
  transition: opacity 0.2s ease;
  font-size: 12px;
}

.image-thumbnail:hover .remove-button {
  opacity: 1;
}

.remove-button:hover {
  background: rgba(255, 0, 0, 0.8);
}

.image-info {
  padding: 4px 6px;
  font-size: 10px;
  color: var(--text-secondary);
  display: flex;
  flex-direction: column;
  height: 40px;
  justify-content: center;
}

.image-name {
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  font-weight: 500;
  margin-bottom: 2px;
}

.image-size {
  color: var(--text-tertiary);
  font-size: 9px;
}
</style>
