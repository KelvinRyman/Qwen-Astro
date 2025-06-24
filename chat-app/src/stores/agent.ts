import { defineStore } from 'pinia';
import { ref } from 'vue';
import type { Ref } from 'vue';
import { agentApi, type Agent, type AgentCreateRequest, type AgentUpdateRequest } from '@/api/agentApi';

export const useAgentStore = defineStore('agent', () => {
  const agents: Ref<Agent[]> = ref([]);
  const isLoading = ref(false);
  const error = ref<string | null>(null);

  // 加载所有Agent
  async function loadAgents() {
    isLoading.value = true;
    error.value = null;
    
    try {
      agents.value = await agentApi.getAgents();
    } catch (err) {
      console.error('获取Agent列表失败:', err);
      error.value = '获取Agent列表失败';
    } finally {
      isLoading.value = false;
    }
  }

  // 创建新Agent
  async function createAgent(data: AgentCreateRequest): Promise<Agent | null> {
    error.value = null;
    
    try {
      const newAgent = await agentApi.createAgent(data);
      agents.value.push(newAgent);
      return newAgent;
    } catch (err) {
      console.error('创建Agent失败:', err);
      error.value = '创建Agent失败';
      return null;
    }
  }

  // 更新Agent
  async function updateAgent(agentId: string, data: AgentUpdateRequest): Promise<Agent | null> {
    error.value = null;
    
    try {
      const updatedAgent = await agentApi.updateAgent(agentId, data);
      const index = agents.value.findIndex(agent => agent.id === agentId);
      if (index !== -1) {
        agents.value[index] = updatedAgent;
      }
      return updatedAgent;
    } catch (err) {
      console.error('更新Agent失败:', err);
      error.value = '更新Agent失败';
      return null;
    }
  }

  // 删除Agent
  async function deleteAgent(agentId: string): Promise<boolean> {
    error.value = null;
    
    try {
      await agentApi.deleteAgent(agentId);
      agents.value = agents.value.filter(agent => agent.id !== agentId);
      return true;
    } catch (err) {
      console.error('删除Agent失败:', err);
      error.value = '删除Agent失败';
      return false;
    }
  }

  // 根据ID获取Agent
  function getAgentById(agentId: string): Agent | undefined {
    return agents.value.find(agent => agent.id === agentId);
  }

  return {
    agents,
    isLoading,
    error,
    loadAgents,
    createAgent,
    updateAgent,
    deleteAgent,
    getAgentById,
  };
});
