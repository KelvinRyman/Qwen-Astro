<template>
  <div
    class="citation-card"
    :data-type="source.source_type"
    @click="handleClick"
  >
    <div class="citation-icon">
      <Icon :name="iconName" />
    </div>
    <div class="citation-content">
      <div class="citation-title">{{ displayTitle }}</div>
      <div class="citation-snippet">{{ source.text_snippet }}</div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import type { PropType } from 'vue'
import type { SourceNode } from '@/api/chatApi'
import Icon from '@/components/AppIcon.vue'

const props = defineProps({
  source: { 
    type: Object as PropType<SourceNode>, 
    required: true 
  }
})

// 计算图标名称
const iconName = computed(() => {
  return props.source.source_type === 'webpage' ? 'quote_webpage' : 'quote_file'
})

// 计算显示标题
const displayTitle = computed(() => {
  if (props.source.source_type === 'webpage') {
    // 对于网页，显示URL或从URL提取的标题
    if (props.source.source_url) {
      try {
        const url = new URL(props.source.source_url)
        return url.hostname
      } catch {
        return props.source.source_url
      }
    }
    return props.source.file_name
  } else {
    // 对于文件，显示文件名
    return props.source.file_name
  }
})

// 处理点击事件
const handleClick = () => {
  if (props.source.source_type === 'webpage' && props.source.source_url) {
    // 网页类型，打开链接
    window.open(props.source.source_url, '_blank', 'noopener,noreferrer')
  } else if (props.source.source_type === 'file') {
    // 文件类型，下载文件
    downloadFile()
  }
}

// 下载文件
const downloadFile = async () => {
  try {
    const downloadUrl = `http://127.0.0.1:5000/api/groups/${props.source.group_id}/files/${props.source.id}/download`

    // 创建一个临时的a标签来触发下载
    const link = document.createElement('a')
    link.href = downloadUrl
    link.download = props.source.file_name
    link.style.display = 'none'

    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
  } catch (error) {
    console.error('下载文件失败:', error)
    // 可以添加用户提示
  }
}
</script>

<style scoped>
.citation-card {
  display: flex;
  align-items: flex-start;
  gap: 12px;
  padding: 12px;
  background-color: var(--bg-tertiary);
  border: 1px solid var(--border-color);
  border-radius: var(--border-radius-medium);
  cursor: pointer;
  transition: all 0.2s ease;
  min-width: 200px;
  max-width: 300px;
}

.citation-card:hover {
  background-color: var(--bg-input);
  border-color: var(--interactive-label-accent-default);
}

.citation-icon {
  flex-shrink: 0;
  width: 48px;
  height: 48px;
  font-size: 48px;
  color: var(--text-secondary);
  /* display: flex; */
  align-items: center;
  justify-content: center;
}

.citation-content {
  flex: 1;
  min-width: 0; /* 允许文本截断 */
}

.citation-title {
  font-size: 14px;
  font-weight: 500;
  color: var(--text-primary);
  margin-bottom: 4px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.citation-snippet {
  font-size: 12px;
  color: var(--text-secondary);
  line-height: 1.4;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  line-clamp: 2; /* 标准属性 */
  -webkit-box-orient: vertical;
  overflow: hidden;
  text-overflow: ellipsis;
}

/* 不同类型的特殊样式 */
.citation-card[data-type="webpage"] {
  cursor: pointer;
}

.citation-card[data-type="file"] {
  cursor: pointer;
}

.citation-card[data-type="file"]:hover .citation-icon {
  color: var(--interactive-label-accent-default);
}

.citation-card[data-type="webpage"]:hover .citation-icon {
  color: var(--interactive-label-accent-default);
}
</style>
