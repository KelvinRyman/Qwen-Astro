<template>
  <div class="dropdown-container" v-click-outside="handleClose">
    <button class="more-button" @click.stop="$emit('toggle')">
      <Icon name="more" />
    </button>
    <transition name="fade-in">
      <div v-if="isOpen" class="dropdown-menu">
        <button class="dropdown-item" @click.stop="$emit('rename')">
          <Icon name="edit" />
          <span>重命名</span>
        </button>
        <button class="dropdown-item delete" @click.stop="$emit('delete')">
          <Icon name="delete" />
          <span>删除</span>
        </button>
      </div>
    </transition>
  </div>
</template>

<script setup lang="ts">
import Icon from '@/components/AppIcon.vue'

const props = defineProps<{
  isOpen: boolean
}>()

const emit = defineEmits(['toggle', 'close', 'rename', 'delete'])

const handleClose = () => {
  if (props.isOpen) {
    emit('close')
  }
}

// 自定义指令：点击外部关闭菜单
const vClickOutside = {
  mounted(el: HTMLElement, binding: any) {
    const element = el as HTMLElement & {
      _clickOutside?: (event: MouseEvent) => void
    }

    element._clickOutside = (event: MouseEvent) => {
      if (!(el === event.target || el.contains(event.target as Node))) {
        binding.value(event)
      }
    }
    document.addEventListener('click', element._clickOutside, true) // Use capture phase
  },
  unmounted(el: HTMLElement) {
    const element = el as HTMLElement & {
      _clickOutside?: (event: MouseEvent) => void
    }

    if (element._clickOutside) {
      document.removeEventListener('click', element._clickOutside, true)
    }
  }
}
</script>

<style scoped>
.dropdown-container {
  position: relative;
}

.more-button {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 28px;
  height: 28px;
  border-radius: 6px;
  background: transparent;
  border: none;
  color: var(--text-secondary);
  cursor: pointer;
}

.more-button:hover {
  background-color: var(--bg-tertiary);
  color: var(--text-primary);
}

.more-button :deep(svg) {
  font-size: 18px;
}

.dropdown-menu {
  position: absolute;
  top: calc(100% + 4px);
  right: 0;
  width: 120px;
  background-color: var(--modal-bg);
  border-radius: var(--border-radius-medium);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3);
  z-index: 100;
  overflow: hidden;
  padding: 4px;
}

.dropdown-item {
  display: flex;
  align-items: center;
  gap: 8px;
  width: 100%;
  padding: 10px 12px;
  border: none;
  background: transparent;
  color: var(--text-primary);
  text-align: left;
  cursor: pointer;
  font-size: 14px;
  border-radius: 6px;
}

.dropdown-item:hover {
  background-color: var(--bg-tertiary);
}

.dropdown-item.delete {
  color: var(--text-danger);
}

.dropdown-item.delete:hover {
  background-color: rgba(237, 94, 88, 0.1);
}

.dropdown-item.delete :deep(svg) {
  color: var(--text-danger);
  font-size: 16px;
}
.dropdown-item :deep(svg) {
  font-size: 16px;
}

/* Animation */
.fade-in-enter-active,
.fade-in-leave-active {
  transition:
    opacity 0.2s ease,
    transform 0.2s ease;
}
.fade-in-enter-from,
.fade-in-leave-to {
  opacity: 0;
  transform: translateY(-5px);
}
</style> 