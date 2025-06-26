import type { ImageItem } from '@/components/ImageThumbnail.vue';

// 支持的图片格式
export const SUPPORTED_IMAGE_TYPES = [
  'image/jpeg',
  'image/jpg', 
  'image/png',
  'image/gif',
  'image/webp'
];

// 支持的文件扩展名
export const SUPPORTED_IMAGE_EXTENSIONS = [
  '.jpg',
  '.jpeg',
  '.png', 
  '.gif',
  '.webp'
];

// 最大文件大小 (10MB)
export const MAX_FILE_SIZE = 10 * 1024 * 1024;

/**
 * 验证文件是否为支持的图片格式
 */
export function validateImageFile(file: File): { valid: boolean; error?: string } {
  // 检查文件类型
  if (!SUPPORTED_IMAGE_TYPES.includes(file.type)) {
    return {
      valid: false,
      error: `不支持的文件格式。支持的格式：${SUPPORTED_IMAGE_EXTENSIONS.join(', ')}`
    };
  }

  // 检查文件大小
  if (file.size > MAX_FILE_SIZE) {
    return {
      valid: false,
      error: `文件大小超过限制。最大支持 ${Math.round(MAX_FILE_SIZE / 1024 / 1024)}MB`
    };
  }

  return { valid: true };
}

/**
 * 将文件转换为base64格式
 */
export function fileToBase64(file: File): Promise<string> {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    
    reader.onload = () => {
      const result = reader.result as string;
      // 移除data:image/xxx;base64,前缀，只保留base64字符串
      const base64 = result.split(',')[1];
      resolve(base64);
    };
    
    reader.onerror = () => {
      reject(new Error('文件读取失败'));
    };
    
    reader.readAsDataURL(file);
  });
}

/**
 * 将文件转换为ImageItem对象
 */
export async function fileToImageItem(file: File): Promise<ImageItem> {
  const validation = validateImageFile(file);
  if (!validation.valid) {
    throw new Error(validation.error);
  }

  const base64 = await fileToBase64(file);
  const dataUrl = `data:${file.type};base64,${base64}`;

  return {
    url: dataUrl,
    name: file.name,
    size: file.size,
    base64: base64,
    type: file.type
  };
}

/**
 * 处理多个文件
 */
export async function processImageFiles(files: FileList | File[]): Promise<{
  success: ImageItem[];
  errors: { file: string; error: string }[];
}> {
  const success: ImageItem[] = [];
  const errors: { file: string; error: string }[] = [];

  const fileArray = Array.from(files);

  for (const file of fileArray) {
    try {
      const imageItem = await fileToImageItem(file);
      success.push(imageItem);
    } catch (error) {
      errors.push({
        file: file.name,
        error: error instanceof Error ? error.message : '未知错误'
      });
    }
  }

  return { success, errors };
}

/**
 * 创建文件选择器
 */
export function createFileSelector(
  multiple: boolean = true,
  onSelect: (files: FileList) => void
): HTMLInputElement {
  const input = document.createElement('input');
  input.type = 'file';
  input.accept = SUPPORTED_IMAGE_TYPES.join(',');
  input.multiple = multiple;
  input.style.display = 'none';

  input.addEventListener('change', (event) => {
    const target = event.target as HTMLInputElement;
    if (target.files && target.files.length > 0) {
      onSelect(target.files);
    }
    // 清空input值，允许重复选择同一文件
    target.value = '';
  });

  return input;
}

/**
 * 处理拖拽事件
 */
export function handleDragOver(event: DragEvent) {
  event.preventDefault();
  event.stopPropagation();
}

export function handleDragEnter(event: DragEvent) {
  event.preventDefault();
  event.stopPropagation();
}

export function handleDragLeave(event: DragEvent) {
  event.preventDefault();
  event.stopPropagation();
}

export function handleDrop(
  event: DragEvent,
  onDrop: (files: File[]) => void
) {
  event.preventDefault();
  event.stopPropagation();

  const files = Array.from(event.dataTransfer?.files || []);
  const imageFiles = files.filter(file => 
    SUPPORTED_IMAGE_TYPES.includes(file.type)
  );

  if (imageFiles.length > 0) {
    onDrop(imageFiles);
  }
}
