# 基于RAG 系统的太空探索与天文科普平台

这是一个基于检索增强生成 (RAG) 的知识库系统，包含前端和后端组件。

## 功能特性

- 创建和管理知识库组
- 上传文件（支持多种格式）
- 添加网页URL进行索引
- 基于知识库的智能问答
- 支持普通对话和RAG对话
- 实时状态更新（文件和网页处理状态）

## 技术栈

### 前端
- Vue.js 3 + TypeScript
- Pinia 状态管理
- Axios 用于API请求

### 后端
- Flask RESTful API
- Flask-CORS 处理跨域请求
- ChromaDB 向量数据库
- LlamaIndex 用于文档处理和检索

## 开发指南

### 安装依赖

```bash
# 使用pip安装后端依赖
pip install -r requirements.txt

# 或者使用uv安装后端依赖（推荐），若未安装uv，请先安装pipx
pipx install uv
# 创建并激活虚拟环境并安装项目依赖
uv sync

# 安装前端依赖
cd chat-app
npm install
```

### 运行开发服务器

在 `Windows` 平台。
```powershell
$env:FLASK_APP="backend.app"
flask run
```

在 `Linux` 或 `macOS` 平台。
```bash
export FLASK_APP="backend.app"
flask run

# 运行前端开发服务器
cd chat-app
npm run dev
```

### 使用uv运行项目

```bash
# 安装uv（如果尚未安装）
pipx install uv

# 创建并激活虚拟环境并安装项目依赖
uv sync

# 运行项目
$env:FLASK_APP="backend.app"  # Windows
export FLASK_APP="backend.app"  # Linux/macOS
flask run
```

## API文档

### 知识库管理
- `GET /api/groups` - 获取所有知识库组
- `POST /api/groups` - 创建新知识库组
- `DELETE /api/groups/{group_id}` - 删除知识库组

### 文件和网页管理
- `POST /api/groups/{group_id}/files` - 上传文件
- `POST /api/groups/{group_id}/webpages` - 添加网页
- `GET /api/groups/{group_id}/sources` - 获取组内所有资源
- `GET /api/groups/{group_id}/files/{file_id}` - 获取文件状态
- `GET /api/groups/{group_id}/webpages/{webpage_id}` - 获取网页状态
- `DELETE /api/groups/{group_id}/files` - 删除文件
- `DELETE /api/groups/{group_id}/webpages` - 删除网页

### 对话管理
- `POST /api/conversations` - 创建新对话
- `GET /api/conversations` - 获取所有对话
- `GET /api/conversations/{conversation_id}` - 获取特定对话
- `POST /api/conversations/{conversation_id}/messages` - 发送消息
- `DELETE /api/conversations/{conversation_id}` - 删除对话

## 实时状态更新

系统实现了自动轮询机制，可以实时更新文件和网页的处理状态：

1. 当用户上传文件或添加网页时，系统自动启动轮询

2. 轮询会定期检查所有处理中的资源状态

3. 当所有资源处理完成后，轮询自动停止

4. 用户界面会显示处理中资源的数量和状态

   

## 代码文件说明

### 1. 项目根目录

- main.py：入口脚本
- qwen_search.py：示例脚本，演示如何通过 Google 搜索+网页爬取+Ollama 本地大模型进行联网问答。
- rag.py：RAG主流程脚本，通常用于命令行测试或批量处理，调用RAG引擎进行检索与生成。
- requirements.txt：后端Python依赖列表。

### 2. 后端API与业务逻辑

- app.py：Flask应用主入口，负责应用初始化、CORS配置、日志设置、RAG引擎实例化、API蓝图注册。
- config.py：后端配置文件，定义后端服务参数。
- models.py：定义后端API的数据模型，如知识库组、文件、网页、对话、消息等的数据结构和校验。
- routes.py：Flask API路由定义，包含所有RESTful接口的实现（知识库管理、文件/网页上传、对话管理、消息流式响应等）。

### 3. RAG核心引擎

- *init*_.py：包初始化文件。
- setup.py：Python包配置与安装脚本。
- components.py：RAG引擎的组件初始化与全局配置，包括大模型、嵌入模型、向量存储等的统一设置。
- config.py：RAG引擎的核心配置，包括数据路径、模型参数、向量数据库参数、Prompt模板等。
- conversation_manager.py：对话历史与上下文管理，负责多轮对话的消息存储与检索。
- data_processor.py：数据处理模块，负责文件/网页的文本提取、分块、清洗、元数据生成等。
- group_manager.py：知识库分组管理，负责知识库组的创建、删除、元数据管理、物理目录管理等。
- rag_pipeline.py：RAG主流程管道，负责数据入库、向量化、检索、生成、知识库组操作等核心业务逻辑。
- utils.py：工具函数集合，如路径处理、文件操作、辅助功能等。

### 4. 前端Vue3项目

- index.html：前端SPA入口HTML文件。
- vite.config.ts：Vite前端构建工具配置。
- tsconfig.json / tsconfig.app.json / tsconfig.node.json：TypeScript编译配置。
- package.json / package-lock.json：前端依赖与脚本管理。
- main.ts：Vue应用入口，挂载根组件。
- App.vue：根组件，定义应用主结构。
- chatApi.ts、knowledgeBaseApi.ts：前端API请求封装，前端API请求封装。
- components/AppIcon.vue：通用图标组件。根据传入的 name 属性渲染不同的SVG图标，统一管理项目内所有图标的显示。
- components/AppSidebar.vue：应用侧边栏组件。负责显示导航菜单、会话列表、知识库入口、设置入口等，支持折叠、展开、重命名会话等操作。
- components/ItemDropdownMenu.vue：通用下拉菜单组件。用于会话、知识库等列表项的操作菜单（如重命名、删除等）。
- components/KnowledgeBaseSelectModal.vue：知识库选择弹窗。用于在聊天时选择关联的知识库组，支持多选、确认、取消等操作。
- components/SearchModal.vue：全局搜索弹窗。用于在对话、知识库等范围内进行内容搜索，支持输入、结果展示等。
- components/SettingsModal.vue设置弹窗。用于展示和修改应用的全局设置，如主题、语言、数据管理、模型配置等。
- components/TheWelcome.vue：欢迎页主组件。用于展示应用的欢迎信息、快速入口、项目介绍等。
- components/icons：用于在欢迎页或设置页中展示不同的功能标签和入口。
- knowledge-base/AddKnowledgeBaseModal.vue：新建知识库弹窗。用于输入知识库名称、描述、选择嵌入模型等，支持表单校验和创建操作。
- knowledge-base/FileItem.vue：文件项组件。用于知识库内容列表中展示单个文件的名称、状态、操作按钮。
- knowledge-base/KnowledgeContent.vue：知识库内容主展示组件。负责展示知识库内的所有文件、网页、处理状态、模型信息等，支持内容刷新、搜索等操作。
- knowledge-base/KnowledgeGroupList.vue：知识库分组列表组件。用于左侧栏展示所有知识库组，支持切换、重命名、删除、添加等操作。
- knowledge-base/KnowledgeSearchModal.vue：知识库内搜索弹窗。用于在当前知识库内进行内容检索，展示搜索结果。
- knowledge-base/WebpageItem.vue：网页项组件。用于知识库内容列表中展示单个网页的URL、状态、操作按钮（如删除、预览等）。
- src/views/：页面级组件（如ChatView.vue聊天页、KnowledgeBaseView.vue知识库页、AboutView.vue关于页等）。
- src/stores/：Pinia状态管理（如chat.ts聊天状态、knowledgeBase.ts知识库状态）。
- src/router/：路由配置（index.ts）。
- src/utils/：前端工具函数。

### 5. Qwen-Astro/archive/（数据归档）

- nasa_apod_explanations.zip：用于知识库初始化或测试。
- nasa_hubble_chunks.zip：用于知识库初始化或测试。
- nasa_news_chunks.zip：用于知识库初始化或测试。
- wikipedia_chunks.zip：用于知识库初始化或测试。

## 总结

- 后端/backend/ 负责API服务、业务逻辑、数据模型、RAG引擎调用。
- rag_engine/ 负责RAG核心流程、数据处理、知识库与对话管理、模型配置。
- chat-app/ 负责前端界面、用户交互、状态管理、API通信。
- archive/ 提供示例数据。
- 根目录脚本 提供命令行工具、说明文档、依赖管理。