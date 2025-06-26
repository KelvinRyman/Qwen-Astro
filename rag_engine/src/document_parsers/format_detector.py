"""
文件格式检测器

通过文件扩展名、MIME类型和文件头部信息检测文档格式。
"""

import mimetypes
from pathlib import Path
from typing import Optional, Dict, List


class FormatDetector:
    """文件格式检测器"""
    
    # 支持的文件格式映射
    SUPPORTED_FORMATS = {
        # PDF
        '.pdf': 'pdf',
        
        # Microsoft Word
        '.docx': 'docx',
        '.doc': 'doc',
        
        # Microsoft PowerPoint
        '.pptx': 'pptx',
        '.ppt': 'ppt',
        
        # Microsoft Excel
        '.xlsx': 'xlsx',
        '.xls': 'xls',
        
        # EPUB
        '.epub': 'epub',
        
        # HTML
        '.html': 'html',
        '.htm': 'html',
        
        # Markdown
        '.md': 'markdown',
        '.markdown': 'markdown',
        
        # 纯文本
        '.txt': 'text',
    }
    
    # 文件头部签名（魔数）
    FILE_SIGNATURES = {
        b'%PDF': 'pdf',
        b'PK\x03\x04': 'office_zip',  # Office 2007+ 格式都是ZIP
        b'\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1': 'office_ole',  # Office 97-2003 格式
        b'<!DOCTYPE html': 'html',
        b'<html': 'html',
        b'<HTML': 'html',
    }
    
    @classmethod
    def detect_format(cls, file_path: str) -> Optional[str]:
        """
        检测文件格式
        
        Args:
            file_path: 文件路径
            
        Returns:
            Optional[str]: 检测到的格式，如果不支持则返回None
        """
        path = Path(file_path)
        
        # 首先通过扩展名检测
        extension = path.suffix.lower()
        if extension in cls.SUPPORTED_FORMATS:
            detected_format = cls.SUPPORTED_FORMATS[extension]
            
            # 对于可能有歧义的格式，进一步验证
            if detected_format in ['docx', 'pptx', 'xlsx'] or extension in ['.doc', '.ppt', '.xls']:
                return cls._verify_office_format(file_path, detected_format)
            
            return detected_format
        
        # 通过文件头部检测
        try:
            with open(file_path, 'rb') as f:
                header = f.read(16)
                
            for signature, format_type in cls.FILE_SIGNATURES.items():
                if header.startswith(signature):
                    if format_type == 'office_zip':
                        return cls._detect_office_zip_format(file_path)
                    elif format_type == 'office_ole':
                        return cls._detect_office_ole_format(file_path)
                    else:
                        return format_type
                        
        except Exception:
            pass
        
        # 通过MIME类型检测
        mime_type, _ = mimetypes.guess_type(file_path)
        if mime_type:
            return cls._mime_to_format(mime_type)
        
        return None
    
    @classmethod
    def _verify_office_format(cls, file_path: str, expected_format: str) -> str:
        """
        验证Office文档格式
        
        Args:
            file_path: 文件路径
            expected_format: 预期格式
            
        Returns:
            str: 验证后的格式
        """
        try:
            with open(file_path, 'rb') as f:
                header = f.read(8)
            
            # 检查是否为ZIP格式（Office 2007+）
            if header.startswith(b'PK\x03\x04'):
                return cls._detect_office_zip_format(file_path) or expected_format
            
            # 检查是否为OLE格式（Office 97-2003）
            elif header.startswith(b'\xd0\xcf\x11\xe0'):
                return cls._detect_office_ole_format(file_path) or expected_format
            
        except Exception:
            pass
        
        return expected_format
    
    @classmethod
    def _detect_office_zip_format(cls, file_path: str) -> Optional[str]:
        """
        检测基于ZIP的Office格式
        
        Args:
            file_path: 文件路径
            
        Returns:
            Optional[str]: 检测到的格式
        """
        try:
            import zipfile
            
            with zipfile.ZipFile(file_path, 'r') as zip_file:
                file_list = zip_file.namelist()
                
                # 检查特征文件
                if 'word/document.xml' in file_list:
                    return 'docx'
                elif 'ppt/presentation.xml' in file_list or 'ppt/slides/' in str(file_list):
                    return 'pptx'
                elif 'xl/workbook.xml' in file_list:
                    return 'xlsx'
                elif 'META-INF/container.xml' in file_list:
                    return 'epub'
                    
        except Exception:
            pass
        
        return None
    
    @classmethod
    def _detect_office_ole_format(cls, file_path: str) -> Optional[str]:
        """
        检测基于OLE的Office格式
        
        Args:
            file_path: 文件路径
            
        Returns:
            Optional[str]: 检测到的格式
        """
        # 对于OLE格式，主要依赖扩展名
        # 这里可以添加更复杂的OLE结构分析
        extension = Path(file_path).suffix.lower()
        if extension == '.doc':
            return 'doc'
        elif extension == '.ppt':
            return 'ppt'
        elif extension == '.xls':
            return 'xls'
        
        return None
    
    @classmethod
    def _mime_to_format(cls, mime_type: str) -> Optional[str]:
        """
        将MIME类型转换为格式
        
        Args:
            mime_type: MIME类型
            
        Returns:
            Optional[str]: 对应的格式
        """
        mime_mapping = {
            'application/pdf': 'pdf',
            'application/vnd.openxmlformats-officedocument.wordprocessingml.document': 'docx',
            'application/msword': 'doc',
            'application/vnd.openxmlformats-officedocument.presentationml.presentation': 'pptx',
            'application/vnd.ms-powerpoint': 'ppt',
            'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet': 'xlsx',
            'application/vnd.ms-excel': 'xls',
            'application/epub+zip': 'epub',
            'text/html': 'html',
            'text/markdown': 'markdown',
            'text/plain': 'text',
        }
        
        return mime_mapping.get(mime_type)
    
    @classmethod
    def get_supported_extensions(cls) -> List[str]:
        """
        获取所有支持的文件扩展名
        
        Returns:
            List[str]: 支持的扩展名列表
        """
        return list(cls.SUPPORTED_FORMATS.keys())
    
    @classmethod
    def is_supported(cls, file_path: str) -> bool:
        """
        检查文件是否被支持
        
        Args:
            file_path: 文件路径
            
        Returns:
            bool: 是否支持
        """
        return cls.detect_format(file_path) is not None
