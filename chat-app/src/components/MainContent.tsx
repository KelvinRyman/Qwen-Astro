import React, { useState, useRef, useEffect, useCallback } from 'react';
import { MicrophoneIcon, PlusIcon, ToolsIcon, SendIcon } from './icons';

/**
 * @description
 * 主内容区域组件，包含欢迎信息和聊天输入框。
 * 支持多行、自适应的文本框。
 */
export const MainContent = () => {
    // 状态：用于管理 textarea 的输入值
    const [text, setText] = useState<string>('');

    // Ref: 用于获取 textarea DOM 节点的引用，以便测量其内容高度
    const textareaRef = useRef<HTMLTextAreaElement>(null);

    /**
     * @description
     * 这是一个副作用 Hook，它会在 `text` 状态变化时运行。
     * 这是实现自适应高度的最佳实践。
     */
    useEffect(() => {
        const textarea = textareaRef.current;
        if (textarea) {
            // 1. 先将高度重置为 auto，让元素根据内容自然收缩
            textarea.style.height = 'auto';
            // 2. 然后将高度设置为内容的实际滚动高度，实现“撑高”效果
            textarea.style.height = `${textarea.scrollHeight}px`;
        }
    }, [text]); // 依赖项数组中只有 text，确保仅在文本变化时执行

    /**
     * @description
     * 处理 textarea 输入变化的回调函数。
     * 使用 useCallback 进行性能优化，防止不必要地重新创建函数。
     */
    const handleInputChange = useCallback((e: React.ChangeEvent<HTMLTextAreaElement>) => {
        setText(e.target.value);
    }, []);

    return (
        <div className="flex-1 flex flex-col bg-[#F9F9F9]">
            <main className="flex-1 flex items-center justify-center">
                <div className="text-center">
                    {/* 当输入框有内容时，可以考虑隐藏此欢迎信息 */}
                    {text.length === 0 && (
                        <h1
                            className="text-6xl text-gray-700"
                            style={{ fontFamily: "'Times New Roman', 'Instrument Serif', serif" }}
                        >
                            Per aspera ad astra.
                        </h1>
                    )}
                </div>
            </main>

            {/* 底部输入区域 */}
            <footer className="p-4">
                <div className="max-w-3xl mx-auto">
                    {/* 
            主输入框容器。
            - 使用 flex-col 实现文本框和按钮的上下两行布局。
            - 保持了完美的圆角和内边距。
          */}
                    <div className="flex flex-col w-full bg-white border border-gray-200 rounded-[28px] shadow-sm p-2.5">
                        {/* 
              第一行：自适应高度的文本输入框 
              - `resize-none`: 禁用手动拖拽调整大小。
              - `max-h-52`: (13rem 或 208px) 设置最大高度，约10行，超出后将不再增高。
              - `overflow-y-auto`: 当内容超出 max-h 时，自动显示垂直滚动条。
            */}
                        <textarea
                            ref={textareaRef}
                            value={text}
                            onChange={handleInputChange}
                            placeholder="询问任何问题"
                            rows={1} // 初始行数为1
                            className="w-full resize-none border-0 bg-transparent px-2 py-2.5 focus:outline-none focus:ring-0 text-gray-800 placeholder-gray-400 overflow-y-auto"
                            style={{ maxHeight: '13rem' }} // 直接使用 style 或 Tailwind class `max-h-52`
                        />

                        {/* 第二行：操作按钮栏 */}
                        <div className="flex justify-between items-center mt-2">
                            {/* 左侧操作按钮组 */}
                            <div className="flex items-center gap-1.5">
                                <button
                                    type="button"
                                    className="p-2 rounded-full hover:bg-gray-100 text-gray-600"
                                    aria-label="添加文件"
                                >
                                    <PlusIcon className="w-5 h-5" />
                                </button>
                                <button
                                    type="button"
                                    className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-gray-100 hover:bg-gray-200 text-sm text-gray-800 font-medium"
                                    aria-label="选择工具"
                                >
                                    <ToolsIcon className="w-5 h-5" />
                                    <span>工具</span>
                                </button>
                                <button
                                    type="button"
                                    className="px-3 py-1.5 rounded-lg bg-gray-100 hover:bg-gray-200 text-sm text-gray-800 font-medium"
                                    aria-label="MCP 设置"
                                >
                                    MCP
                                </button>
                            </div>

                            {/* 右侧操作按钮组 */}
                            <div className="flex items-center gap-1.5">
                                <button
                                    type="button"
                                    className="p-2 rounded-full hover:bg-gray-100 text-gray-600"
                                    aria-label="听写按钮"
                                >
                                    <MicrophoneIcon className="w-5 h-5" />
                                </button>
                                <button
                                    type="button"
                                    className="flex items-center justify-center bg-black text-white rounded-full h-9 w-9 hover:opacity-80 transition-opacity"
                                    aria-label="发送"
                                >
                                    <SendIcon className="w-5 h-5" />
                                </button>
                            </div>
                        </div>
                    </div>
                </div>
            </footer>
        </div>
    );
};