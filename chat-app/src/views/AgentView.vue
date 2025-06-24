<template>
  <div class="agent-view">
    <!-- 页面头部 -->
    <div class="page-header">
      <div class="header-content">
        <h1>Agent</h1>
        <p>自由地创建结合了系统 Prompt 和特定 MCP 工具的自定义版本的 AI Agent。</p>
      </div>
      <button class="create-button" @click="openCreateModal">
        <Icon name="plus" />
        创建
      </button>
    </div>

    <!-- 搜索框 -->
    <div class="search-container">
      <div class="search-box">
        <Icon name="search" />
        <input
          type="text"
          placeholder="搜索Agent"
          v-model="searchQuery"
        />
      </div>
    </div>

    <!-- Agent 列表 -->
    <div class="agents-container">
      <div v-if="isLoading" class="loading-message">
        加载中...
      </div>
      <div v-else-if="filteredAgents.length === 0" class="empty-message">
        <div class="empty-content">
          <Icon name="agent" class="empty-icon"/>
          <h3>暂无Agent</h3>
          <p>创建您的第一个Agent来开始使用</p>
          <button class="create-button-secondary" @click="openCreateModal">
            <Icon name="plus" />
            创建Agent
          </button>
        </div>
      </div>
      <div v-else class="agents-grid">
        <div 
          v-for="agent in filteredAgents" 
          :key="agent.id" 
          class="agent-card"
          @click="selectAgent(agent)"
        >
          <div class="agent-icon">
            <Icon name="agent" />
          </div>
          <div class="agent-info">
            <h3 class="agent-name">{{ agent.name }}</h3>
            <p class="agent-description">{{ agent.description || '无描述' }}</p>
            <div class="agent-meta">
              <span v-if="agent.enable_MCP" class="mcp-badge">MCP</span>
              <span class="created-date">{{ formatDate(agent.created_at) }}</span>
            </div>
          </div>
          <div class="agent-actions">
            <button class="action-button" @click.stop="editAgent(agent)">
              <Icon name="edit" />
            </button>
            <button class="action-button delete" @click.stop="deleteAgent(agent)">
              <Icon name="delete" />
            </button>
          </div>
        </div>
      </div>
    </div>

    <!-- Agent 创建/编辑弹窗 -->
    <AgentCreateModal 
      v-if="isCreateModalOpen"
      :agent="editingAgent"
      @close="closeCreateModal"
      @save="handleAgentSave"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue';
import Icon from '@/components/AppIcon.vue';
import AgentCreateModal from '@/components/AgentCreateModal.vue';
import { useAgentStore } from '@/stores/agent';
import type { Agent } from '@/api/agentApi';

const agentStore = useAgentStore();

// 响应式数据
const searchQuery = ref('');
const isCreateModalOpen = ref(false);
const editingAgent = ref<Agent | null>(null);

// 计算属性
const isLoading = computed(() => agentStore.isLoading);
const agents = computed(() => agentStore.agents);

const filteredAgents = computed(() => {
  let result = agents.value;
  
  // 搜索过滤
  if (searchQuery.value.trim()) {
    const query = searchQuery.value.toLowerCase();
    result = result.filter(agent => 
      agent.name.toLowerCase().includes(query) ||
      agent.description.toLowerCase().includes(query)
    );
  }
  
  return result;
});

// 方法

const openCreateModal = () => {
  editingAgent.value = null;
  isCreateModalOpen.value = true;
};

const closeCreateModal = () => {
  isCreateModalOpen.value = false;
  editingAgent.value = null;
};

const editAgent = (agent: Agent) => {
  editingAgent.value = agent;
  isCreateModalOpen.value = true;
};

const selectAgent = (agent: Agent) => {
  // 可以添加选择Agent的逻辑，比如跳转到聊天页面
  console.log('Selected agent:', agent);
};

const deleteAgent = async (agent: Agent) => {
  if (confirm(`确定要删除Agent "${agent.name}" 吗？`)) {
    await agentStore.deleteAgent(agent.id);
  }
};

const handleAgentSave = async (agentData: any) => {
  if (editingAgent.value) {
    // 更新现有Agent
    await agentStore.updateAgent(editingAgent.value.id, agentData);
  } else {
    // 创建新Agent
    await agentStore.createAgent(agentData);
  }
  closeCreateModal();
};

const formatDate = (dateString: string) => {
  const date = new Date(dateString);
  return date.toLocaleDateString('zh-CN');
};

// 生命周期
onMounted(async () => {
  await agentStore.loadAgents();
});
</script>

<style scoped>
.agent-view {
  flex: 1;
  display: flex;
  flex-direction: column;
  height: 100vh;
  background-color: var(--bg-secondary);
  overflow-y: auto;
  padding: 40px;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 40px;
}

.header-content h1 {
  font-size: 48px;
  font-weight: 600;
  color: var(--text-primary);
  margin: 0 0 12px 0;
}

.header-content p {
  font-size: 18px;
  color: var(--text-secondary);
  margin: 0;
  max-width: 100%;
}

.create-button {
  display: flex;
  align-items: center;
  justify-content: flex-start;
  gap: 6px;
  background-color: #10b981;
  color: white;
  border: none;
  padding: 12px 20px;
  border-radius: var(--border-radius-medium);
  font-size: 16px;
  font-weight: 600;
  cursor: pointer;
  transition: background-color 0.2s;
  box-shadow: 0 2px 4px rgba(16, 185, 129, 0.2);
}

.create-button:hover {
  background-color: #059669;
  box-shadow: 0 4px 8px rgba(16, 185, 129, 0.3);
}

.search-container {
  margin-bottom: 32px;
}

.search-box {
  display: flex;
  align-items: center;
  gap: 12px;
  background-color: var(--bg-input);
  border-radius: var(--border-radius-large);
  padding: 16px 20px;
  max-width: 600px;
}

.search-box input {
  flex: 1;
  background: transparent;
  border: none;
  outline: none;
  color: var(--text-primary);
  font-size: 16px;
}

.search-box input::placeholder {
  color: var(--text-placeholder);
}



.agents-container {
  flex: 1;
}

.loading-message,
.empty-message {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 300px;
  color: var(--text-secondary);
}

.empty-content {
  text-align: center;
}

.empty-icon {
  font-size: 48px;
}

.empty-content h3 {
  margin: 16px 0 8px 0;
  color: var(--text-primary);
}

.empty-content p {
  margin: 0 0 24px 0;
  color: var(--text-secondary);
}

.create-button-secondary {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  background-color: var(--bg-tertiary);
  color: var(--text-primary);
  border: 1px solid var(--border-color);
  padding: 10px 20px;
  border-radius: var(--border-radius-medium);
  font-size: 14px;
  cursor: pointer;
  transition: all 0.2s;
}

.create-button-secondary:hover {
  background-color: var(--bg-input);
}

.agents-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
  gap: 20px;
}

.agent-card {
  background-color: var(--bg-primary);
  border: 1px solid var(--border-color);
  border-radius: var(--border-radius-large);
  padding: 20px;
  cursor: pointer;
  transition: all 0.2s;
  position: relative;
}

.agent-card:hover {
  border-color: var(--accent-color);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
}

.agent-icon {
  width: 48px;
  height: 48px;
  background-color: var(--accent-color);
  border-radius: var(--border-radius-medium);
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  font-size: 48px;
  margin-bottom: 16px;
  margin-left: -6px;
}

.agent-name {
  font-size: 18px;
  font-weight: 600;
  color: var(--text-primary);
  margin: 0 0 8px 0;
  padding-left: 0;
}

.agent-description {
  font-size: 14px;
  color: var(--text-secondary);
  margin: 0 0 12px 0;
  line-height: 1.4;
  display: -webkit-box;
  -webkit-box-orient: vertical;
  overflow: hidden;
  padding-left: 0;
}

.agent-meta {
  display: flex;
  align-items: center;
  gap: 8px;
}

.mcp-badge {
  border: 1px solid var(--text-placeholder);
  background-color: var(--accent-color);
  color: white;
  font-size: 12px;
  padding: 6px 8px;
  border-radius: 12px;
  font-weight: 500;
}

.created-date {
  font-size: 12px;
  color: var(--text-secondary);
}

.agent-actions {
  position: absolute;
  top: 16px;
  right: 16px;
  display: flex;
  gap: 4px;
  opacity: 0;
  transition: opacity 0.2s;
}

.agent-card:hover .agent-actions {
  opacity: 1;
}

.action-button {
  background: var(--bg-secondary);
  border: 1px solid var(--border-color);
  color: var(--text-secondary);
  width: 32px;
  height: 32px;
  border-radius: 6px;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: all 0.2s;
}

.action-button:hover {
  background-color: var(--bg-tertiary);
  color: var(--text-primary);
}

.action-button.delete:hover {
  background-color: #dc2626;
  color: white;
  border-color: #dc2626;
}
</style>
