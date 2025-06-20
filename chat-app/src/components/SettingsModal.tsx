import React, { useState } from 'react';
import { CloseIcon, SettingsIcon, DataManagementIcon } from './icons';

// 定义 Props 类型
interface SettingsModalProps {
    isOpen: boolean;
    onClose: () => void;
}

// 定义激活标签页的类型，以增强类型安全
type ActiveTab = 'general' | 'data';

/**
 * @description
 * 设置模态框组件。
 */
export const SettingsModal = ({ isOpen, onClose }: SettingsModalProps) => {
    // 内部状态，用于管理当前激活的标签页，并明确其类型
    const [activeTab, setActiveTab] = useState<ActiveTab>('general');

    if (!isOpen) {
        return null;
    }

    // ... 其余渲染逻辑与之前相同，但现在使用 TSX ...
    // 为简洁起见，此处不再重复，其内部结构不变。
    // 您只需将之前的 SettingsModal.jsx 内容复制过来，并确保文件名是 .tsx 即可。
    // React 会自动处理 JSX 到 TSX 的转换。
    // 关键是 props 和 state 的类型定义已经完成。
    const renderGeneralSettings = () => (
        <div className="flex-1 p-6 text-gray-800">
            <h2 className="text-lg font-semibold mb-6">通用设置</h2>
            <div className="space-y-4">
                <div className="flex items-center justify-between">
                    <label htmlFor="suggestions" className="text-sm text-gray-700">在聊天中显示跟进建议</label>
                    <div className="relative inline-block w-10 mr-2 align-middle select-none transition duration-200 ease-in">
                        <input type="checkbox" name="toggle" id="suggestions" defaultChecked className="toggle-checkbox absolute block w-6 h-6 rounded-full bg-white border-4 appearance-none cursor-pointer peer" />
                        <label htmlFor="suggestions" className="toggle-label block overflow-hidden h-6 rounded-full bg-gray-300 peer-checked:bg-blue-500 cursor-pointer"></label>
                    </div>
                </div>
                <div className="flex items-center justify-between">
                    <span className="text-sm text-gray-700">语言</span>
                    <button className="text-sm text-gray-500 hover:text-gray-800">自动检测 ▼</button>
                </div>
                <div className="flex items-center justify-between">
                    <span className="text-sm text-gray-700">已归档的聊天</span>
                    <button className="px-3 py-1 text-sm border rounded-md hover:bg-gray-100">管理</button>
                </div>
                <div className="flex items-center justify-between">
                    <span className="text-sm text-gray-700">归档所有聊天</span>
                    <button className="px-3 py-1 text-sm border rounded-md hover:bg-gray-100">全部归档</button>
                </div>
                <div className="flex items-center justify-between">
                    <span className="text-sm text-gray-700">删除所有聊天</span>
                    <button className="px-3 py-1 text-sm border rounded-md text-red-600 border-red-200 hover:bg-red-50">全部删除</button>
                </div>
                <div className="flex items-center justify-between">
                    <span className="text-sm text-gray-700">注销设备</span>
                    <button className="px-3 py-1 text-sm border rounded-md hover:bg-gray-100">注销</button>
                </div>
            </div>
        </div>
    );

    const renderDataSettings = () => (
        <div className="flex-1 p-6 text-gray-800">
            <h2 className="text-lg font-semibold mb-6">数据管理</h2>
            <div className="space-y-4">
                <div className="flex items-center justify-between">
                    <span className="text-sm text-gray-700">为所有用户改进模型</span>
                    <button className="text-sm text-blue-600 hover:underline">开 </button>
                </div>
                <div className="flex items-center justify-between">
                    <span className="text-sm text-gray-700">共享链接</span>
                    <button className="px-3 py-1 text-sm border rounded-md hover:bg-gray-100">管理</button>
                </div>
                <div className="flex items-center justify-between">
                    <span className="text-sm text-gray-700">导出数据</span>
                    <button className="px-3 py-1 text-sm border rounded-md hover:bg-gray-100">导出</button>
                </div>
                <div className="flex items-center justify-between">
                    <span className="text-sm text-gray-700">删除帐户</span>
                    <button className="px-3 py-1 text-sm border rounded-md text-red-600 border-red-200 hover:bg-red-50">删除</button>
                </div>
            </div>
        </div>
    );

    return (
        <div
            className="fixed inset-0 z-50 flex items-center justify-center bg-black bg-opacity-40 backdrop-blur-sm"
            onClick={onClose}
        >
            <div
                className="relative bg-white w-full max-w-3xl rounded-lg shadow-xl flex overflow-hidden"
                onClick={(e) => e.stopPropagation()}
            >
                <button onClick={onClose} className="absolute top-4 right-4 text-gray-400 hover:text-gray-600">
                    <CloseIcon className="w-5 h-5" />
                </button>

                <div className="w-1/4 bg-gray-50 border-r border-gray-200 p-4 space-y-2">
                    <button
                        onClick={() => setActiveTab('general')}
                        className={`w-full text-left text-sm p-2 rounded-md flex items-center gap-3 ${activeTab === 'general' ? 'bg-gray-200 text-gray-800 font-semibold' : 'text-gray-600 hover:bg-gray-100'}`}
                    >
                        <SettingsIcon className="w-4 h-4 text-gray-500" />
                        通用设置
                    </button>
                    <button
                        onClick={() => setActiveTab('data')}
                        className={`w-full text-left text-sm p-2 rounded-md flex items-center gap-3 ${activeTab === 'data' ? 'bg-gray-200 text-gray-800 font-semibold' : 'text-gray-600 hover:bg-gray-100'}`}
                    >
                        <DataManagementIcon className="w-4 h-4 text-gray-500" />
                        数据管理
                    </button>
                </div>

                {activeTab === 'general' ? renderGeneralSettings() : renderDataSettings()}
            </div>
        </div>
    );
};