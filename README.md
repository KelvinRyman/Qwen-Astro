# RAG 知识库系统

这是一个基于检索增强生成 (RAG) 的知识库系统，包含前端和后端组件。

## 功能特性

- 创建和管理知识库组
- 上传文件（支持多种格式）
- 添加网页URL进行索引
- **智能路由系统**：支持三种互斥的对话模式
  - **RAG模式**：基于知识库的智能问答
  - **联网模式**：实时网页搜索 + 深度思考
  - **普通模式**：标准对话（无RAG无联网）
- **深度思考功能**：使用reasoning_effort参数提升回答质量
- **网页搜索功能**：使用Google Search API获取实时信息
- 实时状态更新（文件和网页处理状态）
- Agent系统：自定义AI助手角色

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
- **智能路由引擎**：
  - OpenAI库：普通对话模式
  - Google GenAI库：联网搜索和深度思考模式
  - 自动模式切换和参数传递

## 环境配置

### 环境变量设置

创建 `.env` 文件并配置以下环境变量：

```bash
# 必需的API密钥
API_KEY=your_gemini_api_key_here

# 可选的模型配置
MODEL_NAME=gemini-pro
EMBEDDING_API_KEY=your_embedding_api_key
EMBEDDING_MODEL_NAME=text-embedding-ada-002
EMBEDDING_API_BASE_URL=your_embedding_api_base_url

# Flask配置
FLASK_HOST=0.0.0.0
FLASK_PORT=5000
FLASK_DEBUG=False
```

## 开发指南

### 安装依赖

```bash
# 使用pip安装后端依赖
pip install -r requirements.txt

# 或者使用uv安装后端依赖（推荐）
uv pip install -r requirements.txt

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
- `POST /api/conversations/{conversation_id}/messages` - 发送消息（支持智能路由）
  - 新增参数：
    - `enable_deep_thinking`: 布尔值，是否启用深度思考
    - `enable_web_search`: 布尔值，是否启用网页搜索
- `POST /api/conversations/{conversation_id}/messages/stream` - 流式发送消息
- `DELETE /api/conversations/{conversation_id}` - 删除对话

## 智能路由系统使用说明

### 三种对话模式

1. **RAG模式**（知识库问答）
   - 选择知识库组后自动启用
   - 基于上传的文档和网页进行问答
   - 提供引用来源信息

2. **联网模式**（实时搜索）
   - 点击"搜索网页"工具启用
   - 使用Google Search API获取实时信息
   - 可配合深度思考功能使用

3. **普通模式**（标准对话）
   - 默认模式，无需特殊设置
   - 直接与AI模型对话
   - 可启用深度思考功能提升回答质量

### 互斥逻辑

- 启用RAG → 自动关闭联网和深度思考选项
- 启用联网/深度思考 → 自动清除知识库选择
- 前端UI会自动处理选项的互斥状态

## 实时状态更新

系统实现了自动轮询机制，可以实时更新文件和网页的处理状态：

1. 当用户上传文件或添加网页时，系统自动启动轮询
2. 轮询会定期检查所有处理中的资源状态
3. 当所有资源处理完成后，轮询自动停止
4. 用户界面会显示处理中资源的数量和状态
