import { defineStore } from 'pinia'

// 定义数据结构类型
export interface KnowledgeGroup {
  id: string
  name: string
  icon: string
  embedding_model: string
  rerank_model?: string
}

export interface KnowledgeFile {
  id: string
  name: string
  date: string
  size: string
  status: 'completed' | 'processing' | 'failed'
  type: 'pdf' | 'text' // For icon display
}

export interface KnowledgeUrl {
  id: string
  url: string
  date: string
  status: 'completed' | 'processing' | 'failed'
}

interface KnowledgeBaseState {
  groups: KnowledgeGroup[]
  activeGroupId: string | null
  contentByGroupId: Record<string, { files: KnowledgeFile[]; urls: KnowledgeUrl[] }>
  isLoadingGroups: boolean
  isLoadingContent: boolean
}

// 模拟 API 延迟
const apiDelay = (ms: number) => new Promise((resolve) => setTimeout(resolve, ms))

export const useKnowledgeBaseStore = defineStore('knowledgeBase', {
  state: (): KnowledgeBaseState => ({
    groups: [],
    activeGroupId: null,
    contentByGroupId: {},
    isLoadingGroups: false,
    isLoadingContent: false,
  }),

  getters: {
    // 获取当前激活的分组对象
    activeGroup: (state): KnowledgeGroup | undefined => {
      return state.groups.find((g) => g.id === state.activeGroupId)
    },
    // 获取当前激活分组的内容
    activeContent: (state) => {
      if (!state.activeGroupId) return { files: [], urls: [] }
      return state.contentByGroupId[state.activeGroupId] || { files: [], urls: [] }
    },
    // 计算文件数量
    fileCount: (state): number => {
      if (!state.activeGroupId) return 0
      return state.contentByGroupId[state.activeGroupId]?.files.length || 0
    },
    // 计算网址数量
    urlCount: (state): number => {
      if (!state.activeGroupId) return 0
      return state.contentByGroupId[state.activeGroupId]?.urls.length || 0
    },
  },

  actions: {
    // 模拟获取分组列表
    async fetchGroups() {
      this.isLoadingGroups = true
      await apiDelay(500)
      this.groups = [
        { id: 'group-1', name: '论文', icon: 'document', embedding_model: 'BAAI/bge-m3', rerank_model: 'BAAI/bge-reranker-v2-m3' },
        { id: 'group-2', name: '网络安全', icon: 'security', embedding_model: 'BAAI/bge-m3', rerank_model: 'BAAI/bge-reranker-v2-m3' },
      ]
      // 默认选中第一个
      if (this.groups.length > 0 && !this.activeGroupId) {
        this.selectGroup(this.groups[0].id)
      }
      this.isLoadingGroups = false
    },

    // 选中一个分组
    async selectGroup(groupId: string) {
      this.activeGroupId = groupId
      // 如果该分组的内容尚未加载，则去加载
      if (!this.contentByGroupId[groupId]) {
        await this.fetchContentForGroup(groupId)
      }
    },

    // 模拟根据 ID 获取分组内容
    async fetchContentForGroup(groupId: string) {
      this.isLoadingContent = true
      await apiDelay(800)

      // 模拟不同分组的不同数据
      let content: { files: KnowledgeFile[]; urls: KnowledgeUrl[] } = { files: [], urls: [] }
      if (groupId === 'group-1') {
        content = {
          files: [
            {
              id: 'file-1',
              name: 'PCZero.pdf',
              date: '2025-04-27 23:24',
              size: '611 KB',
              status: 'completed',
              type: 'pdf',
            },
            {
              id: 'file-2',
              name: '1702.08892v3.pdf',
              date: '2025-04-27 23:23',
              size: '1019 KB',
              status: 'completed',
              type: 'pdf',
            },
          ],
          urls: [
            {
              id: 'url-3',
              url: 'https://owasp.org/www-project-top-ten/',
              date: '2025-04-27 23:22',
              status: 'completed',
            },
            {
              id: 'url-4',
              url: 'https://www.example.com',
              date: '2025-04-27 23:21',
              status: 'completed',
            }
          ],
        }
      } else if (groupId === 'group-2') {
        content = {
          files: [],
          urls: [
            {
              id: 'url-3',
              url: 'https://owasp.org/www-project-top-ten/',
              date: '2025-04-27 23:22',
              status: 'completed',
            },
          ],
        }
      }

      this.contentByGroupId[groupId] = content
      this.isLoadingContent = false
    },

    // 模拟删除文件
    async deleteFile(fileId: string) {
      console.log(`[API MOCK] Deleting file with ID: ${fileId}`)
      if (!this.activeGroupId) return

      const groupContent = this.contentByGroupId[this.activeGroupId]
      if (groupContent) {
        groupContent.files = groupContent.files.filter((f) => f.id !== fileId)
      }
    },

    async deleteUrl(urlId: string) {
      console.log(`[API MOCK] Deleting URL with ID: ${urlId}`)
      if (!this.activeGroupId) return

      const groupContent = this.contentByGroupId[this.activeGroupId]
      if (groupContent) {
        groupContent.urls = groupContent.urls.filter((u) => u.id !== urlId)
      }
    },

    // 模拟刷新状态
    async refreshFileStatus(fileId: string) {
      console.log(`[API MOCK] Refreshing status for file with ID: ${fileId}`)
      // 在真实应用中，这里会调用 API，然后更新状态
    },

    async refreshUrlStatus(urlId: string) {
      console.log(`[API MOCK] Refreshing status for URL with ID: ${urlId}`)
      // 在真实应用中，这里会调用 API，然后更新状态
    },
  },
})
