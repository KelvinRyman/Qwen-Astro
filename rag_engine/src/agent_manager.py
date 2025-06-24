import os
import json
import uuid
import logging
from typing import Dict, Optional, List
from threading import RLock
from datetime import datetime

from .config import RAGConfig
from .utils import ensure_directory_exists


class AgentManager:
    """
    管理Agent的元数据和存储。
    确保Agent名称唯一性，并提供Agent的CRUD操作。
    """

    def __init__(self, config: RAGConfig):
        # 使用配置中的数据路径，创建agents.json文件
        self.meta_file_path = os.path.join(config.DATA_PATH, "agents.json")
        self.data_root = config.DATA_PATH
        self._lock = RLock()  # 保证对元数据文件读写的线程安全
        self.agents_meta = self._load_meta()

        # 确保 data 根目录存在
        ensure_directory_exists(self.data_root)

    def _load_meta(self) -> Dict[str, Dict]:
        """
        加载Agent元数据文件。如果文件不存在，则返回空字典。
        确保正确处理中文字符。
        """
        with self._lock:
            if not os.path.exists(self.meta_file_path):
                return {}
            try:
                with open(self.meta_file_path, "r", encoding="utf-8") as f:
                    return json.load(f)
            except (json.JSONDecodeError, IOError) as e:
                logging.error(f"加载Agent元数据文件失败: {e}, 将使用空元数据。")
                return {}

    def _save_meta(self):
        """将当前元数据保存到文件，确保正确处理中文字符。"""
        with self._lock:
            try:
                with open(self.meta_file_path, "w", encoding="utf-8") as f:
                    json.dump(self.agents_meta, f, indent=4, ensure_ascii=False)
            except IOError as e:
                logging.error(f"保存Agent元数据文件失败: {e}")

    def create_agent(self, name: str, system_prompt: str, description: str = "", enable_MCP: bool = False, tools: str = "") -> Optional[Dict]:
        """
        创建一个新的Agent。

        Args:
            name: Agent名称
            system_prompt: 系统提示词
            description: Agent描述
            enable_MCP: 是否启用MCP
            tools: Agent的工具配置

        Returns:
            成功则返回新Agent的元数据字典，失败则返回 None。
        """
        if name in self.get_all_agent_names():
            logging.error(f"Agent名称 '{name}' 已存在，创建失败。")
            return None

        agent_id = str(uuid.uuid4())
        
        new_agent_meta = {
            "name": name,
            "system_prompt": system_prompt,
            "description": description,
            "enable_MCP": enable_MCP,
            "tools": tools,
            "created_at": datetime.now().isoformat(),
        }

        # 使用 agent_id 作为元数据中的 key
        self.agents_meta[agent_id] = new_agent_meta
        self._save_meta()
        logging.info(f"成功创建Agent '{name}' (ID: {agent_id})。")
        return {"id": agent_id, **new_agent_meta}

    def get_agent_by_name(self, name: str) -> Optional[Dict]:
        """通过名称查找Agent。"""
        for agent_id, meta in self.agents_meta.items():
            if meta.get("name") == name:
                return {"id": agent_id, **meta}
        return None

    def get_agent_by_id(self, agent_id: str) -> Optional[Dict]:
        """通过ID查找Agent。"""
        meta = self.agents_meta.get(agent_id)
        return {"id": agent_id, **meta} if meta else None

    def list_agents(self) -> List[Dict]:
        """返回所有Agent的元数据列表。"""
        return [{"id": aid, **meta} for aid, meta in self.agents_meta.items()]

    def get_all_agent_names(self) -> List[str]:
        """返回所有Agent的名称列表。"""
        return [meta["name"] for meta in self.agents_meta.values()]

    def update_agent(self, agent_id: str, update_data: Dict) -> Optional[Dict]:
        """
        更新Agent信息。

        Args:
            agent_id: Agent ID
            update_data: 要更新的数据字典

        Returns:
            成功则返回更新后的Agent元数据，失败则返回None
        """
        with self._lock:
            agent_meta = self.agents_meta.get(agent_id)
            if not agent_meta:
                logging.error(f"更新Agent失败：找不到Agent (ID: {agent_id})。")
                return None

            # 检查名称唯一性（如果要更新名称）
            if "name" in update_data and update_data["name"] != agent_meta["name"]:
                if update_data["name"] in self.get_all_agent_names():
                    logging.error(f"Agent名称 '{update_data['name']}' 已存在，更新失败。")
                    return None

            # 更新字段
            for key, value in update_data.items():
                if key in ["name", "system_prompt", "description", "enable_MCP", "tools"]:
                    agent_meta[key] = value

            self._save_meta()
            logging.info(f"成功更新Agent (ID: {agent_id})。")
            return {"id": agent_id, **agent_meta}

    def delete_agent(self, agent_id: str) -> bool:
        """
        删除指定的Agent。

        Args:
            agent_id: Agent ID

        Returns:
            成功删除返回True，否则返回False
        """
        with self._lock:
            if agent_id not in self.agents_meta:
                logging.warning(f"尝试删除一个不存在的Agent (ID: {agent_id})，操作跳过。")
                return True  # 幂等性：不存在就等于已删除

            agent_name = self.agents_meta[agent_id].get("name", "未知")
            del self.agents_meta[agent_id]
            self._save_meta()
            logging.info(f"成功删除Agent '{agent_name}' (ID: {agent_id})。")
            return True
