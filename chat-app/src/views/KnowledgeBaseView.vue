<template>
  <div class="knowledge-base-view">
    <KnowledgeGroupList
      :groups="store.groups"
      :active-group-id="store.activeGroupId"
      :is-loading="store.isLoadingGroups"
      @select-group="store.selectGroup"
      @add-group="isAddModalVisible = true"
      @rename-group="handleRenameGroup"
      @delete-group="handleDeleteGroup"
    />
    <KnowledgeContent
      v-if="store.activeGroup"
      :key="store.activeGroupId ?? ''"
      :group="store.activeGroup"
      :is-loading="store.isLoadingContent"
      :files="store.activeContent.files"
      :urls="store.activeContent.urls"
      :file-count="store.fileCount"
      :url-count="store.urlCount"
      @refresh="refreshActiveGroup"
    />
    <div v-else class="placeholder">
      <div class="empty-state">
        <Icon name="knowledge" class="empty-icon" />
        <h3>选择或创建一个知识库</h3>
        <p>知识库可以帮助你管理和检索文档和网页内容</p>
        <button class="create-btn" @click="isAddModalVisible = true">
          <Icon name="plus" /> 创建知识库
        </button>
      </div>
    </div>
    <AddKnowledgeBaseModal 
      v-if="isAddModalVisible" 
      @close="isAddModalVisible = false"
      @created="handleGroupCreated" 
    />
    <div v-if="isRenameModalVisible" class="modal-overlay" @click.self="isRenameModalVisible = false">
      <div class="rename-modal">
        <h3>重命名知识库</h3>
        <input 
          v-model="newGroupName" 
          type="text" 
          class="rename-input" 
          placeholder="输入新名称"
          @keyup.enter="confirmRename"
        />
        <div class="modal-actions">
          <button class="cancel-btn" @click="isRenameModalVisible = false">取消</button>
          <button class="confirm-btn" @click="confirmRename">确认</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { useKnowledgeBaseStore } from '@/stores/knowledgeBase'
import KnowledgeGroupList from '@/components/knowledge-base/KnowledgeGroupList.vue'
import KnowledgeContent from '@/components/knowledge-base/KnowledgeContent.vue'
import AddKnowledgeBaseModal from '@/components/knowledge-base/AddKnowledgeBaseModal.vue'
import Icon from '@/components/AppIcon.vue'

const store = useKnowledgeBaseStore()
const isAddModalVisible = ref(false)
const isRenameModalVisible = ref(false)
const newGroupName = ref('')
const currentGroupId = ref('')

onMounted(() => {
  // 如果没有分组数据，则获取
  if (store.groups.length === 0) {
    store.fetchGroups()
  }
})

// 处理知识库创建成功事件
function handleGroupCreated(newGroup: { id: string; name: string }) {
  // 自动选择新创建的组
  store.selectGroup(newGroup.id)
}

// 刷新当前激活的知识库组内容
function refreshActiveGroup() {
  if (store.activeGroupId) {
    store.fetchContentForGroup(store.activeGroupId)
  }
}

// 处理重命名知识库组
function handleRenameGroup(groupId: string) {
  // 找到当前组并设置当前名称
  const group = store.groups.find(g => g.id === groupId)
  if (group) {
    newGroupName.value = group.name
    currentGroupId.value = groupId
    isRenameModalVisible.value = true
  }
}

// 确认重命名
async function confirmRename() {
  if (newGroupName.value.trim() && currentGroupId.value) {
    try {
      // 这里需要在store中添加renameGroup方法
      await store.renameGroup(currentGroupId.value, newGroupName.value.trim())
      isRenameModalVisible.value = false
    } catch (error) {
      console.error('重命名知识库失败:', error)
    }
  }
}

// 处理删除知识库组
async function handleDeleteGroup(groupId: string) {
  if (confirm('确定要删除这个知识库吗？此操作不可恢复。')) {
    await store.deleteGroup(groupId)
  }
}
</script>

<style scoped>
.knowledge-base-view {
  display: flex;
  height: 100%;
  width: 100%;
  background-color: var(--bg-secondary);
}
.placeholder {
  flex-grow: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--text-secondary);
}

.empty-state {
  text-align: center;
  max-width: 400px;
  padding: 20px;
}

.empty-icon {
  font-size: 64px;
  color: var(--text-secondary);
  margin-bottom: 16px;
  opacity: 0.7;
}

.empty-state h3 {
  font-size: 1.2em;
  margin: 0 0 8px 0;
  color: var(--text-primary);
}

.empty-state p {
  margin: 0 0 24px 0;
  color: var(--text-secondary);
}

.create-btn {
  background-color: var(--button-primary-bg);
  color: var(--button-primary-text);
  border: none;
  padding: 10px 20px;
  border-radius: 8px;
  cursor: pointer;
  font-size: 1em;
  font-weight: 500;
  display: flex;
  align-items: center;
  gap: 8px;
  margin: 0 auto;
}

.create-btn:hover {
  filter: brightness(1.1);
}

/* 模态框样式 */
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background-color: var(--bg-overlay);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}

.rename-modal {
  background-color: var(--modal-bg);
  border-radius: var(--border-radius-medium);
  padding: 24px;
  width: 400px;
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.2);
}

.rename-modal h3 {
  margin-top: 0;
  margin-bottom: 16px;
  font-size: 18px;
  color: var(--text-primary);
}

.rename-input {
  width: 100%;
  padding: 10px 12px;
  border-radius: 6px;
  border: 1px solid var(--border-color);
  background-color: var(--bg-input);
  color: var(--text-primary);
  font-size: 14px;
  margin-bottom: 16px;
}

.modal-actions {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
}

.cancel-btn {
  padding: 8px 16px;
  border-radius: 6px;
  border: 1px solid var(--border-color);
  background-color: transparent;
  color: var(--text-secondary);
  cursor: pointer;
}

.confirm-btn {
  padding: 8px 16px;
  border-radius: 6px;
  border: none;
  background-color: var(--button-primary-bg);
  color: var(--text-primary);
  cursor: pointer;
}

.confirm-btn:hover {
  filter: brightness(1.1);
}
</style>
