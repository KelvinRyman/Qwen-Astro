import { defineStore } from 'pinia'
import { knowledgeBaseApi } from '../api/knowledgeBaseApi'
import { PollingManager } from '../utils/pollingManager'
import { ref } from 'vue'

// 定义数据结构类型
export interface KnowledgeGroup {
  id: string
  name: string
  description?: string
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

// 创建一个全局的轮询管理器实例
let pollingManager: PollingManager | null = null;

export const useKnowledgeBaseStore = defineStore('knowledgeBase', {
  state: () => ({
    groups: [] as KnowledgeGroup[],
    activeGroupId: null as string | null,
    contentByGroupId: {} as Record<string, { files: KnowledgeFile[]; urls: KnowledgeUrl[] }>,
    isLoadingGroups: false,
    isLoadingContent: false,
    isCreatingGroup: false,
    isUploadingFile: false,
    isAddingUrl: false,
    error: null as string | null,
    // 轮询相关状态
    pollingEnabled: true,  // 默认启用轮询
    pollingInterval: 5000  // 默认5秒轮询一次
  }),

  getters: {
    // 获取当前激活的分组对象
    activeGroup: (state) => {
      return state.groups.find((g) => g.id === state.activeGroupId)
    },
    // 获取当前激活分组的内容
    activeContent: (state) => {
      if (!state.activeGroupId) return { files: [], urls: [] }
      return state.contentByGroupId[state.activeGroupId] || { files: [], urls: [] }
    },
    // 计算文件数量
    fileCount: (state) => {
      if (!state.activeGroupId) return 0
      return state.contentByGroupId[state.activeGroupId]?.files.length || 0
    },
    // 计算网址数量
    urlCount: (state) => {
      if (!state.activeGroupId) return 0
      return state.contentByGroupId[state.activeGroupId]?.urls.length || 0
    },
    // 获取处理中的文件
    processingFiles: (state) => {
      if (!state.activeGroupId) return [] as KnowledgeFile[]
      const content = state.contentByGroupId[state.activeGroupId]
      if (!content) return [] as KnowledgeFile[]
      return content.files.filter(file => file.status === 'processing')
    },
    // 获取处理中的网页
    processingWebpages: (state) => {
      if (!state.activeGroupId) return [] as KnowledgeUrl[]
      const content = state.contentByGroupId[state.activeGroupId]
      if (!content) return [] as KnowledgeUrl[]
      return content.urls.filter(url => url.status === 'processing')
    },
    // 是否有正在处理的资源
    hasProcessingResources(): boolean {
      return this.processingFiles.length > 0 || this.processingWebpages.length > 0
    }
  },

  actions: {
    // 获取分组列表
    async fetchGroups() {
      this.isLoadingGroups = true
      this.error = null
      
      try {
        this.groups = await knowledgeBaseApi.getGroups()
        
        // 默认选中第一个
        if (this.groups.length > 0 && !this.activeGroupId) {
          this.selectGroup(this.groups[0].id)
        }
      } catch (error) {
        console.error('获取知识库组失败:', error)
        this.error = '获取知识库组失败'
      } finally {
        this.isLoadingGroups = false
      }
    },

    // 创建新知识库组
    async createGroup(name: string, description: string) {
      this.isCreatingGroup = true
      this.error = null
      
      try {
        const newGroup = await knowledgeBaseApi.createGroup(name, description)
        this.groups.push(newGroup)
        return newGroup
      } catch (error) {
        console.error('创建知识库组失败:', error)
        this.error = '创建知识库组失败'
        return null
      } finally {
        this.isCreatingGroup = false
      }
    },

    // 删除知识库组
    async deleteGroup(groupId: string) {
      this.error = null
      
      try {
        await knowledgeBaseApi.deleteGroup(groupId)
        this.groups = this.groups.filter(g => g.id !== groupId)
        
        // 如果删除的是当前激活的组，重置激活状态
        if (this.activeGroupId === groupId) {
          this.activeGroupId = this.groups.length > 0 ? this.groups[0].id : null
          
          // 如果还有其他组，选择第一个
          if (this.activeGroupId) {
            this.selectGroup(this.activeGroupId)
          }
        }
        
        // 从缓存中删除该组的内容
        if (groupId in this.contentByGroupId) {
          delete this.contentByGroupId[groupId]
        }
        
        return true
      } catch (error) {
        console.error('删除知识库组失败:', error)
        this.error = '删除知识库组失败'
        return false
      }
    },

    // 选中一个分组
    async selectGroup(groupId: string) {
      // 如果当前有轮询，先停止
      this.stopPolling()
      
      this.activeGroupId = groupId
      // 如果该分组的内容尚未加载，则去加载
      if (!this.contentByGroupId[groupId]) {
        await this.fetchContentForGroup(groupId)
      }
      
      // 启动对当前组的轮询
      this.startPolling()
    },

    // 根据 ID 获取分组内容
    async fetchContentForGroup(groupId: string) {
      this.isLoadingContent = true
      this.error = null
      
      try {
        const content = await knowledgeBaseApi.getGroupContent(groupId)
        this.contentByGroupId[groupId] = content
      } catch (error) {
        console.error(`获取知识库组 ${groupId} 内容失败:`, error)
        this.error = '获取知识库内容失败'
        // 确保即使失败也有一个空的内容对象
        this.contentByGroupId[groupId] = { files: [], urls: [] }
      } finally {
        this.isLoadingContent = false
      }
    },

    // 上传文件
    async uploadFile(file: File) {
      if (!this.activeGroupId) return null
      
      this.isUploadingFile = true
      this.error = null
      
      try {
        const newFile = await knowledgeBaseApi.uploadFile(this.activeGroupId, file)
        
        // 添加到当前组的文件列表中
        if (this.contentByGroupId[this.activeGroupId]) {
          this.contentByGroupId[this.activeGroupId].files.push(newFile)
        }
        
        // 如果轮询未启动，则启动轮询
        this.startPolling()
        
        return newFile
      } catch (error) {
        console.error('上传文件失败:', error)
        this.error = '上传文件失败'
        return null
      } finally {
        this.isUploadingFile = false
      }
    },

    // 添加网页
    async addWebpage(url: string) {
      if (!this.activeGroupId) return null
      
      this.isAddingUrl = true
      this.error = null
      
      try {
        const newUrl = await knowledgeBaseApi.addWebpage(this.activeGroupId, url)
        
        // 添加到当前组的网页列表中
        if (this.contentByGroupId[this.activeGroupId]) {
          this.contentByGroupId[this.activeGroupId].urls.push(newUrl)
        }
        
        // 如果轮询未启动，则启动轮询
        this.startPolling()
        
        return newUrl
      } catch (error) {
        console.error('添加网页失败:', error)
        this.error = '添加网页失败'
        return null
      } finally {
        this.isAddingUrl = false
      }
    },

    // 删除文件
    async deleteFile(fileId: string) {
      if (!this.activeGroupId) return false
      this.error = null
      
      try {
        await knowledgeBaseApi.deleteFile(this.activeGroupId, fileId)
        
        // 从本地状态中移除
        const groupContent = this.contentByGroupId[this.activeGroupId]
        if (groupContent) {
          groupContent.files = groupContent.files.filter(f => f.id !== fileId)
        }
        
        return true
      } catch (error) {
        console.error('删除文件失败:', error)
        this.error = '删除文件失败'
        return false
      }
    },

    // 删除网页
    async deleteUrl(urlId: string) {
      if (!this.activeGroupId) return false
      this.error = null
      
      try {
        await knowledgeBaseApi.deleteWebpage(this.activeGroupId, urlId)
        
        // 从本地状态中移除
        const groupContent = this.contentByGroupId[this.activeGroupId]
        if (groupContent) {
          groupContent.urls = groupContent.urls.filter(u => u.id !== urlId)
        }
        
        return true
      } catch (error) {
        console.error('删除网页失败:', error)
        this.error = '删除网页失败'
        return false
      }
    },

    // 刷新文件状态
    async refreshFileStatus(fileId: string) {
      if (!this.activeGroupId) return
      
      try {
        const status = await knowledgeBaseApi.getFileStatus(this.activeGroupId, fileId)
        
        // 更新本地状态
        const groupContent = this.contentByGroupId[this.activeGroupId]
        if (groupContent) {
          const file = groupContent.files.find(f => f.id === fileId)
          if (file) {
            file.status = status as 'completed' | 'processing' | 'failed'
          }
        }
      } catch (error) {
        console.error('刷新文件状态失败:', error)
      }
    },

    // 刷新网页状态
    async refreshWebpageStatus(urlId: string) {
      if (!this.activeGroupId) return
      
      try {
        const status = await knowledgeBaseApi.getWebpageStatus(this.activeGroupId, urlId)
        
        // 更新本地状态
        const groupContent = this.contentByGroupId[this.activeGroupId]
        if (groupContent) {
          const url = groupContent.urls.find(u => u.id === urlId)
          if (url) {
            url.status = status as 'completed' | 'processing' | 'failed'
          }
        }
      } catch (error) {
        console.error('刷新网页状态失败:', error)
      }
    },

    // 刷新所有处理中的资源状态
    async refreshAllProcessingStatus() {
      if (!this.activeGroupId) return
      
      const processingFiles = this.processingFiles
      const processingUrls = this.processingWebpages
      
      // 刷新所有处理中的文件状态
      for (const file of processingFiles) {
        await this.refreshFileStatus(file.id)
      }
      
      // 刷新所有处理中的网页状态
      for (const url of processingUrls) {
        await this.refreshWebpageStatus(url.id)
      }
    },

    // 启动轮询
    startPolling() {
      if (!this.pollingEnabled || !this.activeGroupId) return
      
      // 如果有处理中的资源，启动轮询
      if (this.hasProcessingResources) {
        if (!pollingManager) {
          pollingManager = new PollingManager(
            async () => {
              await this.refreshAllProcessingStatus()
              
              // 如果没有处理中的资源了，停止轮询
              if (!this.hasProcessingResources) {
                this.stopPolling()
              }
            },
            this.pollingInterval
          )
        }
        
        pollingManager.start()
      }
    },

    // 停止轮询
    stopPolling() {
      if (pollingManager) {
        pollingManager.stop()
      }
    },

    // 启用/禁用轮询
    setPollingEnabled(enabled: boolean) {
      this.pollingEnabled = enabled
      if (enabled) {
        this.startPolling()
      } else {
        this.stopPolling()
      }
    },

    // 设置轮询间隔
    setPollingInterval(intervalMs: number) {
      this.pollingInterval = intervalMs
      // 如果轮询已启动，更新间隔
      if (pollingManager && this.pollingEnabled) {
        pollingManager.setInterval(intervalMs)
      }
    },

    // 重命名知识库组
    async renameGroup(groupId: string, newName: string) {
      this.error = null
      
      try {
        await knowledgeBaseApi.renameGroup(groupId, newName)
        
        // 更新本地状态
        const groupIndex = this.groups.findIndex(g => g.id === groupId)
        if (groupIndex !== -1) {
          this.groups[groupIndex].name = newName
        }
        
        return true
      } catch (error) {
        console.error('重命名知识库组失败:', error)
        this.error = '重命名知识库组失败'
        return false
      }
    }
  }
});
