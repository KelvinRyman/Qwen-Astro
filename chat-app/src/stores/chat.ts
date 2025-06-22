import { defineStore } from 'pinia';
import { ref } from 'vue';
import type { Ref } from 'vue';

export interface ChatItem {
  id: number;
  title: string;
}

export interface ChatGroup {
  title: string;
  items: ChatItem[];
}

export const useChatStore = defineStore('chat', () => {
  const chatHistory: Ref<ChatGroup[]> = ref([
    {
      title: '今天',
      items: [
        { id: 1, title: 'TypeScript vs JavaScript in Vue' },
      ]
    },
    {
      title: '昨天',
      items: [
        { id: 2, title: 'ChatGPT 对话记录管理' },
      ]
    },
    {
      title: '前 7 天',
      items: [
        { id: 3, title: 'LLM Fine-Tuning in Space' },
        { id: 4, title: 'DeepSpeed MP Error' },
        { id: 5, title: '双卡 3090 微调 Qwen3' }
      ]
    }
  ]);

  // 重命名聊天
  function renameChat(chatId: number, newTitle: string) {
    if (!newTitle.trim()) return;

    chatHistory.value.forEach(group => {
      const chat = group.items.find(item => item.id === chatId);
      if (chat) {
        chat.title = newTitle.trim();
      }
    });
  }

  // 删除聊天
  function deleteChat(chatId: number) {
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
  }

  return {
    chatHistory,
    renameChat,
    deleteChat
  };
}); 