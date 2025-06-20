import os
import json
import uuid
import logging
from datetime import datetime
from typing import List, Dict, Optional, Any
from threading import Lock


class ConversationManager:
    """管理对话历史的存储和检索。"""

    def __init__(self, history_path: str = "history"):
        self.history_path = history_path
        self._lock = Lock()
        os.makedirs(self.history_path, exist_ok=True)

    def _get_conv_path(self, conversation_id: str) -> str:
        return os.path.join(self.history_path, f"{conversation_id}.jsonl")

    def create_conversation(self) -> Dict[str, Any]:
        """创建一个新的空会话，并返回其元数据。"""
        conversation_id = str(uuid.uuid4())
        filepath = self._get_conv_path(conversation_id)

        # 创建一个元数据头部，写入文件第一行
        meta = {
            "id": conversation_id,
            "title": "New Conversation",
            "created_at": datetime.utcnow().isoformat(),
            "last_modified": datetime.utcnow().isoformat(),
        }

        with self._lock:
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(json.dumps({"type": "metadata", "data": meta}) + "\n")

        logging.info(f"创建新会话: {conversation_id}")
        return meta

    def list_conversations(self) -> List[Dict[str, Any]]:
        """列出所有会话的元数据。"""
        conversations = []
        for filename in os.listdir(self.history_path):
            if filename.endswith(".jsonl"):
                filepath = os.path.join(self.history_path, filename)
                with open(filepath, "r", encoding="utf-8") as f:
                    try:
                        first_line = f.readline()
                        record = json.loads(first_line)
                        if record.get("type") == "metadata":
                            conversations.append(record["data"])
                    except (json.JSONDecodeError, KeyError):
                        logging.warning(f"无法解析会话文件 {filename} 的元数据。")

        # 按最后修改时间降序排序
        return sorted(conversations, key=lambda x: x["last_modified"], reverse=True)

    def get_conversation(self, conversation_id: str) -> Optional[Dict[str, Any]]:
        """获取单个会话的所有消息和元数据。"""
        filepath = self._get_conv_path(conversation_id)
        if not os.path.exists(filepath):
            return None

        messages = []
        metadata = {}
        with open(filepath, "r", encoding="utf-8") as f:
            for line in f:
                record = json.loads(line)
                if record.get("type") == "metadata":
                    metadata = record["data"]
                elif record.get("type") == "message":
                    messages.append(record["data"])

        return {"metadata": metadata, "messages": messages}

    def add_message_to_conversation(
        self, conversation_id: str, message: Dict[str, str]
    ):
        """向会话追加一条消息，并更新最后修改时间。"""
        filepath = self._get_conv_path(conversation_id)
        if not os.path.exists(filepath):
            raise FileNotFoundError("会话不存在。")

        # 准备新消息记录
        message_record = {
            "type": "message",
            "data": {
                "role": message["role"],
                "content": message["content"],
                "timestamp": datetime.utcnow().isoformat(),
            },
        }

        with self._lock:
            # 读取所有行，更新元数据，然后重写文件
            lines = []
            with open(filepath, "r", encoding="utf-8") as f:
                lines = f.readlines()

            if lines:
                meta_record = json.loads(lines[0])
                if meta_record.get("type") == "metadata":
                    meta_record["data"]["last_modified"] = datetime.utcnow().isoformat()
                    # 如果是第一条用户消息，更新会话标题
                    if message["role"] == "user" and len(lines) == 1:
                        meta_record["data"]["title"] = message["content"][:50]
                    lines[0] = json.dumps(meta_record) + "\n"

            lines.append(json.dumps(message_record) + "\n")

            with open(filepath, "w", encoding="utf-8") as f:
                f.writelines(lines)

    def delete_conversation(self, conversation_id: str) -> bool:
        """删除一个会话文件。"""
        filepath = self._get_conv_path(conversation_id)
        if os.path.exists(filepath):
            os.remove(filepath)
            logging.info(f"删除会话: {conversation_id}")
            return True
        return False

    def search_conversations(self, query: str) -> List[Dict[str, Any]]:
        """在所有会话内容中模糊搜索。"""
        results = []
        query_lower = query.lower()

        for conv_meta in self.list_conversations():
            conv_id = conv_meta["id"]
            conversation = self.get_conversation(conv_id)
            if conversation:
                # 检查标题
                if query_lower in conversation["metadata"]["title"].lower():
                    results.append({"match_type": "title", "conversation": conv_meta})
                    continue  # 匹配到标题就不用再检查内容了

                # 检查消息内容
                for msg in conversation["messages"]:
                    if query_lower in msg["content"].lower():
                        results.append(
                            {"match_type": "content", "conversation": conv_meta}
                        )
                        break  # 一个会话只添加一次
        return results
