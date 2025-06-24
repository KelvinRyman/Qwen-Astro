import axios from 'axios';

// API基础URL
const API_BASE_URL = 'http://127.0.0.1:5000/api';

// 创建axios实例
const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 10000,
  withCredentials: false,
});

// 定义聊天相关的数据接口
export interface Conversation {
  id: string;
  title: string;
  created_at: string;
  group_ids: string[] | null;
  agent_id?: string | null;
  messages: Message[];
}

export interface Message {
  role: 'user' | 'assistant';
  content: string;
  timestamp?: string;
  isGenerating?: boolean;
  group_ids?: string[]; // 用户消息关联的知识库组ID
  sources?: SourceNode[]; // 助手消息的引用来源
}

export interface ConversationSummary {
  id: string;
  title: string;
  created_at: string;
  last_message: string;
}

// 源节点接口，表示检索到的知识片段
export interface SourceNode {
  id: string;
  score: number;
  group_id: string;
  file_name: string;
  page_label: string;
  text_snippet: string;
  source_type: 'file' | 'webpage';  // 来源类型
  source_url?: string;              // 网页URL（可选）
}

export interface QueryResponse {
  answer: string;
  sources: SourceNode[];
}

// 聊天API服务
export const chatApi = {
  // 获取所有对话列表
  async getConversations(): Promise<ConversationSummary[]> {
    const response = await apiClient.get('/conversations');
    return response.data;
  },

  // 获取单个对话详情
  async getConversation(conversationId: string): Promise<Conversation> {
    const response = await apiClient.get(`/conversations/${conversationId}`);
    return response.data;
  },

  // 创建新对话
  async createConversation(groupIds?: string[], agentId?: string): Promise<Conversation> {
    const response = await apiClient.post('/conversations', {
      group_ids: groupIds,
      agent_id: agentId
    });
    return response.data;
  },

  // 发送消息到对话
  async sendMessage(conversationId: string, message: string, groupIds?: string[]): Promise<QueryResponse> {
    const response = await apiClient.post(`/conversations/${conversationId}/messages`, {
      message,
      group_ids: groupIds
    });
    return response.data;
  },

  // 删除对话
  async deleteConversation(conversationId: string): Promise<void> {
    await apiClient.delete(`/conversations/${conversationId}`);
  },

  // 删除消息
  async deleteMessages(conversationId: string, fromIndex: number): Promise<void> {
    await apiClient.delete(`/conversations/${conversationId}/messages`, {
      data: { from_index: fromIndex }
    });
  },

  // 重命名对话
  async renameConversation(conversationId: string, newTitle: string): Promise<void> {
    await apiClient.post(`/conversations/${conversationId}/rename`, {
      title: newTitle
    });
  },

  // 更新对话关联的知识库组
  async updateConversationGroups(conversationId: string, groupIds: string[]): Promise<void> {
    await apiClient.post(`/conversations/${conversationId}/groups`, {
      group_ids: groupIds
    });
  },

  // 搜索对话
  async searchConversations(query: string): Promise<ConversationSummary[]> {
    const response = await apiClient.get(`/conversations/search?q=${encodeURIComponent(query)}`);
    return response.data;
  },

  // 格式化日期为相对时间
  formatRelativeTime(dateString: string): string {
    const date = new Date(dateString);
    const now = new Date();
    const diffInDays = Math.floor((now.getTime() - date.getTime()) / (1000 * 60 * 60 * 24));
    
    if (diffInDays === 0) {
      return '今天';
    } else if (diffInDays === 1) {
      return '昨天';
    } else if (diffInDays < 7) {
      return '前 7 天';
    } else if (diffInDays < 30) {
      return '前 30 天';
    } else {
      // 格式化为年月日
      return `${date.getFullYear()}年${date.getMonth() + 1}月${date.getDate()}日`;
    }
  },

  // 将对话列表按日期分组
  groupConversationsByDate(conversations: ConversationSummary[]): { title: string; items: ConversationSummary[] }[] {
    const groupedConversations: { [key: string]: ConversationSummary[] } = {};
    
    conversations.forEach(conversation => {
      const timeGroup = this.formatRelativeTime(conversation.created_at);
      if (!groupedConversations[timeGroup]) {
        groupedConversations[timeGroup] = [];
      }
      groupedConversations[timeGroup].push(conversation);
    });
    
    // 转换为数组格式并按时间排序
    const sortOrder = ['今天', '昨天', '前 7 天', '前 30 天'];
    
    return Object.keys(groupedConversations)
      .sort((a, b) => {
        const indexA = sortOrder.indexOf(a);
        const indexB = sortOrder.indexOf(b);
        
        if (indexA !== -1 && indexB !== -1) {
          return indexA - indexB;
        } else if (indexA !== -1) {
          return -1;
        } else if (indexB !== -1) {
          return 1;
        } else {
          return a.localeCompare(b);
        }
      })
      .map(title => ({
        title,
        items: groupedConversations[title]
      }));
  },

  // 发送消息到对话（流式响应）
  async sendMessageStreamed(
    conversationId: string, 
    message: string, 
    onChunk: (chunk: string) => void, 
    onComplete: (response: QueryResponse) => void,
    groupIds?: string[]
  ): Promise<void> {
    try {
      // 创建请求
      const response = await fetch(`${API_BASE_URL}/conversations/${conversationId}/messages/stream`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ 
          message,
          group_ids: groupIds
        })
      });

      // 创建读取器
      const reader = response.body?.getReader();
      if (!reader) {
        throw new Error('无法创建响应流读取器');
      }

      // 用于存储完整响应
      let fullResponse = '';
      
      // 读取流
      while (true) {
        const { done, value } = await reader.read();
        if (done) break;
        
        // 解码接收到的块
        const chunk = new TextDecoder().decode(value);
        fullResponse += chunk;
        
        // 调用回调函数处理新块
        onChunk(chunk);
      }
      
      // 完成后解析完整响应并调用完成回调
      const jsonResponse = JSON.parse(fullResponse);
      onComplete(jsonResponse);
    } catch (error) {
      console.error('流式发送消息失败:', error);
      throw error;
    }
  },

  // 重新生成消息（流式响应）
  async regenerateMessageStreamed(
    conversationId: string, 
    fromMessageIndex: number,
    onChunk: (chunk: string) => void, 
    onComplete: (response: QueryResponse) => void
  ): Promise<void> {
    try {
      const response = await fetch(`${API_BASE_URL}/conversations/${conversationId}/regenerate/stream`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ from_message_index: fromMessageIndex })
      });

      const reader = response.body?.getReader();
      if (!reader) {
        throw new Error('无法创建响应流读取器');
      }

      let fullResponse = '';
      const decoder = new TextDecoder();

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;
        
        const chunk = decoder.decode(value, { stream: true });
        fullResponse += chunk;
        onChunk(chunk); // 直接传递原始块
      }
      
      // 流结束后，fullResponse包含完整的JSON对象
      const jsonResponse = JSON.parse(fullResponse);
      onComplete(jsonResponse);

    } catch (error) {
      console.error('流式重新生成消息失败:', error);
      throw error;
    }
  },
}; 