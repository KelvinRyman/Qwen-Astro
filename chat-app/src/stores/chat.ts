import { defineStore } from 'pinia';
import { ref, computed } from 'vue';
import type { Ref } from 'vue';
import { chatApi, type ConversationSummary, type Conversation, type QueryResponse } from '@/api/chatApi';

export interface ChatItem {
  id: string;
  title: string;
}

export interface ChatGroup {
  title: string;
  items: ChatItem[];
}

export interface ChatMessage {
  role: 'user' | 'assistant';
  content: string;
  isGenerating?: boolean; // 标记消息是否正在生成中
}

export const useChatStore = defineStore('chat', () => {
  const chatHistory: Ref<ChatGroup[]> = ref([]);
  const isLoading = ref(false);
  const currentConversation: Ref<Conversation | null> = ref(null);
  const error = ref<string | null>(null);
  const isNewChatMode = ref(false);
  const isGeneratingMessage = ref(false);

  // 加载所有对话
  async function loadConversations() {
    isLoading.value = true;
    error.value = null;
    
    try {
      const conversations = await chatApi.getConversations();
      chatHistory.value = chatApi.groupConversationsByDate(conversations);
    } catch (err) {
      console.error('获取对话列表失败:', err);
      error.value = '获取对话列表失败';
    } finally {
      isLoading.value = false;
    }
  }

  // 加载单个对话详情
  async function loadConversation(conversationId: string) {
    isLoading.value = true;
    error.value = null;
    isNewChatMode.value = false;
    
    try {
      currentConversation.value = await chatApi.getConversation(conversationId);
    } catch (err) {
      console.error(`获取对话 ${conversationId} 详情失败:`, err);
      error.value = '获取对话详情失败';
    } finally {
      isLoading.value = false;
    }
  }

  // 准备新对话（不立即创建）
  function prepareNewChat() {
    isNewChatMode.value = true;
    currentConversation.value = null;
  }

  // 创建新对话（仅在发送第一条消息时调用）
  async function createConversation(groupIds?: string[]) {
    isLoading.value = true;
    error.value = null;
    
    try {
      const newConversation = await chatApi.createConversation(groupIds);
      
      // 更新对话列表
      const timeGroup = chatApi.formatRelativeTime(newConversation.created_at);
      const existingGroup = chatHistory.value.find(group => group.title === timeGroup);
      
      if (existingGroup) {
        existingGroup.items.unshift({
          id: newConversation.id,
          title: newConversation.title
        });
      } else {
        chatHistory.value.unshift({
          title: timeGroup,
          items: [{
            id: newConversation.id,
            title: newConversation.title
          }]
        });
      }
      
      currentConversation.value = newConversation;
      isNewChatMode.value = false;
      return newConversation.id;
    } catch (err) {
      console.error('创建新对话失败:', err);
      error.value = '创建新对话失败';
      return null;
    } finally {
      isLoading.value = false;
    }
  }

  // 发送消息
  async function sendMessage(message: string): Promise<QueryResponse | null> {
    error.value = null;
    
    try {
      // 如果是新对话模式，先创建对话
      if (isNewChatMode.value) {
        const conversationId = await createConversation();
        if (!conversationId) return null;
      }
      
      if (!currentConversation.value) return null;
      
      // 先乐观更新UI，添加用户消息
      currentConversation.value.messages.push({
        role: 'user',
        content: message
      });
      
      // 添加一个空的助手消息，标记为正在生成
      isGeneratingMessage.value = true;
      currentConversation.value.messages.push({
        role: 'assistant',
        content: '',
        isGenerating: true
      });
      
      // 获取当前助手消息的索引
      const assistantMessageIndex = currentConversation.value.messages.length - 1;
      
      try {
        // 使用流式API发送消息
        await chatApi.sendMessageStreamed(
          currentConversation.value.id,
          message,
          // 处理每个接收到的文本块
          (chunk) => {
            if (currentConversation.value && currentConversation.value.messages[assistantMessageIndex]) {
              // 累加文本块到助手消息
              currentConversation.value.messages[assistantMessageIndex].content += chunk;
            }
          },
          // 处理完成回调
          (response) => {
            if (currentConversation.value && currentConversation.value.messages[assistantMessageIndex]) {
              // 更新最终消息内容并移除生成中标记
              currentConversation.value.messages[assistantMessageIndex].content = response.answer;
              currentConversation.value.messages[assistantMessageIndex].isGenerating = false;
              isGeneratingMessage.value = false;
              
              // 如果是第一条消息，更新对话标题
              if (currentConversation.value.messages.length === 2) {
                const title = message.length > 20 ? message.substring(0, 20) + '...' : message;
                renameChat(currentConversation.value.id, title);
              }
            }
          }
        );
        
        return null; // 由于是流式响应，这里不返回具体内容
      } catch (err) {
        // 如果流式API失败，回退到普通API
        console.error('流式API失败，回退到普通API:', err);
        
        // 发送普通请求
        const response = await chatApi.sendMessage(currentConversation.value.id, message);
        
        // 更新助手消息
        if (currentConversation.value && currentConversation.value.messages[assistantMessageIndex]) {
          currentConversation.value.messages[assistantMessageIndex].content = response.answer;
          currentConversation.value.messages[assistantMessageIndex].isGenerating = false;
          isGeneratingMessage.value = false;
        }
        
        // 如果是第一条消息，更新对话标题
        if (currentConversation.value.messages.length === 2) {
          const title = message.length > 20 ? message.substring(0, 20) + '...' : message;
          renameChat(currentConversation.value.id, title);
        }
        
        return response;
      }
    } catch (err) {
      console.error('发送消息失败:', err);
      error.value = '发送消息失败';
      isGeneratingMessage.value = false;
      
      // 如果失败，移除最后一条助手消息（如果存在）
      if (currentConversation.value && currentConversation.value.messages.length > 0) {
        const lastMessage = currentConversation.value.messages[currentConversation.value.messages.length - 1];
        if (lastMessage.role === 'assistant' && lastMessage.isGenerating) {
          currentConversation.value.messages.pop();
        }
      }
      
      return null;
    }
  }

  // 重命名聊天
  async function renameChat(chatId: string, newTitle: string) {
    if (!newTitle.trim()) return;
    
    // 更新本地状态
    chatHistory.value.forEach(group => {
      const chat = group.items.find(item => item.id === chatId);
      if (chat) {
        chat.title = newTitle.trim();
      }
    });
    
    // 如果是当前对话，也更新当前对话的标题
    if (currentConversation.value && currentConversation.value.id === chatId) {
      currentConversation.value.title = newTitle.trim();
    }
    
    // 注意：后端API目前可能不支持重命名对话，这里只更新前端状态
    // 如果后端支持，可以添加API调用
  }

  // 删除聊天
  async function deleteChat(chatId: string) {
    try {
      await chatApi.deleteConversation(chatId);
      
      // 更新本地状态
      chatHistory.value.forEach((group, groupIndex) => {
        const chatIndex = group.items.findIndex(item => item.id === chatId);
        if (chatIndex !== -1) {
          group.items.splice(chatIndex, 1);
          
          // 如果该组没有聊天项了，删除该组
          if (group.items.length === 0) {
            chatHistory.value.splice(groupIndex, 1);
          }
        }
      });
      
      // 如果删除的是当前对话，清空当前对话
      if (currentConversation.value && currentConversation.value.id === chatId) {
        currentConversation.value = null;
      }
      
      return true;
    } catch (err) {
      console.error('删除对话失败:', err);
      error.value = '删除对话失败';
      return false;
    }
  }

  // 搜索对话
  async function searchConversations(query: string) {
    if (!query.trim()) {
      await loadConversations();
      return;
    }
    
    isLoading.value = true;
    error.value = null;
    
    try {
      const results = await chatApi.searchConversations(query);
      chatHistory.value = chatApi.groupConversationsByDate(results);
    } catch (err) {
      console.error('搜索对话失败:', err);
      error.value = '搜索对话失败';
    } finally {
      isLoading.value = false;
    }
  }

  return {
    chatHistory,
    isLoading,
    currentConversation,
    error,
    isNewChatMode,
    isGeneratingMessage,
    loadConversations,
    loadConversation,
    prepareNewChat,
    createConversation,
    sendMessage,
    renameChat,
    deleteChat,
    searchConversations
  };
}); 