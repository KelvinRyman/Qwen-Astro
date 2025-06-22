import axios from 'axios';
import type { KnowledgeGroup, KnowledgeFile, KnowledgeUrl } from '../stores/knowledgeBase';

// API基础URL
const API_BASE_URL = 'http://127.0.0.1:5000/api';

// 创建axios实例
const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 10000,
  // 允许跨域请求携带凭证
  withCredentials: false,
});

// 知识库API服务
export const knowledgeBaseApi = {
  // 获取所有知识库组
  async getGroups(): Promise<KnowledgeGroup[]> {
    const response = await apiClient.get('/groups');
    // 转换后端数据格式为前端格式
    return response.data.map((group: any) => ({
      id: group.id,
      name: group.name,
      description: group.description || "",
      embedding_model: 'BAAI/bge-m3', // 固定值
      rerank_model: 'BAAI/bge-reranker-v2-m3', // 固定值
    }));
  },

  // 创建新知识库组
  async createGroup(name: string, description: string = ""): Promise<KnowledgeGroup> {
    console.log("发送创建知识库请求:", { name, description });
    const response = await apiClient.post('/groups', { name, description });
    return {
      id: response.data.id,
      name: response.data.name,
      description: response.data.description,
      embedding_model: 'BAAI/bge-m3', // 固定值
      rerank_model: 'BAAI/bge-reranker-v2-m3', // 固定值
    };
  },

  // 重命名知识库组
  async renameGroup(groupId: string, newName: string): Promise<void> {
    await apiClient.put(`/groups/${groupId}`, { name: newName });
  },

  // 删除知识库组
  async deleteGroup(groupId: string): Promise<void> {
    await apiClient.delete(`/groups/${groupId}`);
  },

  // 获取知识库组内容
  async getGroupContent(groupId: string): Promise<{ files: KnowledgeFile[], urls: KnowledgeUrl[] }> {
    const response = await apiClient.get(`/groups/${groupId}/sources`);
    
    // 转换后端文件数据为前端格式
    const files: KnowledgeFile[] = response.data.files.map((file: any) => ({
      id: file.id,
      name: file.name,
      date: file.creation_time,
      size: this.formatFileSize(file.size),
      status: file.status,
      type: this.getFileType(file.name),
    }));

    // 转换后端网页数据为前端格式
    const urls: KnowledgeUrl[] = response.data.webpages.map((webpage: any) => ({
      id: webpage.id,
      url: webpage.url,
      date: webpage.creation_time,
      status: webpage.status,
    }));

    return { files, urls };
  },

  // 上传文件到知识库组
  async uploadFile(groupId: string, file: File): Promise<KnowledgeFile> {
    const formData = new FormData();
    formData.append('files', file);

    const response = await apiClient.post(`/groups/${groupId}/files`, formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });

    // 返回第一个文件的信息（假设一次只上传一个文件）
    const fileData = response.data[0];
    return {
      id: fileData.id,
      name: fileData.name,
      date: fileData.creation_time,
      size: this.formatFileSize(fileData.size),
      status: fileData.status,
      type: this.getFileType(fileData.name),
    };
  },

  // 添加网页到知识库组
  async addWebpage(groupId: string, url: string): Promise<KnowledgeUrl> {
    const response = await apiClient.post(`/groups/${groupId}/webpages`, {
      urls: [url],
    });

    // 返回第一个网页的信息（假设一次只添加一个网页）
    const webpageData = response.data[0];
    return {
      id: webpageData.id,
      url: webpageData.url,
      date: webpageData.creation_time,
      status: webpageData.status,
    };
  },

  // 删除文件
  async deleteFile(groupId: string, fileId: string): Promise<void> {
    await apiClient.delete(`/groups/${groupId}/files`, {
      data: { file_ids: [fileId] },
    });
  },

  // 删除网页
  async deleteWebpage(groupId: string, webpageId: string): Promise<void> {
    await apiClient.delete(`/groups/${groupId}/webpages`, {
      data: { webpage_ids: [webpageId] },
    });
  },

  // 获取文件状态
  async getFileStatus(groupId: string, fileId: string): Promise<string> {
    const response = await apiClient.get(`/groups/${groupId}/files/${fileId}`);
    return response.data.status;
  },

  // 获取网页状态
  async getWebpageStatus(groupId: string, webpageId: string): Promise<string> {
    const response = await apiClient.get(`/groups/${groupId}/webpages/${webpageId}`);
    return response.data.status;
  },

  // 辅助方法：格式化文件大小
  formatFileSize(sizeInBytes: number): string {
    if (sizeInBytes < 1024) {
      return `${sizeInBytes} B`;
    } else if (sizeInBytes < 1024 * 1024) {
      return `${(sizeInBytes / 1024).toFixed(0)} KB`;
    } else {
      return `${(sizeInBytes / (1024 * 1024)).toFixed(0)} MB`;
    }
  },

  // 辅助方法：获取文件类型
  getFileType(filename: string): 'pdf' | 'text' {
    const extension = filename.split('.').pop()?.toLowerCase();
    if (extension === 'pdf') {
      return 'pdf';
    }
    return 'text';
  },
}; 