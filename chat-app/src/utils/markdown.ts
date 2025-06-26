/**
 * Markdown渲染工具
 * 
 * 提供安全的Markdown到HTML转换功能，集成主题样式
 */

import MarkdownIt from 'markdown-it'

// 创建markdown-it实例
const md = new MarkdownIt({
  // 启用HTML标签（但会被下面的规则限制）
  html: true,
  // 自动转换URL为链接
  linkify: true,
  // 启用一些语言中性的替换和引号美化
  typographer: true,
  // 换行符转换为<br>
  breaks: false,
})

// 安全的HTML标签白名单
const ALLOWED_TAGS = new Set([
  'p', 'br', 'strong', 'em', 'u', 's', 'del', 'ins',
  'h1', 'h2', 'h3', 'h4', 'h5', 'h6',
  'ul', 'ol', 'li',
  'blockquote',
  'a',
  'code', 'pre',
  'table', 'thead', 'tbody', 'tr', 'th', 'td',
  'hr',
  'img'
])

// 安全的HTML属性白名单
const ALLOWED_ATTRS: Record<string, string[]> = {
  'a': ['href', 'title', 'target', 'rel'],
  'img': ['src', 'alt', 'title', 'width', 'height'],
  'th': ['align'],
  'td': ['align'],
}

/**
 * 自定义链接渲染规则
 * 为外部链接添加安全属性
 */
const defaultLinkOpenRenderer = md.renderer.rules.link_open || function(tokens, idx, options, env, self) {
  return self.renderToken(tokens, idx, options)
}

md.renderer.rules.link_open = function (tokens, idx, options, env, self) {
  const token = tokens[idx]
  const href = token.attrGet('href')
  
  if (href) {
    // 检查是否为外部链接
    const isExternal = /^https?:\/\//.test(href) || href.startsWith('//')
    
    if (isExternal) {
      // 为外部链接添加安全属性
      token.attrSet('target', '_blank')
      token.attrSet('rel', 'noopener noreferrer')
    }
  }
  
  return defaultLinkOpenRenderer(tokens, idx, options, env, self)
}

/**
 * 简单的HTML标签和属性过滤器
 * 移除不在白名单中的标签和属性
 */
function sanitizeHtml(html: string): string {
  // 这是一个简单的实现，生产环境建议使用专门的HTML sanitizer库
  return html.replace(/<(\/?)([\w-]+)([^>]*)>/g, (match, slash, tagName, attrs) => {
    const tag = tagName.toLowerCase()
    
    // 检查标签是否在白名单中
    if (!ALLOWED_TAGS.has(tag)) {
      return ''
    }
    
    // 处理属性
    let cleanAttrs = ''
    if (attrs && ALLOWED_ATTRS[tag]) {
      const allowedAttrs = ALLOWED_ATTRS[tag]
      const attrRegex = /(\w+)=["']([^"']*)["']/g
      let attrMatch
      
      while ((attrMatch = attrRegex.exec(attrs)) !== null) {
        const [, attrName, attrValue] = attrMatch
        if (allowedAttrs.includes(attrName)) {
          // 简单的属性值清理
          const cleanValue = attrValue.replace(/[<>"']/g, '')
          cleanAttrs += ` ${attrName}="${cleanValue}"`
        }
      }
    }
    
    return `<${slash}${tag}${cleanAttrs}>`
  })
}

/**
 * 检测文本是否包含Markdown语法
 */
export function hasMarkdownSyntax(text: string): boolean {
  // 检测常见的Markdown语法模式
  const markdownPatterns = [
    /^#{1,6}\s+/m,           // 标题
    /\*\*.*?\*\*/,           // 粗体
    /\*[^*\s].*?[^*\s]\*/,   // 斜体（避免误判单个*）
    /__.*?__/,               // 粗体（下划线）
    /_[^_\s].*?[^_\s]_/,     // 斜体（下划线，避免误判单个_）
    /\[.*?\]\(.*?\)/,        // 链接
    /!\[.*?\]\(.*?\)/,       // 图片
    /^[-*+]\s+/m,            // 无序列表
    /^\d+\.\s+/m,            // 有序列表
    /^>\s+/m,                // 引用
    /`[^`]+`/,               // 行内代码
    /```[\s\S]*?```/,        // 代码块
    /^\|.*\|$/m,             // 表格
    /^---+$/m,               // 水平线
    /~~.*?~~/,               // 删除线
  ]

  return markdownPatterns.some(pattern => pattern.test(text))
}

/**
 * 将Markdown文本转换为安全的HTML
 */
export function renderMarkdown(text: string): string {
  try {
    // 使用markdown-it渲染
    const html = md.render(text)
    
    // 进行HTML安全过滤
    const safeHtml = sanitizeHtml(html)
    
    return safeHtml
  } catch (error) {
    console.error('Markdown渲染失败:', error)
    // 渲染失败时返回原始文本的HTML转义版本
    return escapeHtml(text)
  }
}

/**
 * HTML转义函数
 */
function escapeHtml(text: string): string {
  const div = document.createElement('div')
  div.textContent = text
  return div.innerHTML
}

/**
 * 为纯文本添加基本的换行处理
 */
export function renderPlainText(text: string): string {
  return escapeHtml(text).replace(/\n/g, '<br>')
}

/**
 * 智能渲染函数
 * 自动检测是否包含Markdown语法并选择合适的渲染方式
 */
export function smartRender(text: string): string {
  if (!text) return ''

  // 限制文本长度，防止性能问题
  const MAX_TEXT_LENGTH = 50000
  if (text.length > MAX_TEXT_LENGTH) {
    console.warn('文本过长，截断处理')
    text = text.substring(0, MAX_TEXT_LENGTH) + '\n\n...(内容已截断)'
  }

  // 检测是否包含Markdown语法
  if (hasMarkdownSyntax(text)) {
    return renderMarkdown(text)
  } else {
    return renderPlainText(text)
  }
}
