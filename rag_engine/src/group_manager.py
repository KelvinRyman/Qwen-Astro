import os
import json
import uuid
import shutil
import logging
from typing import Dict, Optional, List
from threading import Lock, RLock
from datetime import datetime

from .config import RAGConfig
from .utils import ensure_directory_exists


class GroupManager:
    """
    管理资源组的元数据和物理存储。
    确保组名唯一性，并将逻辑组映射到物理目录。
    """

    def __init__(self, config: RAGConfig):
        self.meta_file_path = config.GROUP_META_FILE_PATH
        self.data_root = os.path.dirname(self.meta_file_path)
        self._lock = RLock()  # 保证对元数据文件读写的线程安全
        self.groups_meta = self._load_meta()

        # 确保 data 根目录存在
        ensure_directory_exists(self.data_root)

    def _load_meta(self) -> Dict[str, Dict]:
        """
        加载元数据文件。如果文件不存在，则返回空字典。
        确保正确处理中文字符。
        """
        with self._lock:
            if not os.path.exists(self.meta_file_path):
                return {}
            try:
                with open(self.meta_file_path, "r", encoding="utf-8") as f:
                    return json.load(f)
            except (json.JSONDecodeError, IOError) as e:
                logging.error(f"加载组元数据文件失败: {e}, 将使用空元数据。")
                return {}

    def _save_meta(self):
        """将当前元数据保存到文件，确保正确处理中文字符。"""
        with self._lock:
            try:
                with open(self.meta_file_path, "w", encoding="utf-8") as f:
                    json.dump(self.groups_meta, f, indent=4, ensure_ascii=False)
            except IOError as e:
                logging.error(f"保存组元数据文件失败: {e}")

    def create_group(self, name: str, description: str) -> Optional[Dict]:
        """
        创建一个新的组。

        - 检查名称唯一性。
        - 生成一个物理目录。
        - 更新并保存元数据。

        Returns:
            成功则返回新组的元数据字典，失败则返回 None。
        """
        if name in self.get_all_group_names():
            logging.error(f"组名 '{name}' 已存在，创建失败。")
            return None

        group_id = str(uuid.uuid4())
        group_dir = os.path.join(self.data_root, group_id)

        try:
            os.makedirs(group_dir)
            logging.info(f"为新组 '{name}' 创建了物理目录: {group_dir}")
        except OSError as e:
            logging.error(f"创建组目录失败: {e}")
            return None

        new_group_meta = {
            "name": name,
            "description": description,
            "directory": group_id,  # 只存储相对ID，不存储完整路径
            "files": [],
            "webpages": [],
        }

        # 使用 group_id 作为元数据中的 key，这比用 name 更稳定
        self.groups_meta[group_id] = new_group_meta
        self._save_meta()
        logging.info(f"成功创建组 '{name}' (ID: {group_id})。")
        return {"id": group_id, **new_group_meta}

    def get_group_by_name(self, name: str) -> Optional[Dict]:
        """通过名称查找组。"""
        for group_id, meta in self.groups_meta.items():
            if meta.get("name") == name:
                return {"id": group_id, **meta}
        return None

    def get_group_by_id(self, group_id: str) -> Optional[Dict]:
        """通过ID查找组。"""
        meta = self.groups_meta.get(group_id)
        return {"id": group_id, **meta} if meta else None

    def get_all_groups(self) -> List[Dict]:
        """返回所有组的元数据列表。"""
        return [{"id": gid, **meta} for gid, meta in self.groups_meta.items()]

    def get_all_group_names(self) -> List[str]:
        """返回所有组的名称列表。"""
        return [meta["name"] for meta in self.groups_meta.values()]

    def get_group_physical_path(self, group_id: str) -> Optional[str]:
        """获取组的物理目录的完整路径。"""
        meta = self.get_group_by_id(group_id)
        if not meta:
            return None
        return os.path.join(self.data_root, meta["directory"])

    def get_file_by_id(self, group_id: str, file_id: str) -> Optional[Dict]:
        """通过文件ID在指定组中查找文件元数据。"""
        group = self.get_group_by_id(group_id)
        if group:
            for file_info in group.get("files", []):
                if file_info.get("id") == file_id:
                    return file_info
        return None

    def get_file_by_name(self, group_id: str, file_name: str) -> Optional[Dict]:
        """通过文件名在指定组中查找文件元数据。"""
        group = self.get_group_by_id(group_id)
        if group:
            for file_info in group.get("files", []):
                if file_info.get("name") == file_name:
                    return file_info
        return None
        
    def get_webpage_by_url(self, group_id: str, url: str) -> Optional[Dict]:
        """通过URL在指定组中查找网页元数据。"""
        group = self.get_group_by_id(group_id)
        if group:
            for webpage_info in group.get("webpages", []):
                if webpage_info.get("url") == url:
                    return webpage_info
        return None

    def add_file_meta(
        self, group_id: str, file_name: str, file_size: int, storage_path: str = None, status: str = "processing"
    ) -> Optional[Dict]:
        """
        向元数据中添加一个文件的记录。
        
        Args:
            group_id: 组的唯一标识符
            file_name: 原始文件名（可能包含中文）
            file_size: 文件大小（字节）
            storage_path: 存储路径（相对于组目录，通常使用ID作为文件名）
            status: 文件处理状态
        
        Returns:
            成功则返回文件元数据字典，失败则返回None
        """
        with self._lock:
            group_meta = self.groups_meta.get(group_id)
            if not group_meta:
                logging.error(f"添加文件元数据失败：找不到组 (ID: {group_id})。")
                return None

            # 如果没有提供存储路径，则使用文件名作为存储路径
            if storage_path is None:
                storage_path = file_name

            file_meta = {
                "id": str(uuid.uuid4()),
                "name": file_name,
                "path": storage_path,  # 物理路径相对于组目录
                "creation_time": datetime.now().strftime("%Y-%m-%d %H:%M"),
                "size": file_size,
                "status": status,
            }
            group_meta["files"].append(file_meta)
            self._save_meta()
            logging.info(f"成功将文件 '{file_name}' 的元数据添加到组 '{group_meta['name']}'。")
            return file_meta

    def update_file_status(self, group_id: str, file_id: str, status: str) -> bool:
        """更新组中特定文件的状态。"""
        with self._lock:
            group_meta = self.groups_meta.get(group_id)
            if not group_meta:
                return False

            for file_info in group_meta.get("files", []):
                if file_info.get("id") == file_id:
                    file_info["status"] = status
                    self._save_meta()
                    logging.info(f"文件 {file_id} 的状态已更新为: {status}")
                    return True
            return False

    def remove_file_meta(self, group_id: str, file_id: str) -> bool:
        """只从元数据中移除一个文件的记录。"""
        with self._lock:
            group_meta = self.groups_meta.get(group_id)
            if not group_meta:
                return False

            initial_len = len(group_meta["files"])
            group_meta["files"] = [f for f in group_meta["files"] if f["id"] != file_id]

            if len(group_meta["files"]) < initial_len:
                self._save_meta()
                return True
            return False

    def add_webpage_meta(self, group_id: str, url: str, status: str = "processing") -> Optional[Dict]:
        """只向元数据中添加一个网页的记录。"""
        with self._lock:
            group_meta = self.groups_meta.get(group_id)
            if not group_meta:
                logging.error(f"添加网页元数据失败：找不到组 (ID: {group_id})。")
                return None

            webpage_meta = {
                "id": str(uuid.uuid4()),
                "url": url,
                "creation_time": datetime.now().strftime("%Y-%m-%d %H:%M"),
                "status": status,
            }
            group_meta["webpages"].append(webpage_meta)
            self._save_meta()
            logging.info(f"成功将网页 '{url}' 的元数据添加到组 '{group_meta['name']}'。")
            return webpage_meta

    def update_webpage_status(self, group_id: str, webpage_id: str, status: str) -> bool:
        """更新组中特定网页的状态。"""
        with self._lock:
            group_meta = self.groups_meta.get(group_id)
            if not group_meta:
                return False

            for page_info in group_meta.get("webpages", []):
                if page_info.get("id") == webpage_id:
                    page_info["status"] = status
                    self._save_meta()
                    logging.info(f"网页 {webpage_id} 的状态已更新为: {status}")
                    return True
            return False

    def remove_webpage_meta(self, group_id: str, webpage_id: str) -> bool:
        """只从元数据中移除一个网页的记录。"""
        with self._lock:
            group_meta = self.groups_meta.get(group_id)
            if not group_meta:
                return False

            initial_len = len(group_meta["webpages"])
            group_meta["webpages"] = [
                w for w in group_meta["webpages"] if w["id"] != webpage_id
            ]

            if len(group_meta["webpages"]) < initial_len:
                self._save_meta()
                return True
            return False

    def list_files_metadata(self, group_id: str) -> List[Dict]:
        """返回指定组中所有文件的元数据列表。"""
        group = self.get_group_by_id(group_id)
        return group.get("files", []) if group else []

    def list_webpages_metadata(self, group_id: str) -> List[Dict]:
        """返回指定组中所有网页的元数据列表。"""
        group = self.get_group_by_id(group_id)
        return group.get("webpages", []) if group else []

    def delete_group_metadata_and_storage(self, group_id: str) -> bool:
        """
        删除组的元数据条目以及其物理存储目录。
        这是一个底层操作，应当在向量数据库被清理之后调用。
        
        Keyword arguments:
        group_id -- 组的唯一标识符
        Return: 返回是否成功删除组
        """

        group_meta = self.get_group_by_id(group_id)
        if not group_meta:
            logging.warning(
                f"尝试删除一个不存在的组元数据 (ID: {group_id})，操作跳过。"
            )
            return True  # 幂等性：不存在就等于已删除

        # 步骤 1: 删除物理目录
        physical_path = self.get_group_physical_path(group_id)
        if physical_path and os.path.exists(physical_path):
            try:
                shutil.rmtree(physical_path)
                logging.info(
                    f"成功删除组 '{group_meta['name']}' 的物理目录: {physical_path}"
                )
            except OSError as e:
                logging.error(f"删除组 '{group_meta['name']}' 的物理目录失败: {e}")
                # 即使目录删除失败，我们可能仍希望继续删除元数据，但这取决于业务需求。
                # 在这里，我们选择中止，因为这可能表示权限问题。
                return False

        # 步骤 2: 从元数据字典中删除条目并保存
        with self._lock:
            if group_id in self.groups_meta:
                del self.groups_meta[group_id]
                self._save_meta()
                logging.info(
                    f"成功从元数据文件中删除了组 '{group_meta['name']}' (ID: {group_id})。"
                )
            else:
                logging.warning(f"在准备删除元数据时，发现组ID '{group_id}' 已不存在。")

        return True

    def list_files_in_group(self, group_id: str) -> List[str]:
        """
        列出指定组的物理目录下的所有文件名。

        Returns:
            一个包含文件名的列表，如果目录不存在则返回空列表。
        """
        physical_path = self.get_group_physical_path(group_id)
        if not physical_path or not os.path.isdir(physical_path):
            return []

        try:
            # 只返回文件名，不包括子目录
            return [
                f
                for f in os.listdir(physical_path)
                if os.path.isfile(os.path.join(physical_path, f))
            ]
        except OSError as e:
            logging.error(f"无法列出组 '{group_id}' 目录中的文件: {e}")
            return []
