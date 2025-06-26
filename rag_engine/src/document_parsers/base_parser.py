"""
文档解析器基类

定义了所有文档解析器的统一接口和基础功能。
"""

import logging
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
from pathlib import Path


@dataclass
class DocumentMetadata:
    """文档元数据结构"""
    title: Optional[str] = None
    author: Optional[str] = None
    creator: Optional[str] = None
    subject: Optional[str] = None
    keywords: Optional[str] = None
    creation_date: Optional[str] = None
    modification_date: Optional[str] = None
    page_count: Optional[int] = None
    word_count: Optional[int] = None
    file_size: Optional[int] = None
    format_type: Optional[str] = None
    format_version: Optional[str] = None
    language: Optional[str] = None
    # 格式特定的元数据
    extra_metadata: Optional[Dict[str, Any]] = None


@dataclass
class DocumentChunk:
    """文档分块结构"""
    text: str
    metadata: Dict[str, Any]
    chunk_id: Optional[str] = None
    page_number: Optional[int] = None
    section_title: Optional[str] = None
    chunk_type: Optional[str] = None  # 'paragraph', 'page', 'slide', 'sheet', etc.


class DocumentParser(ABC):
    """文档解析器基类"""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        初始化解析器
        
        Args:
            config: 解析器配置参数
        """
        self.config = config or {}
        self.logger = logging.getLogger(self.__class__.__name__)
    
    @abstractmethod
    def can_parse(self, file_path: str) -> bool:
        """
        检查是否能解析指定文件
        
        Args:
            file_path: 文件路径
            
        Returns:
            bool: 是否支持解析
        """
        pass
    
    @abstractmethod
    def extract_metadata(self, file_path: str) -> DocumentMetadata:
        """
        提取文档元数据
        
        Args:
            file_path: 文件路径
            
        Returns:
            DocumentMetadata: 文档元数据
        """
        pass
    
    @abstractmethod
    def extract_text(self, file_path: str) -> str:
        """
        提取文档全文
        
        Args:
            file_path: 文件路径
            
        Returns:
            str: 提取的文本内容
        """
        pass
    
    @abstractmethod
    def extract_chunks(self, file_path: str) -> List[DocumentChunk]:
        """
        提取文档分块
        
        Args:
            file_path: 文件路径
            
        Returns:
            List[DocumentChunk]: 文档分块列表
        """
        pass
    
    def validate_file(self, file_path: str) -> Tuple[bool, Optional[str]]:
        """
        验证文件是否有效
        
        Args:
            file_path: 文件路径
            
        Returns:
            Tuple[bool, Optional[str]]: (是否有效, 错误信息)
        """
        try:
            path = Path(file_path)
            if not path.exists():
                return False, f"文件不存在: {file_path}"
            
            if not path.is_file():
                return False, f"路径不是文件: {file_path}"
            
            if path.stat().st_size == 0:
                return False, f"文件为空: {file_path}"
            
            return True, None
            
        except Exception as e:
            return False, f"文件验证失败: {str(e)}"
    
    def get_supported_extensions(self) -> List[str]:
        """
        获取支持的文件扩展名
        
        Returns:
            List[str]: 支持的扩展名列表
        """
        return []
    
    def get_parser_name(self) -> str:
        """
        获取解析器名称
        
        Returns:
            str: 解析器名称
        """
        return self.__class__.__name__
    
    def _clean_text(self, text: str) -> str:
        """
        清理和标准化文本
        
        Args:
            text: 原始文本
            
        Returns:
            str: 清理后的文本
        """
        if not text:
            return ""
        
        # 标准化换行符
        text = text.replace('\r\n', '\n').replace('\r', '\n')
        
        # 移除多余的空白字符
        lines = []
        for line in text.split('\n'):
            cleaned_line = ' '.join(line.split())
            if cleaned_line:  # 只保留非空行
                lines.append(cleaned_line)
        
        return '\n'.join(lines)
    
    def _create_chunk_metadata(self, base_metadata: Dict[str, Any], 
                              chunk_specific: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        创建分块元数据
        
        Args:
            base_metadata: 基础元数据
            chunk_specific: 分块特定元数据
            
        Returns:
            Dict[str, Any]: 合并后的元数据
        """
        metadata = base_metadata.copy()
        if chunk_specific:
            metadata.update(chunk_specific)
        return metadata
