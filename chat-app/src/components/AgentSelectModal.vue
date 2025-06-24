<template>
  <div class="modal-overlay" @click.self="closeModal">
    <div class="modal-container">
      <div class="modal-header">
        <h2>选择Agent</h2>
        <button class="close-button" @click="closeModal">
          <Icon name="close" />
        </button>
      </div>
      
      <div class="modal-body">
        <div v-if="isLoading" class="loading-message">
          加载中...
        </div>
        <div v-else-if="agents.length === 0" class="empty-message">
          暂无可用的Agent
        </div>
        <div v-else class="agents-list">
          <!-- 无Agent选项 -->
          <div 
            class="agent-item"
            :class="{ 'selected': selectedAgentId === null }"
            @click="selectAgent(null)"
          >
            <div class="agent-info">
              <Icon name="chat" />
              <div class="agent-details">
                <div class="agent-name">无Agent</div>
                <div class="agent-description">使用默认的聊天模式</div>
              </div>
            </div>
            <Icon v-if="selectedAgentId === null" name="check" class="selected-icon" />
          </div>
          
          <!-- Agent列表 -->
          <div 
            v-for="agent in agents" 
            :key="agent.id" 
            class="agent-item"
            :class="{ 'selected': selectedAgentId === agent.id }"
            @click="selectAgent(agent.id)"
          >
            <div class="agent-info">
              <Icon name="agent" />
              <div class="agent-details">
                <div class="agent-name">{{ agent.name }}</div>
                <div class="agent-description">{{ agent.description || '无描述' }}</div>
              </div>
            </div>
            <Icon v-if="selectedAgentId === agent.id" name="check" class="selected-icon" />
          </div>
        </div>
      </div>
      
      <div class="modal-footer">
        <button class="cancel-button" @click="closeModal">取消</button>
        <button class="confirm-button" @click="confirmSelection">确定</button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue';
import Icon from './AppIcon.vue';
import { useAgentStore } from '@/stores/agent';
import type { Agent } from '@/api/agentApi';

const props = defineProps<{
  currentAgentId?: string | null;
}>();

const emit = defineEmits<{
  close: [];
  select: [agentId: string | null];
}>();

const agentStore = useAgentStore();
const isLoading = ref(true);
const agents = ref<Agent[]>([]);
const selectedAgentId = ref<string | null>(props.currentAgentId || null);

// 初始化
onMounted(async () => {
  try {
    await agentStore.loadAgents();
    agents.value = agentStore.agents;
  } catch (error) {
    console.error('加载Agent列表失败:', error);
  } finally {
    isLoading.value = false;
  }
});

// 选择Agent
const selectAgent = (agentId: string | null): void => {
  selectedAgentId.value = agentId;
};

// 确认选择
const confirmSelection = (): void => {
  emit('select', selectedAgentId.value);
  closeModal();
};

// 关闭弹窗
const closeModal = (): void => {
  emit('close');
};
</script>

<style scoped>
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background-color: rgba(0, 0, 0, 0.5);
  display: flex;
  justify-content: center;
  align-items: center;
  z-index: 1000;
}

.modal-container {
  background-color: var(--bg-primary);
  border-radius: var(--border-radius-large);
  width: 90%;
  max-width: 500px;
  max-height: 80vh;
  display: flex;
  flex-direction: column;
  box-shadow: 0 10px 30px rgba(0, 0, 0, 0.3);
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 20px 24px;
  border-bottom: 1px solid var(--border-color);
}

.modal-header h2 {
  margin: 0;
  color: var(--text-primary);
  font-size: 18px;
  font-weight: 600;
}

.close-button {
  background: transparent;
  border: none;
  color: var(--text-secondary);
  cursor: pointer;
  padding: 4px;
  border-radius: 4px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.close-button:hover {
  background-color: var(--bg-tertiary);
  color: var(--text-primary);
}

.modal-body {
  flex: 1;
  overflow-y: auto;
  padding: 16px 24px;
}

.loading-message,
.empty-message {
  text-align: center;
  padding: 40px 20px;
  color: var(--text-secondary);
  font-size: 16px;
}

.agents-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.agent-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 16px;
  border-radius: var(--border-radius-medium);
  cursor: pointer;
  transition: background-color 0.2s;
  border: 2px solid transparent;
}

.agent-item:hover {
  background-color: var(--bg-secondary);
}

.agent-item.selected {
  background-color: var(--bg-tertiary);
  border-color: var(--accent-color);
}

.agent-info {
  display: flex;
  align-items: center;
  gap: 12px;
  flex: 1;
}

.agent-details {
  flex: 1;
}

.agent-name {
  font-weight: 600;
  color: var(--text-primary);
  margin-bottom: 4px;
}

.agent-description {
  font-size: 14px;
  color: var(--text-secondary);
  line-height: 1.4;
}

.selected-icon {
  color: var(--accent-color);
  font-size: 20px;
}

.modal-footer {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
  padding: 20px 24px;
  border-top: 1px solid var(--border-color);
}

.cancel-button,
.confirm-button {
  padding: 10px 20px;
  border-radius: var(--border-radius-medium);
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;
}

.cancel-button {
  background: transparent;
  border: 1px solid var(--border-color);
  color: var(--text-secondary);
}

.cancel-button:hover {
  background-color: var(--bg-secondary);
  color: var(--text-primary);
}

.confirm-button {
  background-color: var(--accent-color);
  border: 1px solid var(--accent-color);
  color: white;
}

.confirm-button:hover {
  background-color: var(--accent-color-hover);
  border-color: var(--accent-color-hover);
}
</style>
