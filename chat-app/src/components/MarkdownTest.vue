<template>
  <div class="markdown-test">
    <h2>Markdown渲染测试</h2>
    
    <div class="test-section">
      <h3>测试消息</h3>
      <div class="message-wrapper">
        <div class="assistant-message-wrapper">
          <div class="assistant-message">
            <MessageContent :content="testMarkdown" message-type="assistant" />
          </div>
        </div>
      </div>
    </div>
    
    <div class="test-section">
      <h3>纯文本测试</h3>
      <div class="message-wrapper">
        <div class="user-message-wrapper">
          <div class="user-message">
            <MessageContent :content="testPlainText" message-type="user" />
          </div>
        </div>
      </div>
    </div>
    
    <div class="test-section">
      <h3>生成中测试</h3>
      <div class="message-wrapper">
        <div class="assistant-message-wrapper">
          <div class="assistant-message">
            <MessageContent :content="testGenerating" :is-generating="true" message-type="assistant" />
          </div>
        </div>
      </div>
    </div>

    <div class="test-section">
      <h3>样式对比测试</h3>
      <div class="message-wrapper">
        <div class="user-message-wrapper">
          <div class="user-message">
            <MessageContent :content="testStyleComparison" message-type="user" />
          </div>
        </div>
      </div>
      <div class="message-wrapper">
        <div class="assistant-message-wrapper">
          <div class="assistant-message">
            <MessageContent :content="testStyleComparison" message-type="assistant" />
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import MessageContent from './MessageContent.vue'

const testMarkdown = `# 这是一个标题

这是一个包含**粗体**和*斜体*文本的段落。还有~~删除线~~文本。

## 二级标题

### 列表示例

- 无序列表项1
- 无序列表项2
  - 嵌套项目
  - 另一个嵌套项目

1. 有序列表项1
2. 有序列表项2
3. 有序列表项3

### 代码示例

这是一个\`行内代码\`示例。

\`\`\`javascript
function hello() {
  console.log("Hello, World!");
  return "这是一个代码块示例";
}
\`\`\`

### 引用

> 这是一个引用块
> 可以包含多行内容
>
> 甚至可以包含**格式化**文本

### 链接和图片

这是一个[内部链接](#section)和一个[外部链接](https://example.com)。

### 表格

| 功能 | 状态 | 描述 |
|------|------|------|
| Markdown渲染 | ✅ | 支持基本语法 |
| 代码高亮 | ❌ | 暂不支持 |
| 数学公式 | ❌ | 暂不支持 |

---

这是一条水平线上方的内容。

### 混合内容测试

这里有一些**重要**的信息：

1. 支持\`行内代码\`
2. 支持[链接](https://github.com)
3. 支持*强调*文本

> **注意**：这是一个包含格式化文本的引用块。`

const testPlainText = `这是一个纯文本消息
包含多行内容
但没有Markdown语法`

const testGenerating = `这是一个正在生成的消息...`

const testStyleComparison = `## 样式对比测试

这是一个用来测试**用户消息**和**助手消息**样式差异的示例。

### 代码示例
\`\`\`javascript
function greet(name) {
  return \`Hello, \${name}!\`;
}
\`\`\`

### 引用块
> 这是一个引用块，用来测试不同消息类型的样式差异。
> 注意观察背景色和边框颜色的变化。

### 表格
| 特性 | 用户消息 | 助手消息 |
|------|----------|----------|
| 背景色 | 深色 | 浅色 |
| 代码块 | 黄色高亮 | 橙色高亮 |
| 链接色 | 浅蓝色 | 深蓝色 |

### 链接测试
这是一个[测试链接](https://example.com)，观察不同消息类型的链接颜色。`
</script>

<style scoped>
.markdown-test {
  padding: 20px;
  max-width: 800px;
  margin: 0 auto;
}

.test-section {
  margin-bottom: 40px;
  border: 1px solid var(--border-color);
  border-radius: 8px;
  padding: 20px;
}

.test-section h3 {
  margin-top: 0;
  color: var(--text-primary);
}

.message-wrapper {
  margin-bottom: 24px;
  display: flex;
  flex-direction: column;
  max-width: 800px;
  margin-left: auto;
  margin-right: auto;
  width: 100%;
}

.user-message-wrapper {
  align-self: flex-end;
  max-width: 80%;
  position: relative;
}

.user-message {
  align-self: flex-end;
  background-color: var(--bg-input);
  color: var(--text-primary);
  padding: 14px;
  border-radius: var(--border-radius-large);
  word-break: break-word;
  line-height: 1.5;
  font-size: 16px;
}

.assistant-message-wrapper {
  align-self: flex-start;
  max-width: 100%;
  position: relative;
}

.assistant-message {
  color: var(--text-primary);
  line-height: 1.5;
  font-size: 16px;
  margin-bottom: 8px;
}
</style>
