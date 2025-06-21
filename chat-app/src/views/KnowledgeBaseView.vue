<template>
  <div class="knowledge-base-view">
    <KnowledgeGroupList
      :groups="store.groups"
      :active-group-id="store.activeGroupId"
      :is-loading="store.isLoadingGroups"
      @select-group="store.selectGroup"
      @add-group="isAddModalVisible = true"
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
      @delete-file="store.deleteFile"
      @refresh-file="store.refreshFileStatus"
    />
    <div v-else class="placeholder">
      <!-- 可以在这里放一个 "请选择或创建一个知识库" 的提示 -->
    </div>
    <AddKnowledgeBaseModal v-if="isAddModalVisible" @close="isAddModalVisible = false" />
  </div>
</template>

<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { useKnowledgeBaseStore } from '@/stores/knowledgeBase'
import KnowledgeGroupList from '@/components/knowledge-base/KnowledgeGroupList.vue'
import KnowledgeContent from '@/components/knowledge-base/KnowledgeContent.vue'
import AddKnowledgeBaseModal from '@/components/knowledge-base/AddKnowledgeBaseModal.vue'

const store = useKnowledgeBaseStore()
const isAddModalVisible = ref(false)

onMounted(() => {
  // 如果没有分组数据，则获取
  if (store.groups.length === 0) {
    store.fetchGroups()
  }
})
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
</style>
