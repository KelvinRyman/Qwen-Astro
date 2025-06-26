import { ref, computed } from 'vue';
import type { Ref } from 'vue';
import type { ImageItem } from '@/components/ImageThumbnail.vue';
import {
  processImageFiles,
  createFileSelector,
  handleDragOver,
  handleDragEnter,
  handleDragLeave,
  handleDrop
} from '@/utils/imageUtils';

export interface UseImageUploadOptions {
  maxImages?: number;
  onError?: (errors: { file: string; error: string }[]) => void;
  onSuccess?: (images: ImageItem[]) => void;
}

export function useImageUpload(options: UseImageUploadOptions = {}) {
  const { maxImages = 10, onError, onSuccess } = options;
  
  // 响应式状态
  const selectedImages: Ref<ImageItem[]> = ref([]);
  const isUploading = ref(false);
  const isDragOver = ref(false);

  // 计算属性
  const hasImages = computed(() => selectedImages.value.length > 0);
  const canAddMore = computed(() => selectedImages.value.length < maxImages);
  const imageCount = computed(() => selectedImages.value.length);

  // 文件选择器
  let fileSelector: HTMLInputElement | null = null;

  /**
   * 初始化文件选择器
   */
  const initFileSelector = () => {
    if (!fileSelector) {
      fileSelector = createFileSelector(true, handleFileSelect);
      document.body.appendChild(fileSelector);
    }
  };

  /**
   * 处理文件选择
   */
  const handleFileSelect = async (files: FileList) => {
    if (!canAddMore.value) {
      onError?.([{ file: '', error: `最多只能选择 ${maxImages} 张图片` }]);
      return;
    }

    isUploading.value = true;

    try {
      const { success, errors } = await processImageFiles(files);
      
      // 检查是否超出限制
      const availableSlots = maxImages - selectedImages.value.length;
      const imagesToAdd = success.slice(0, availableSlots);
      
      if (success.length > availableSlots) {
        errors.push({
          file: '',
          error: `已达到最大图片数量限制 (${maxImages}张)，部分图片未添加`
        });
      }

      // 添加成功的图片
      selectedImages.value.push(...imagesToAdd);

      // 处理错误
      if (errors.length > 0) {
        onError?.(errors);
      }

      // 成功回调
      if (imagesToAdd.length > 0) {
        onSuccess?.(imagesToAdd);
      }

    } catch (error) {
      onError?.([{ 
        file: '', 
        error: error instanceof Error ? error.message : '处理图片时发生未知错误' 
      }]);
    } finally {
      isUploading.value = false;
    }
  };

  /**
   * 打开文件选择对话框
   */
  const openFileSelector = () => {
    if (!canAddMore.value) {
      onError?.([{ file: '', error: `最多只能选择 ${maxImages} 张图片` }]);
      return;
    }

    initFileSelector();
    fileSelector?.click();
  };

  /**
   * 移除指定索引的图片
   */
  const removeImage = (index: number) => {
    if (index >= 0 && index < selectedImages.value.length) {
      selectedImages.value.splice(index, 1);
    }
  };

  /**
   * 清空所有图片
   */
  const clearImages = () => {
    selectedImages.value = [];
  };

  /**
   * 获取所有图片的base64数据
   */
  const getImageBase64List = (): string[] => {
    return selectedImages.value.map(img => img.base64);
  };

  /**
   * 拖拽相关事件处理
   */
  const onDragOver = (event: DragEvent) => {
    handleDragOver(event);
    isDragOver.value = true;
  };

  const onDragEnter = (event: DragEvent) => {
    handleDragEnter(event);
    isDragOver.value = true;
  };

  const onDragLeave = (event: DragEvent) => {
    handleDragLeave(event);
    isDragOver.value = false;
  };

  const onDrop = (event: DragEvent) => {
    isDragOver.value = false;
    
    if (!canAddMore.value) {
      onError?.([{ file: '', error: `最多只能选择 ${maxImages} 张图片` }]);
      return;
    }

    handleDrop(event, async (files: File[]) => {
      isUploading.value = true;

      try {
        const { success, errors } = await processImageFiles(files);
        
        // 检查是否超出限制
        const availableSlots = maxImages - selectedImages.value.length;
        const imagesToAdd = success.slice(0, availableSlots);
        
        if (success.length > availableSlots) {
          errors.push({
            file: '',
            error: `已达到最大图片数量限制 (${maxImages}张)，部分图片未添加`
          });
        }

        // 添加成功的图片
        selectedImages.value.push(...imagesToAdd);

        // 处理错误
        if (errors.length > 0) {
          onError?.(errors);
        }

        // 成功回调
        if (imagesToAdd.length > 0) {
          onSuccess?.(imagesToAdd);
        }

      } catch (error) {
        onError?.([{ 
          file: '', 
          error: error instanceof Error ? error.message : '处理图片时发生未知错误' 
        }]);
      } finally {
        isUploading.value = false;
      }
    });
  };

  /**
   * 清理资源
   */
  const cleanup = () => {
    if (fileSelector && document.body.contains(fileSelector)) {
      document.body.removeChild(fileSelector);
      fileSelector = null;
    }
  };

  return {
    // 状态
    selectedImages,
    isUploading,
    isDragOver,
    
    // 计算属性
    hasImages,
    canAddMore,
    imageCount,
    
    // 方法
    openFileSelector,
    removeImage,
    clearImages,
    getImageBase64List,
    
    // 拖拽事件
    onDragOver,
    onDragEnter,
    onDragLeave,
    onDrop,
    
    // 清理
    cleanup
  };
}
