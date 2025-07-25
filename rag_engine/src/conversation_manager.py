import os
import json
import uuid
import logging
from datetime import datetime
from typing import List, Dict, Optional, Any
from threading import Lock


class ConversationManager:
    """管理对话历史的存储和检索。"""

    def __init__(self, history_dir="history"):
        self.history_dir = history_dir
        os.makedirs(self.history_dir, exist_ok=True)
        self._lock = Lock()

    def _get_conv_path(self, conversation_id: str) -> str:
        return os.path.join(self.history_dir, f"{conversation_id}.json")

    def create_conversation(self, conversation_id: str, group_ids: Optional[List[str]] = None, agent_id: Optional[str] = None) -> Dict:
        """创建一个新的对话，包含一个可选的关联组ID列表和Agent ID。"""
        conv_path = self._get_conv_path(conversation_id)
        if os.path.exists(conv_path):
            logging.warning(f"对话 {conversation_id} 已存在。")
            return self.get_conversation(conversation_id)

        conversation_data = {
            "id": conversation_id,
            "title": "新对话",  # 添加默认标题
            "created_at": datetime.now().isoformat(),
            "group_ids": group_ids or [],
            "agent_id": agent_id,  # 添加Agent ID
            "messages": [],
        }
        with open(conv_path, "w", encoding="utf-8") as f:
            json.dump(conversation_data, f, indent=4)
        return conversation_data

    def get_conversation(self, conversation_id: str) -> Optional[Dict]:
        conv_path = self._get_conv_path(conversation_id)
        if not os.path.exists(conv_path):
            return None
        with open(conv_path, "r", encoding="utf-8") as f:
            return json.load(f)

    def add_message_to_conversation(
        self, conversation_id: str, role: str, content: Any, sources: Optional[List[Dict]] = None
    ):
        conversation = self.get_conversation(conversation_id)
        if not conversation:
            logging.error(f"尝试向不存在的对话 {conversation_id} 添加消息。")
            return

        message = {
            "role": role,
            "content": content,
            "timestamp": datetime.now().isoformat()
        }

        # 如果有sources数据，添加到消息中
        if sources:
            message["sources"] = sources

        conversation["messages"].append(message)
        with open(self._get_conv_path(conversation_id), "w", encoding="utf-8") as f:
            json.dump(conversation, f, indent=4)

    def rename_conversation(self, conversation_id: str, new_title: str) -> bool:
        """重命名对话。"""
        with self._lock:
            conversation = self.get_conversation(conversation_id)
            if not conversation:
                logging.error(f"尝试重命名不存在的对话 {conversation_id}。")
                return False
            
            conversation["title"] = new_title
            with open(self._get_conv_path(conversation_id), "w", encoding="utf-8") as f:
                json.dump(conversation, f, indent=4)
            return True

    def list_conversations(self) -> List[Dict]:
        conversations = []
        for filename in os.listdir(self.history_dir):
            if filename.endswith(".json"):
                conv_id = os.path.splitext(filename)[0]
                conv_data = self.get_conversation(conv_id)
                if conv_data:
                    # 返回一个简化的摘要，而不是完整的消息历史
                    conversations.append(self._create_conversation_summary(conv_data))
        # 按创建时间降序排序
        conversations.sort(key=lambda x: x["created_at"], reverse=True)
        return conversations

    def delete_conversation(self, conversation_id: str) -> bool:
        conv_path = self._get_conv_path(conversation_id)
        if os.path.exists(conv_path):
            os.remove(conv_path)
            logging.info(f"删除会话: {conversation_id}")
            return True
        return False

    def delete_messages_from_index(self, conversation_id: str, from_index: int) -> bool:
        """从指定索引开始删除消息。"""
        with self._lock:
            conversation = self.get_conversation(conversation_id)
            if not conversation:
                logging.error(f"尝试从不存在的对话 {conversation_id} 删除消息。")
                return False
            
            if from_index < 0 or from_index >= len(conversation["messages"]):
                logging.error(f"无效的消息索引: {from_index}，对话 {conversation_id} 有 {len(conversation['messages'])} 条消息。")
                return False
            
            # 保留指定索引之前的消息
            conversation["messages"] = conversation["messages"][:from_index]
            
            with open(self._get_conv_path(conversation_id), "w", encoding="utf-8") as f:
                json.dump(conversation, f, indent=4)
            return True

    def search_conversations(self, query: str) -> List[Dict]:
        """在所有对话历史中搜索包含查询字符串的对话。"""
        matching_conversations = []
        for filename in os.listdir(self.history_dir):
            if filename.endswith(".json"):
                conv_id = os.path.splitext(filename)[0]
            conversation = self.get_conversation(conv_id)
            if conversation:
                # 检查标题
                    title = conversation.get("title", "")
                    if query.lower() in title.lower():
                        matching_conversations.append(self._create_conversation_summary(conversation))
                        continue

                # 检查消息内容
                    for message in conversation.get("messages", []):
                        content = message.get("content", "")
                        # 处理多模态消息内容
                        if isinstance(content, dict) and content.get("type") == "multimodal":
                            content = content.get("text", "")
                        elif isinstance(content, str):
                            pass  # 保持原样
                        else:
                            content = str(content)  # 转换为字符串

                        if query.lower() in content.lower():
                            matching_conversations.append(self._create_conversation_summary(conversation))
                            break
        return matching_conversations

    def _create_conversation_summary(self, conversation: Dict) -> Dict:
        """创建对话摘要。"""
        last_message = "空对话"
        if conversation["messages"]:
            content = conversation["messages"][-1]["content"]
            # 处理多模态消息内容
            if isinstance(content, dict) and content.get("type") == "multimodal":
                text_content = content.get("text", "")
                if content.get("images"):
                    last_message = f"{text_content[:40]}... [包含图片]"
                else:
                    last_message = text_content[:50] + "..." if len(text_content) > 50 else text_content
            elif isinstance(content, str):
                last_message = content[:50] + "..." if len(content) > 50 else content
            else:
                last_message = str(content)[:50] + "..."

        return {
            "id": conversation["id"],
            "title": conversation.get("title", "新对话"),
            "created_at": conversation["created_at"],
            "group_ids": conversation.get("group_ids", []),
            "last_message": last_message,
        }
