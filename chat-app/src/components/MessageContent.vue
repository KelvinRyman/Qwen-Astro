<template>
  <div class="message-content">
    <!-- 多模态内容渲染 -->
    <div v-if="isMultiModal" class="multimodal-content">
      <div v-for="(item, index) in contentArray" :key="index" class="content-item">
        <!-- 文本内容 -->
        <div
          v-if="item.type === 'text'"
          class="markdown-content"
          :class="`markdown-content--${messageType}`"
          v-html="renderText(item.text)"
        ></div>

        <!-- 图片内容 -->
        <div v-else-if="item.type === 'image_url'" class="image-content">
          <img :src="item.image_url.url" :alt="'用户上传的图片'" class="message-image" />
        </div>
      </div>
    </div>

    <!-- 纯文本内容渲染 -->
    <div
      v-else-if="renderedContent"
      class="markdown-content"
      :class="`markdown-content--${messageType}`"
      v-html="renderedContent"
    ></div>

    <!-- 生成中的光标 -->
    <span v-if="isGenerating" class="generating-cursor"></span>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { smartRender } from '@/utils/markdown'
import type { MessageContent as MessageContentType, TextContent, ImageContent } from '@/api/chatApi'

interface Props {
  content: MessageContentType
  isGenerating?: boolean
  messageType?: 'user' | 'assistant'
}

const props = withDefaults(defineProps<Props>(), {
  isGenerating: false,
  messageType: 'assistant'
})

// 计算属性
const isMultiModal = computed(() => {
  return Array.isArray(props.content)
})

const contentArray = computed(() => {
  return Array.isArray(props.content) ? props.content : []
})

const displayContent = computed(() => {
  if (Array.isArray(props.content)) {
    // 多模态内容，提取文本部分用于渲染
    const textParts = props.content
      .filter((item): item is TextContent => item.type === 'text')
      .map(item => item.text)
    return textParts.join('\n')
  }
  return props.content || ''
})

// 渲染单个文本内容
const renderText = (text: string) => {
  try {
    return smartRender(text)
  } catch (error) {
    console.error('文本内容渲染失败:', error)
    return text.replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/\n/g, '<br>')
  }
}

// 计算属性：自动监听content变化并重新渲染（用于纯文本模式）
const renderedContent = computed(() => {
  if (!displayContent.value) return ''

  try {
    return smartRender(displayContent.value)
  } catch (error) {
    console.error('消息内容渲染失败:', error)
    // 渲染失败时显示原始文本
    return displayContent.value.replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/\n/g, '<br>')
  }
})
</script>

<style scoped>
.message-content {
  position: relative;
}

.multimodal-content {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.content-item {
  display: block;
}

.image-content {
  margin: 8px 0;
}

.message-image {
  max-width: 100%;
  max-height: 400px;
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  cursor: pointer;
  transition: transform 0.2s ease;
}

.message-image:hover {
  transform: scale(1.02);
}

/* 生成中的光标动画 */
.generating-cursor {
  display: inline-block;
  width: 2px;
  height: 1.2em;
  background-color: var(--text-primary);
  margin-left: 2px;
  animation: blink 1s infinite;
  vertical-align: text-bottom;
}

@keyframes blink {
  0%, 50% { opacity: 1; }
  51%, 100% { opacity: 0; }
}

/* 自定义Markdown样式 - 基础设置 */
.markdown-content {
  font-family: inherit;
  font-size: inherit;
  line-height: inherit;
  color: inherit;
  word-wrap: break-word;
  overflow-wrap: break-word;
}

/* ===== 标题样式 ===== */
.markdown-content h1,
.markdown-content h2,
.markdown-content h3,
.markdown-content h4,
.markdown-content h5,
.markdown-content h6 {
  margin-top: 1.5em;
  margin-bottom: 0.75em;
  font-weight: 600;
  line-height: 1.25;
  color: inherit;
}

.markdown-content h1:first-child,
.markdown-content h2:first-child,
.markdown-content h3:first-child,
.markdown-content h4:first-child,
.markdown-content h5:first-child,
.markdown-content h6:first-child {
  margin-top: 0;
}

.markdown-content h1 {
  font-size: 1.75em;
  border-bottom: 2px solid;
  padding-bottom: 0.3em;
}

.markdown-content h2 {
  font-size: 1.5em;
  border-bottom: 1px solid;
  padding-bottom: 0.25em;
}

.markdown-content h3 {
  font-size: 1.25em;
}

.markdown-content h4 {
  font-size: 1.1em;
}

.markdown-content h5 {
  font-size: 1em;
  font-weight: 600;
}

.markdown-content h6 {
  font-size: 0.9em;
  font-weight: 600;
  opacity: 0.8;
}

/* ===== 段落样式 ===== */
.markdown-content p {
  margin-top: 0;
  margin-bottom: 1em;
  line-height: 1.6;
}

.markdown-content p:last-child {
  margin-bottom: 0;
}

/* ===== 列表样式 ===== */
.markdown-content ul,
.markdown-content ol {
  margin-top: 0;
  margin-bottom: 1em;
  padding-left: 1.5em;
}

.markdown-content li {
  margin-bottom: 0.25em;
  line-height: 1.5;
}

.markdown-content li > p {
  margin-bottom: 0.5em;
}

.markdown-content li:last-child > p {
  margin-bottom: 0;
}

.markdown-content ul ul,
.markdown-content ol ol,
.markdown-content ul ol,
.markdown-content ol ul {
  margin-top: 0.25em;
  margin-bottom: 0.25em;
}

/* ===== 引用样式 ===== */
.markdown-content blockquote {
  margin: 1em 0;
  padding: 0.75em 1em;
  border-left: 4px solid;
  border-radius: 0 6px 6px 0;
  font-style: italic;
  position: relative;
}

.markdown-content blockquote > :first-child {
  margin-top: 0;
}

.markdown-content blockquote > :last-child {
  margin-bottom: 0;
}

/* ===== 链接样式 ===== */
.markdown-content a {
  text-decoration: none;
  border-bottom: 1px solid transparent;
  transition: all 0.2s ease;
}

.markdown-content a:hover {
  border-bottom-color: currentColor;
}

/* ===== 强调文本样式 ===== */
.markdown-content strong {
  font-weight: 600;
}

.markdown-content em {
  font-style: italic;
}

.markdown-content del {
  text-decoration: line-through;
  opacity: 0.7;
}

/* ===== 代码样式 ===== */
.markdown-content code {
  padding: 0.2em 0.4em;
  margin: 0;
  font-size: 0.9em;
  border-radius: 4px;
  font-family: 'SFMono-Regular', 'Monaco', 'Consolas', 'Liberation Mono', 'Courier New', monospace;
  font-weight: 400;
}

.markdown-content pre {
  margin: 1em 0;
  padding: 1em;
  overflow-x: auto;
  font-size: 0.875em;
  line-height: 1.5;
  border-radius: 8px;
  border: 1px solid;
  position: relative;
}

.markdown-content pre code {
  display: block;
  padding: 0;
  margin: 0;
  overflow: visible;
  line-height: inherit;
  word-wrap: normal;
  background-color: transparent;
  border: 0;
  border-radius: 0;
  font-size: inherit;
}

/* ===== 表格样式 ===== */
.markdown-content table {
  border-spacing: 0;
  border-collapse: collapse;
  margin: 1em 0;
  width: 100%;
  overflow-x: auto;
  display: table;
  border-radius: 6px;
  border: 1px solid;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
}

.markdown-content table th,
.markdown-content table td {
  padding: 0.5em 0.75em;
  border-right: 1px solid;
  text-align: left;
  vertical-align: top;
}

.markdown-content table th:last-child,
.markdown-content table td:last-child {
  border-right: none;
}

.markdown-content table th {
  font-weight: 600;
  border-bottom: 2px solid;
}

.markdown-content table tbody tr {
  border-bottom: 1px solid;
}

.markdown-content table tbody tr:last-child {
  border-bottom: none;
}

/* ===== 水平线样式 ===== */
.markdown-content hr {
  height: 2px;
  padding: 0;
  margin: 2em 0;
  border: 0;
  border-radius: 1px;
}

/* ===== 图片样式 ===== */
.markdown-content img {
  max-width: 100%;
  height: auto;
  border-radius: 6px;
  margin: 0.5em 0;
  display: block;
}

/* ===== 用户消息样式 (深色背景) ===== */
.markdown-content--user {
  /* 标题边框颜色 */
}

.markdown-content--user h1,
.markdown-content--user h2 {
  border-color: rgba(255, 255, 255, 0.2);
}

.markdown-content--user blockquote {
  border-left-color: rgba(255, 255, 255, 0.3);
  background-color: rgba(255, 255, 255, 0.05);
  color: rgba(255, 255, 255, 0.8);
}

.markdown-content--user a {
  color: #7dd3fc;
}

.markdown-content--user code {
  background-color: rgba(255, 255, 255, 0.15);
  color: #fcd34d;
  border: 1px solid rgba(255, 255, 255, 0.1);
}

.markdown-content--user pre {
  background-color: rgba(255, 255, 255, 0.05);
  border-color: rgba(255, 255, 255, 0.1);
}

.markdown-content--user table {
  border-color: rgba(255, 255, 255, 0.2);
}

.markdown-content--user table th,
.markdown-content--user table td {
  border-color: rgba(255, 255, 255, 0.1);
}

.markdown-content--user table th {
  background-color: rgba(255, 255, 255, 0.05);
  border-bottom-color: rgba(255, 255, 255, 0.2);
}

.markdown-content--user table tbody tr {
  border-color: rgba(255, 255, 255, 0.1);
}

.markdown-content--user hr {
  background-color: rgba(255, 255, 255, 0.2);
}

/* ===== 助手消息样式 (浅色背景) ===== */
.markdown-content--assistant {
  /* 默认样式，继承主题颜色 */
}

.markdown-content--assistant h1,
.markdown-content--assistant h2 {
  border-color: var(--border-color);
}

.markdown-content--assistant blockquote {
  border-left-color: var(--link-color);
  background-color: rgba(86, 149, 210, 0.1);
  color: var(--text-secondary);
}

.markdown-content--assistant a {
  color: var(--link-color);
}

.markdown-content--assistant code {
  background-color: rgba(86, 149, 210, 0.15);
  color: #f59e0b;
  border: 1px solid rgba(86, 149, 210, 0.2);
}

.markdown-content--assistant pre {
  background-color: var(--bg-mid);
  border-color: var(--border-color);
}

.markdown-content--assistant table {
  border-color: var(--border-color);
}

.markdown-content--assistant table th,
.markdown-content--assistant table td {
  border-color: var(--border-color);
}

.markdown-content--assistant table th {
  background-color: rgba(86, 149, 210, 0.1);
  border-bottom-color: var(--border-color);
}

.markdown-content--assistant table tbody tr {
  border-color: var(--border-color);
}

.markdown-content--assistant hr {
  background-color: var(--border-color);
}

/* ===== 响应式设计 ===== */
@media (max-width: 768px) {
  .markdown-content table {
    font-size: 0.875em;
    display: block;
    overflow-x: auto;
    white-space: nowrap;
  }

  .markdown-content pre {
    padding: 0.75em;
    font-size: 0.8em;
  }

  .markdown-content h1 {
    font-size: 1.5em;
  }

  .markdown-content h2 {
    font-size: 1.25em;
  }

  .markdown-content h3 {
    font-size: 1.1em;
  }

  .markdown-content blockquote {
    padding: 0.5em 0.75em;
    margin: 0.75em 0;
  }

  .markdown-content ul,
  .markdown-content ol {
    padding-left: 1.25em;
  }
}

/* ===== 小屏幕优化 ===== */
@media (max-width: 480px) {
  .markdown-content h1 {
    font-size: 1.375em;
  }

  .markdown-content h2 {
    font-size: 1.125em;
  }

  .markdown-content pre {
    padding: 0.5em;
    font-size: 0.75em;
  }

  .markdown-content table th,
  .markdown-content table td {
    padding: 0.375em 0.5em;
  }
}

/* ===== 打印样式 ===== */
@media print {
  .markdown-content {
    color: black !important;
  }

  .markdown-content a {
    color: black !important;
    text-decoration: underline !important;
  }

  .markdown-content pre,
  .markdown-content code {
    background-color: #f5f5f5 !important;
    color: black !important;
  }
}
</style>
