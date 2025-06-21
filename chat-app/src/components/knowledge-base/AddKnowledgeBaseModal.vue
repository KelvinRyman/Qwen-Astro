<template>
  <div class="modal-overlay" @click.self="emit('close')">
    <div class="modal-content">
      <button class="close-button" @click="emit('close')">
        <Icon name="close" />
      </button>
      <div class="modal-header">
        <h2>创建新知识库</h2>
      </div>
      <div class="modal-body">
        <div class="form-item">
          <label for="kb-name">名称</label>
          <input id="kb-name" v-model="name" type="text" placeholder="为你的知识库取个名字" />
        </div>
        <div class="form-item">
          <label for="kb-desc">描述</label>
          <textarea
            id="kb-desc"
            v-model="description"
            placeholder="简单描述一下你的知识库"
            maxlength="50"
          ></textarea>
          <div class="char-count">{{ description.length }}/50</div>
        </div>
        <div class="form-item">
          <label for="embedding-model">嵌入模型</label>
          <select id="embedding-model" v-model="embeddingModel">
            <option value="text-embedding-ada-002">text-embedding-ada-002</option>
            <option value="qwen-text-embedding-v1">qwen-text-embedding-v1</option>
          </select>
        </div>
        <div class="form-item">
          <label for="rerank-model">重排模型</label>
          <select id="rerank-model" v-model="rerankModel">
            <option value="bge-reranker-base">bge-reranker-base</option>
            <option value="cohere-rerank-english-v2.0">cohere-rerank-english-v2.0</option>
          </select>
        </div>
        <div class="separator"></div>
        <div class="setting-item">
          <label>自动设置嵌入维度</label>
          <div class="switch-container">
            <input
              id="auto-dimension-toggle"
              v-model="autoDimension"
              type="checkbox"
              class="switch-input"
            />
            <label for="auto-dimension-toggle" class="switch-label"></label>
          </div>
        </div>
      </div>
      <div class="modal-footer">
        <button class="cancel-button" @click="emit('close')">取消</button>
        <button class="create-button" :disabled="!isFormValid">创建</button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import Icon from '@/components/AppIcon.vue'

const emit = defineEmits(['close'])

const name = ref('')
const description = ref('')
const embeddingModel = ref('text-embedding-ada-002')
const rerankModel = ref('bge-reranker-base')
const autoDimension = ref(true)

const isFormValid = computed(() => {
  return name.value.trim() !== '' && embeddingModel.value !== '' && rerankModel.value !== ''
})
</script>

<style scoped>
/* Modal Layout */
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background-color: var(--bg-overlay);
  display: flex;
  justify-content: center;
  align-items: center;
  z-index: 1000;
  backdrop-filter: blur(8px);
}

.modal-content {
  background-color: var(--modal-bg);
  border-radius: var(--border-radius-large);
  width: 100%;
  max-width: 700px;
  position: relative;
  display: flex;
  flex-direction: column;
  box-shadow: 0 10px 30px rgba(0, 0, 0, 0.5);
}

.close-button {
  position: absolute;
  top: 16px;
  left: 16px;
  background: none;
  border: none;
  color: var(--text-secondary);
  cursor: pointer;
  padding: 8px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 10;
  transition:
    background-color 0.2s,
    color 0.2s;
}
.close-button:hover {
  background-color: var(--bg-tertiary);
  color: var(--text-primary);
}
.close-button :deep(svg) {
  font-size: 20px;
}

.modal-header {
  padding: 24px 24px 16px;
  padding-left: 60px; /* Space for close button */
  border-bottom: 1px solid var(--border-color);
}

.modal-header h2 {
  margin: 0;
  font-size: 1.25em;
  font-weight: 600;
  color: var(--text-primary);
}

.modal-body {
  padding: 24px;
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.modal-footer {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
  padding: 20px 24px;
  border-top: 1px solid var(--border-color);
  background-color: var(--modal-nav-bg);
  border-bottom-left-radius: var(--border-radius-large);
  border-bottom-right-radius: var(--border-radius-large);
}

/* Form Styles */
.form-item {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.form-item label {
  color: var(--text-primary);
  font-weight: 500;
  font-size: 0.9em;
}

.form-item input,
.form-item textarea,
.form-item select {
  width: 100%;
  padding: 10px 12px;
  border-radius: 8px;
  background-color: var(--bg-secondary);
  border: 1px solid var(--border-color);
  color: var(--text-primary);
  font-size: 1em;
}
.form-item input:focus,
.form-item textarea:focus,
.form-item select:focus {
  outline: none;
  border-color: var(--button-primary-bg);
  box-shadow: 0 0 0 2px var(--button-primary-bg-light);
}

.form-item textarea {
  min-height: 80px;
  resize: none;
}

.char-count {
  text-align: right;
  color: var(--text-secondary);
  font-size: 0.8em;
  margin-top: 4px;
}

.separator {
  height: 1px;
  background-color: var(--border-color);
  width: 100%;
  margin: 8px 0;
}

/* Buttons */
.cancel-button,
.create-button {
  border: none;
  padding: 10px 20px;
  border-radius: 8px;
  cursor: pointer;
  font-size: 1em;
  font-weight: 500;
}

.cancel-button {
  background-color: var(--button-secondary-bg);
  color: var(--text-primary);
}
.cancel-button:hover {
  filter: brightness(1.2);
}

.create-button {
  background-color: var(--button-primary-bg);
  color: var(--button-primary-text);
}
.create-button:hover {
  filter: brightness(1.1);
}
.create-button:disabled {
  background-color: var(--button-disabled-bg);
  color: var(--text-disabled);
  cursor: not-allowed;
}

/* Switch from SettingsModal */
.setting-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: 1em;
}

.setting-item label {
  color: var(--text-primary);
  font-weight: 500;
  font-size: 0.9em;
}

.switch-container {
  position: relative;
  width: 44px;
  height: 24px;
}

.switch-input {
  opacity: 0;
  width: 0;
  height: 0;
}

.switch-label {
  position: absolute;
  cursor: pointer;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background-color: var(--switch-bg-off);
  transition: 0.4s;
  border-radius: 34px;
}

.switch-label:before {
  position: absolute;
  content: '';
  height: 20px;
  width: 20px;
  left: 2px;
  bottom: 2px;
  background-color: white;
  transition: 0.4s;
  border-radius: 50%;
}

.switch-input:checked + .switch-label {
  background-color: var(--switch-bg-on);
}

.switch-input:checked + .switch-label:before {
  transform: translateX(20px);
}
</style> 