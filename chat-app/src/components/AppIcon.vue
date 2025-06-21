<template>
    <span class="icon-wrapper" v-html="iconSvg"></span>
</template>

<script setup lang="ts">
import { computed } from 'vue';

const props = defineProps<{
  name: string;
}>();

// 使用 Vite 的 glob 导入功能，将所有 SVG 作为原始文本导入
const icons = import.meta.glob('../assets/icons/*.svg', { query: '?raw', import: 'default', eager: true });

const iconSvg = computed(() => {
  const path = `../assets/icons/${props.name}.svg`;
  return icons[path] || ''; // 如果找不到图标，返回空字符串
});
</script>

<style scoped>
.icon-wrapper {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  color: inherit; /* 继承父元素的颜色 */
}

/* 通过 v-html 插入的 SVG 会被这个选择器影响 */
.icon-wrapper :deep(svg) {
  width: 1em; /* 设置宽度为1em，使其大小可以被 font-size 控制 */
  height: 1em; /* 设置高度为1em */
  fill: currentColor; /* 使 SVG 颜色与文本颜色一致 */
}
</style>