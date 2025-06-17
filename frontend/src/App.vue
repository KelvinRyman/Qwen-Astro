<template>
  <el-container class="app-container">
    <el-header>
      <h1>智能问答系统-问天</h1>
    </el-header>
    
    <el-main>
      <router-view></router-view>
    </el-main>
  </el-container>
</template>

<script setup>
import { ElContainer, ElHeader, ElMain } from 'element-plus'
</script>

<style>
@import './assets/styles/main.css';

/* 全局样式 */
html {
  scroll-behavior: smooth;
}

body {
  margin: 0;
  font-family: var(--font-body);
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
}

/* 自定义滚动条 */
::-webkit-scrollbar {
  width: 8px;
}

::-webkit-scrollbar-track {
  background: var(--primary-dark);
}

::-webkit-scrollbar-thumb {
  background: var(--accent-purple);
  border-radius: 4px;
}

::-webkit-scrollbar-thumb:hover {
  background: var(--accent-gold);
}
</style>

<style scoped>
.app-container {
  min-height: 100vh;
}

.el-header {
  background-color: transparent;
  color: var(--text-white);
  text-align: center;
  line-height: 60px;
  padding: 0;
}

.el-main {
  padding: 20px;
  background-color: transparent;
}
</style> 