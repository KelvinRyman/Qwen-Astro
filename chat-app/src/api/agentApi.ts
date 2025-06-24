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

// 定义Agent相关的数据接口
export interface Agent {
  id: string;
  name: string;
  system_prompt: string;
  description: string;
  enable_MCP: boolean;
  tools: string;
  created_at: string;
}

export interface AgentCreateRequest {
  name: string;
  system_prompt: string;
  description?: string;
  enable_MCP?: boolean;
  tools?: string;
}

export interface AgentUpdateRequest {
  name?: string;
  system_prompt?: string;
  description?: string;
  enable_MCP?: boolean;
  tools?: string;
}

// Agent API服务
export const agentApi = {
  // 获取所有Agent
  async getAgents(): Promise<Agent[]> {
    const response = await apiClient.get('/agents');
    return response.data;
  },

  // 获取单个Agent详情
  async getAgent(agentId: string): Promise<Agent> {
    const response = await apiClient.get(`/agents/${agentId}`);
    return response.data;
  },

  // 创建新Agent
  async createAgent(data: AgentCreateRequest): Promise<Agent> {
    const response = await apiClient.post('/agents', data);
    return response.data;
  },

  // 更新Agent
  async updateAgent(agentId: string, data: AgentUpdateRequest): Promise<Agent> {
    const response = await apiClient.put(`/agents/${agentId}`, data);
    return response.data;
  },

  // 删除Agent
  async deleteAgent(agentId: string): Promise<void> {
    await apiClient.delete(`/agents/${agentId}`);
  },
};
