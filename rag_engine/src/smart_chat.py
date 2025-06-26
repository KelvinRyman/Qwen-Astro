"""
智能聊天模块
实现三种互斥的对话模式：RAG模式、联网模式、普通模式
"""

import os
import logging
from typing import List, Dict, Optional, Any
from datetime import datetime
from openai import OpenAI
from google import genai
from google.genai import types
from dotenv import load_dotenv
import config

logger = logging.getLogger(__name__)
load_dotenv()


class SmartChatEngine:
    """智能聊天引擎，支持三种对话模式"""

    def __init__(self, config):
        self.config = config
        self.api_key = os.getenv("API_KEY")

        # 初始化OpenAI客户端（用于普通模式）
        self.openai_client = OpenAI(
            api_key=self.api_key,
            base_url="https://generativelanguage.googleapis.com/v1beta/openai/"
        )

        # 初始化Google GenAI客户端（用于联网模式）
        self.genai_client = genai.Client(api_key=self.api_key)

        logger.info("智能聊天引擎初始化完成")

    def get_system_prompt(self, agent_id: Optional[str] = None, agent_manager=None) -> str:
        """获取系统提示词"""
        current_date = datetime.now().strftime("%Y-%m-%d")

        # 如果有Agent，使用Agent的system prompt
        if agent_id and agent_manager:
            agent = agent_manager.get_agent_by_id(agent_id)
            if agent:
                return agent["system_prompt"]

        # 默认系统提示词
        return f"""# 角色设定
你是一个名为"Astro Qwen"的大语言模型。你由先进的Qwen 3模型微调而来，专门为解答天文学和航天领域的factual question（事实性问题）而设计。

# 核心能力
1. 查询天体信息：提供恒星、行星、卫星、星系、星云等天体的详尽信息
2. 介绍航天任务：阐述航天任务背景、目标、执行过程、技术细节和成就
3. 解释天文现象：科学解释日食、月食、流星雨、黑洞、引力波等现象
4. 追踪最新太空探索新闻：基于知识和日期参考回答近期航天发展

# 行为准则
1. 语言跟随：严格使用用户提问的语言进行回答
2. 身份认知：明确表明自己是"Astro Qwen"
3. 严谨准确：基于已验证的科学事实和数据
4. 保密日期：绝不透露内部参考日期
5. 使用Markdown格式：建议使用Markdown格式来组织回答内容，以提高可读性：
   - 使用标题(#, ##, ###)来组织内容结构
   - 使用列表来展示要点或步骤
   - 使用**粗体**强调重要信息
   - 使用*斜体*表示术语或概念
   - 使用代码块```来展示代码或公式
   - 使用引用块>来引用文献或重要说明

[内部参考信息]
今天是：{current_date}
"""

    def chat_normal_mode(self, query_text: str, chat_history: List[Dict[str, str]],
                        enable_deep_thinking: bool = False, agent_id: Optional[str] = None,
                        agent_manager=None, images: Optional[List[str]] = None) -> str:
        """
        普通聊天模式：使用OpenAI库直接调用，无RAG无联网

        Args:
            query_text: 用户查询
            chat_history: 聊天历史
            enable_deep_thinking: 是否启用深度思考
            agent_id: Agent ID
            agent_manager: Agent管理器
            images: 图片base64数据列表（不包含data:前缀）

        Returns:
            生成的回复文本
        """
        try:
            system_prompt = self.get_system_prompt(agent_id, agent_manager)
            model = config.MODEL_NAME

            # 构建消息列表
            messages = [{"role": "system", "content": system_prompt}]

            # 添加聊天历史
            for msg in chat_history:
                messages.append({
                    "role": msg["role"],
                    "content": msg["content"]
                })

            # 构建当前用户消息（支持多模态）
            if images and len(images) > 0:
                # 多模态消息格式
                content = [{"type": "text", "text": query_text}]
                for image_base64 in images:
                    content.append({
                        "type": "image_url",
                        "image_url": {"url": f"data:image/jpeg;base64,{image_base64}"}
                    })
                messages.append({"role": "user", "content": content})
            else:
                # 纯文本消息
                messages.append({"role": "user", "content": query_text})

            # 如果启用深度思考，添加reasoning_effort参数
            if enable_deep_thinking:
                request_params["reasoning_effort"] = "high"  # 可配置为low/medium/high
                model = "gemini-2.5-pro"

            # 构建请求参数
            request_params = {
                "model": model,
                "messages": messages,
                "stream": False,  # 这里先实现非流式，后续可以扩展
            }

            # 调用OpenAI API
            response = self.openai_client.chat.completions.create(**request_params)

            return response.choices[0].message.content

        except Exception as e:
            logger.error(f"普通聊天模式出错: {e}", exc_info=True)
            raise

    def chat_normal_mode_stream(self, query_text: str, chat_history: List[Dict[str, str]],
                               enable_deep_thinking: bool = False, agent_id: Optional[str] = None,
                               agent_manager=None, images: Optional[List[str]] = None):
        """
        普通聊天模式流式版本：使用OpenAI库流式调用，无RAG无联网

        Args:
            query_text: 用户查询
            chat_history: 聊天历史
            enable_deep_thinking: 是否启用深度思考
            agent_id: Agent ID

        Yields:
            生成的回复文本块
        """
        try:
            system_prompt = self.get_system_prompt(agent_id, agent_manager)

            # 构建消息列表
            messages = [{"role": "system", "content": system_prompt}]

            # 添加聊天历史
            for msg in chat_history:
                messages.append({
                    "role": msg["role"],
                    "content": msg["content"]
                })

            # 构建当前用户消息（支持多模态）
            if images and len(images) > 0:
                # 多模态消息格式
                content = [{"type": "text", "text": query_text}]
                for image_base64 in images:
                    content.append({
                        "type": "image_url",
                        "image_url": {"url": f"data:image/jpeg;base64,{image_base64}"}
                    })
                messages.append({"role": "user", "content": content})
            else:
                # 纯文本消息
                messages.append({"role": "user", "content": query_text})

            # 构建请求参数
            request_params = {
                "model": "gemini-2.5-flash",
                "messages": messages,
                "stream": True  # 启用流式
            }

            # 如果启用深度思考，添加reasoning_effort参数
            if enable_deep_thinking:
                request_params["reasoning_effort"] = "medium"  # 可配置为low/medium/high

            # 调用OpenAI API流式
            response = self.openai_client.chat.completions.create(**request_params)

            # 流式返回内容
            for chunk in response:
                if chunk.choices[0].delta.content is not None:
                    yield chunk.choices[0].delta.content

        except Exception as e:
            logger.error(f"普通聊天模式流式出错: {e}", exc_info=True)
            raise

    def chat_web_search_mode(self, query_text: str, chat_history: List[Dict[str, str]],
                           enable_deep_thinking: bool = False, agent_id: Optional[str] = None,
                           agent_manager=None, images: Optional[List[str]] = None) -> str:
        """
        联网搜索模式：使用Google GenAI + GoogleSearch工具

        Args:
            query_text: 用户查询
            chat_history: 聊天历史
            enable_deep_thinking: 是否启用深度思考
            agent_id: Agent ID

        Returns:
            生成的回复文本
        """
        try:
            system_prompt = self.get_system_prompt(agent_id, agent_manager)

            # 构建消息内容
            contents = [system_prompt]

            # 添加聊天历史
            for msg in chat_history:
                contents.append(f"{msg['role']}: {msg['content']}")

            # 添加当前用户消息
            contents.append(f"user: {query_text}")

            # 合并所有内容
            full_content = "\n".join(contents)

            # 配置GoogleSearch工具
            grounding_tool = types.Tool(
                google_search=types.GoogleSearch()
            )

            # 构建配置
            config_params = {
                "tools": [grounding_tool]
            }

            # 如果启用深度思考，可以在这里添加相关配置
            # Google GenAI的深度思考可能需要不同的实现方式

            config = types.GenerateContentConfig(**config_params)

            # 调用Google GenAI API
            response = self.genai_client.models.generate_content_stream(
                model=os.getenv('MODEL_NAME'),
                contents=full_content,
                config=config,
            )

            return response.text

        except Exception as e:
            logger.error(f"联网搜索模式出错: {e}", exc_info=True)
            raise

    def chat_web_search_mode_stream(self, query_text: str, chat_history: List[Dict[str, str]],
                                  enable_deep_thinking: bool = False, agent_id: Optional[str] = None,
                                  agent_manager=None, images: Optional[List[str]] = None):
        """
        联网搜索模式流式版本：使用Google GenAI + GoogleSearch工具

        Args:
            query_text: 用户查询
            chat_history: 聊天历史
            enable_deep_thinking: 是否启用深度思考
            agent_id: Agent ID

        Yields:
            生成的回复文本块
        """
        try:
            system_prompt = self.get_system_prompt(agent_id, agent_manager)

            # 构建消息内容
            contents = [system_prompt]

            # 添加聊天历史
            for msg in chat_history:
                contents.append(f"{msg['role']}: {msg['content']}")

            # 添加当前用户消息
            contents.append(f"user: {query_text}")

            # 合并所有内容
            full_content = "\n".join(contents)

            # 配置GoogleSearch工具
            grounding_tool = types.Tool(
                google_search=types.GoogleSearch()
            )

            # 构建配置
            config_params = {
                "tools": [grounding_tool]
            }

            # 如果启用深度思考，可以在这里添加相关配置
            # Google GenAI的深度思考可能需要不同的实现方式

            config = types.GenerateContentConfig(**config_params)

            # 调用Google GenAI API流式
            for chunk in self.genai_client.models.generate_content_stream(
                model=os.getenv('MODEL_NAME'),
                contents=full_content,
                config=config,
            ):
                if chunk.text:
                    yield chunk.text

        except Exception as e:
            logger.error(f"联网搜索模式流式出错: {e}", exc_info=True)
            raise
