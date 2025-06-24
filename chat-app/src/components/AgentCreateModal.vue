<template>
  <div class="modal-overlay" @click.self="emit('close')">
    <div class="modal-content">
      <button class="close-button" @click="emit('close')">
        <Icon name="close" />
      </button>
      <div class="modal-header">
        <h2>{{ isEditing ? '编辑Agent' : '创建新Agent' }}</h2>
      </div>
      <div class="modal-body">
        <div class="form-item">
          <label for="agent-name">名称</label>
          <input 
            id="agent-name" 
            v-model="name" 
            type="text" 
            placeholder="为你的Agent取个名字" 
            maxlength="50"
          />
        </div>
        
        <div class="form-item">
          <label for="agent-desc">描述</label>
          <textarea
            id="agent-desc"
            v-model="description"
            placeholder="简单描述一下你的Agent"
            maxlength="200"
          ></textarea>
          <div class="char-count">{{ description.length }}/200</div>
        </div>

        <div class="setting-item">
          <label>启用MCP</label>
          <div class="switch-container">
            <input
              id="mcp-toggle"
              v-model="enableMCP"
              type="checkbox"
              class="switch-input"
            />
            <label for="mcp-toggle" class="switch-label"></label>
          </div>
        </div>

        <div class="form-item">
          <label for="agent-tools">工具</label>
          <textarea
            id="agent-tools"
            v-model="tools"
            placeholder="MCP工具暂时禁用"
            disabled
            class="tools-textarea"
          ></textarea>
          <div class="tools-hint">MCP工具功能暂时禁用</div>
        </div>

        <div class="form-item">
          <label for="agent-prompt">Prompt</label>
          <textarea
            id="agent-prompt"
            v-model="systemPrompt"
            placeholder="输入Agent的系统提示词..."
            class="prompt-textarea"
          ></textarea>
          <div class="char-count">{{ systemPrompt.length }} 字符</div>
        </div>
        
        <!-- 错误消息显示 -->
        <div v-if="errorMessage" class="error-message">
          {{ errorMessage }}
        </div>
      </div>
      <div class="modal-footer">
        <button class="cancel-button" @click="emit('close')" :disabled="isSaving">取消</button>
        <button 
          class="save-button" 
          :disabled="!isFormValid || isSaving" 
          @click="saveAgent"
        >
          <span v-if="isSaving">{{ isEditing ? '保存中...' : '创建中...' }}</span>
          <span v-else>{{ isEditing ? '保存' : '创建' }}</span>
        </button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import Icon from '@/components/AppIcon.vue'
import type { Agent } from '@/api/agentApi'

const props = defineProps<{
  agent?: Agent | null
}>()

const emit = defineEmits<{
  close: []
  save: [agentData: any]
}>()

// 表单数据
const name = ref('')
const description = ref('')
const enableMCP = ref(false)
const tools = ref('')
const systemPrompt = ref('')

// 状态
const isSaving = ref(false)
const errorMessage = ref('')

// 计算属性
const isEditing = computed(() => !!props.agent)

const isFormValid = computed(() => {
  return name.value.trim() !== '' && systemPrompt.value.trim() !== ''
})

// 初始化表单数据
onMounted(() => {
  if (props.agent) {
    name.value = props.agent.name
    description.value = props.agent.description
    enableMCP.value = props.agent.enable_MCP
    tools.value = props.agent.tools
    systemPrompt.value = props.agent.system_prompt
  }
})

// 保存Agent
async function saveAgent() {
  if (!isFormValid.value || isSaving.value) return
  
  isSaving.value = true
  errorMessage.value = ''
  
  try {
    const agentData = {
      name: name.value.trim(),
      description: description.value.trim(),
      enable_MCP: enableMCP.value,
      tools: tools.value.trim(),
      system_prompt: systemPrompt.value.trim()
    }
    
    emit('save', agentData)
  } catch (error) {
    console.error('保存Agent时出错:', error)
    errorMessage.value = '保存Agent时发生错误'
    isSaving.value = false
  }
}
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
  max-height: 90vh;
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
  transition: background-color 0.2s, color 0.2s;
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
  padding-left: 60px;
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
  overflow-y: auto;
  flex: 1;
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
.form-item textarea {
  width: 100%;
  padding: 10px 12px;
  border-radius: 8px;
  background-color: var(--bg-secondary);
  border: 1px solid var(--border-color);
  color: var(--text-primary);
  font-size: 1em;
  font-family: inherit;
}

.form-item input:focus,
.form-item textarea:focus {
  outline: none;
  border-color: var(--button-primary-bg);
  box-shadow: 0 0 0 2px var(--button-primary-bg-light);
}

.form-item textarea {
  min-height: 80px;
  resize: none;
}

.tools-textarea {
  min-height: 60px;
  resize: none;
  opacity: 0.6;
  cursor: not-allowed;
}

.prompt-textarea {
  min-height: 120px;
  font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', monospace;
  font-size: 0.9em;
  line-height: 1.5;
  resize: none;
}

.char-count {
  text-align: right;
  color: var(--text-secondary);
  font-size: 0.8em;
  margin-top: 4px;
}

.tools-hint {
  color: var(--text-secondary);
  font-size: 0.8em;
  margin-top: 4px;
}

/* Setting Item (Switch) */
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

/* Buttons */
.cancel-button,
.save-button {
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

.save-button {
  background-color: var(--button-primary-bg);
  color: var(--button-primary-text);
}

.save-button:hover {
  filter: brightness(1.1);
}

.save-button:disabled {
  background-color: var(--button-disabled-bg);
  color: var(--text-disabled);
  cursor: not-allowed;
}

/* Error Message */
.error-message {
  color: var(--text-error);
  font-size: 0.8em;
  margin-top: 8px;
}
</style>
