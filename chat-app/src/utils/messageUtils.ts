import type { MessageContent, TextContent, ImageContent } from '@/api/chatApi';

/**
 * 将后端存储的消息内容转换为前端期望的格式
 */
export function convertBackendMessageContent(backendContent: any): MessageContent {
  // 如果是字符串，直接返回
  if (typeof backendContent === 'string') {
    return backendContent;
  }
  
  // 如果是后端的多模态格式
  if (backendContent && typeof backendContent === 'object' && backendContent.type === 'multimodal') {
    const content: (TextContent | ImageContent)[] = [];
    
    // 添加文本内容
    if (backendContent.text) {
      content.push({
        type: 'text',
        text: backendContent.text
      });
    }
    
    // 添加图片内容
    if (backendContent.images && Array.isArray(backendContent.images)) {
      backendContent.images.forEach((imageBase64: string) => {
        content.push({
          type: 'image_url',
          image_url: {
            url: `data:image/jpeg;base64,${imageBase64}`
          }
        });
      });
    }
    
    return content;
  }
  
  // 如果已经是前端格式的数组，直接返回
  if (Array.isArray(backendContent)) {
    return backendContent;
  }
  
  // 其他情况，转换为字符串
  return String(backendContent);
}

/**
 * 从消息内容中提取纯文本（用于复制、搜索等）
 */
export function extractTextFromMessageContent(content: MessageContent): string {
  if (typeof content === 'string') {
    return content;
  }
  
  if (Array.isArray(content)) {
    return content
      .filter(item => item.type === 'text')
      .map(item => (item as TextContent).text)
      .join('\n');
  }
  
  return String(content);
}

/**
 * 检查消息内容是否包含图片
 */
export function hasImages(content: MessageContent): boolean {
  if (Array.isArray(content)) {
    return content.some(item => item.type === 'image_url');
  }
  return false;
}

/**
 * 从消息内容中提取图片URL列表
 */
export function extractImageUrls(content: MessageContent): string[] {
  if (Array.isArray(content)) {
    return content
      .filter(item => item.type === 'image_url')
      .map(item => (item as ImageContent).image_url.url);
  }
  return [];
}

/**
 * 生成消息摘要（用于对话列表显示）
 */
export function generateMessageSummary(content: MessageContent, maxLength: number = 50): string {
  const text = extractTextFromMessageContent(content);
  const hasImg = hasImages(content);
  
  let summary = text.length > maxLength ? text.substring(0, maxLength) + '...' : text;
  
  if (hasImg) {
    summary += ' [包含图片]';
  }
  
  return summary || '空消息';
}
