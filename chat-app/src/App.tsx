import React, { useState, useCallback } from 'react';
import { Sidebar } from './components/Sidebar';
import { MainContent } from './components/MainContent';
import { SettingsModal } from './components/SettingsModal';
import { SidebarIcon } from './components/icons';

/**
 * @description
 * 应用的主组件，负责整体布局和状态管理。
 * - 使用 `useState<boolean>` 管理设置模态框的打开/关闭状态。
 * - 使用 `useCallback` 包装 toggle 函数以进行性能优化。
 * - 使用 `isSidebarOpen` 状态来控制侧边栏的显示。
 */
function App() {
  // 状态：控制设置模态框是否可见，并明确其类型为布尔值
  const [isModalOpen, setModalOpen] = useState<boolean>(false);

  // 状态：控制侧边栏是否展开，默认为展开
  const [isSidebarOpen, setSidebarOpen] = useState<boolean>(true);

  // 函数：使用 useCallback 进行记忆化，防止不必要的重渲染
  const handleToggleSettingsModal = useCallback(() => {
    setModalOpen(prev => !prev);
  }, []);

  // 回调：用于展开或收起侧边栏
  const handleToggleSidebar = useCallback(() => {
    setSidebarOpen(prev => !prev);
  }, []);

  return (
    <div className="flex h-screen w-screen overflow-hidden bg-gray-100">
      {/* 
        侧边栏容器。
        - 使用 isSidebarOpen 状态动态切换宽度。
        - `transition-all` 和 `duration-300` 启用流畅的宽度变化动画。
        - `flex-shrink-0` 防止侧边栏在屏幕缩小时被压缩。
      */}
      <div
        className={`
          flex-shrink-0 bg-white border-r border-gray-200 
          transition-all duration-300 ease-in-out
          ${isSidebarOpen ? 'w-64' : 'w-16'}
        `}
      >
        <Sidebar
          isOpen={isSidebarOpen}
          onToggle={handleToggleSidebar}
          onOpenSettings={handleToggleSettingsModal}
        />
      </div>

      {/* 主内容区 */}
      <MainContent />

      {/* 设置模态框 */}
      <SettingsModal isOpen={isModalOpen} onClose={handleToggleSettingsModal} />
    </div>
  );
}

export default App;