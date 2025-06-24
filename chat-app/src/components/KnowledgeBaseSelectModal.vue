<template>
  <div class="modal-overlay" @click.self="closeModal">
    <div class="modal-container">
      <div class="modal-header">
        <h2>选择知识库</h2>
        <button class="close-button" @click="closeModal">
          <Icon name="close" />
        </button>
      </div>
      
      <div class="modal-body">
        <div v-if="isLoading" class="loading-message">
          加载中...
        </div>
        <div v-else-if="groups.length === 0" class="empty-message">
          暂无可用的知识库组
        </div>
        <div v-else class="knowledge-groups-list">
          <div 
            v-for="group in groups" 
            :key="group.id" 
            class="knowledge-group-item"
            @click="toggleGroupSelection(group.id)"
          >
            <div class="group-info">
              <Icon name="knowledge" />
              <div class="group-name">{{ group.name }}</div>
            </div>
            <Icon v-if="isGroupSelected(group.id)" name="check" class="selected-icon" />
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
import { ref, onMounted, computed } from 'vue';
import Icon from './AppIcon.vue';
import { useKnowledgeBaseStore } from '@/stores/knowledgeBase';
import type { KnowledgeGroup } from '@/stores/knowledgeBase';

const props = defineProps<{
  conversationId: string;
  selectedGroupIds: string[];
}>();

const emit = defineEmits<{
  close: [];
  update: [selectedGroupIds: string[]];
}>();

const knowledgeBaseStore = useKnowledgeBaseStore();
const isLoading = ref(true);
const groups = ref<KnowledgeGroup[]>([]);
const selectedIds = ref<string[]>([]);

// 初始化选中的知识库组ID
onMounted(async () => {
  // 加载所有知识库组
  try {
    await knowledgeBaseStore.fetchGroups();
    groups.value = knowledgeBaseStore.groups;
    
    // 设置初始选中状态
    selectedIds.value = [...props.selectedGroupIds];
  } catch (error) {
    console.error('加载知识库组失败:', error);
  } finally {
    isLoading.value = false;
  }
});

// 检查知识库组是否被选中
const isGroupSelected = (groupId: string): boolean => {
  return selectedIds.value.includes(groupId);
};

// 切换知识库组的选中状态
const toggleGroupSelection = (groupId: string): void => {
  if (isGroupSelected(groupId)) {
    // 如果已选中，则取消选中
    selectedIds.value = selectedIds.value.filter(id => id !== groupId);
  } else {
    // 如果未选中，则添加到选中列表
    selectedIds.value.push(groupId);
  }
};

// 确认选择
const confirmSelection = (): void => {
  emit('update', selectedIds.value);
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
  width: 500px;
  max-width: 90%;
  max-height: 90vh;
  display: flex;
  flex-direction: column;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.3);
}

.modal-header {
  padding: 16px 20px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  border-bottom: 1px solid var(--border-color);
}

.modal-header h2 {
  margin: 0;
  font-size: 18px;
  font-weight: 600;
  color: var(--text-primary);
}

.close-button {
  background: transparent;
  border: none;
  color: var(--text-secondary);
  cursor: pointer;
  padding: 6px;
  border-radius: 50%;
  width: 32px;
  height: 32px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.close-button:hover {
  background-color: var(--bg-tertiary);
  color: var(--text-primary);
}

.modal-body {
  padding: 20px;
  overflow-y: auto;
  flex-grow: 1;
  max-height: 60vh;
}

.loading-message,
.empty-message {
  text-align: center;
  padding: 20px;
  color: var(--text-secondary);
}

.knowledge-groups-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.knowledge-group-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 16px;
  border-radius: var(--border-radius-medium);
  cursor: pointer;
  transition: background-color 0.2s;
}

.knowledge-group-item:hover {
  background-color: var(--bg-tertiary);
}

.group-info {
  display: flex;
  align-items: center;
  gap: 12px;
}

.group-info :deep(svg) {
  font-size: 20px;
  color: var(--text-secondary);
}

.group-name {
  font-size: 16px;
  color: var(--text-primary);
}

.selected-icon {
  color: var(--accent-color);
  font-size: 20px;
}

.modal-footer {
  padding: 16px 20px;
  display: flex;
  justify-content: flex-end;
  gap: 12px;
  border-top: 1px solid var(--border-color);
}

.cancel-button,
.confirm-button {
  padding: 8px 16px;
  border-radius: var(--border-radius-medium);
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  transition: background-color 0.2s, color 0.2s;
}

.cancel-button {
  background-color: transparent;
  border: 1px solid var(--border-color);
  color: var(--text-secondary);
}

.cancel-button:hover {
  background-color: var(--bg-tertiary);
  color: var(--text-primary);
}

.confirm-button {
  background-color: var(--accent-color);
  border: none;
  color: white;
}

.confirm-button:hover {
  filter: brightness(0.9);
}
</style> 