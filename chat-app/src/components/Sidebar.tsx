import React from 'react';
import {
    NewChatIcon,
    SidebarIcon,
    SearchIcon,
    KnowledgeIcon,
    AgentsIcon,
    SettingsIcon,
} from './icons';

// 定义组件的 props 类型
interface SidebarProps {
    isOpen: boolean;
    onToggle: () => void;   // 用于切换侧边栏的展开/收起状态
    onOpenSettings: () => void;
}

/**
 * @description
 * 侧边栏导航组件。
 * - `onOpenSettings`: 点击设置按钮时触发的回调函数。
 */
export const Sidebar = ({ isOpen, onToggle, onOpenSettings }: SidebarProps) => {
    const itemVisiblityClass = `
        transition-all duration-200 ease-in-out
        ${isOpen ? 'opacity-100 translate-x-0' : 'opacity-0 -translate-x-4 pointer-events-none'}
    `;
    return (
        <div className="w-64 bg-white border-r border-gray-200 flex flex-col h-full p-2">
            {/* 侧边栏顶部 */}
            <div className="flex items-center justify-between p-2 mb-4">
                <button className="p-2 rounded-lg hover:bg-gray-100">
                    <SidebarIcon className="w-5 h-5 text-gray-600" />
                </button>
            </div>

            {/* 搜索框 */}
            <div className="relative mb-4 px-2">
                <div className="absolute inset-y-0 left-0 pl-5 flex items-center pointer-events-none">
                    <SearchIcon className="w-4 h-4 text-gray-400" />
                </div>
                <input
                    type="text"
                    placeholder="搜索聊天"
                    className="w-full bg-gray-100 border-none rounded-lg pl-9 pr-3 py-2 text-sm focus:ring-2 focus:ring-blue-500"
                />
            </div>

            {/* 导航链接 */}
            <nav className="px-2 space-y-1 mb-4">
                <a href='#' className="flex items-center gap-3 p-2 rounded-lg hover:bg-gray-100 text-sm text-gray-700">
                    <NewChatIcon className="w-5 h-5 text-gray-500" />
                    新聊天
                </a>
                <a href="#" className="flex items-center gap-3 p-2 rounded-lg hover:bg-gray-100 text-sm text-gray-700">
                    <KnowledgeIcon className="w-5 h-5 text-gray-500" />
                    知识库
                </a>
                <a href="#" className="flex items-center gap-3 p-2 rounded-lg hover:bg-gray-100 text-sm text-gray-700">
                    <AgentsIcon className="w-5 h-5 text-gray-500" />
                    Agent
                </a>
            </nav>

            {/* 聊天记录区域 */}
            <div className="flex-grow"></div>

            {/* 侧边栏底部 */}
            <div className="p-2">
                <button
                    onClick={onOpenSettings}
                    className="w-full flex items-center gap-3 p-2 rounded-lg hover:bg-gray-100 text-sm text-gray-700"
                >
                    <SettingsIcon className="w-5 h-5 text-gray-500" />
                    设置
                </button>
            </div>
        </div>
    );
};