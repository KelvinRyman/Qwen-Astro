"""
文档解析器工厂

根据文件格式创建相应的解析器实例。
"""

import logging
from typing import Optional, Dict, Any, List
from .base_parser import DocumentParser
from .format_detector import FormatDetector


class ParserFactory:
    """文档解析器工厂"""
    
    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)
        self._parsers = {}
        self._register_parsers()
    
    def _register_parsers(self):
        """注册所有可用的解析器"""
        try:
            # 延迟导入以避免循环依赖
            from .pdf_parser import PDFParser
            self._parsers['pdf'] = PDFParser
        except ImportError as e:
            self.logger.warning(f"PDF解析器不可用: {e}")
        
        try:
            from .docx_parser import DocxParser
            self._parsers['docx'] = DocxParser
        except ImportError as e:
            self.logger.warning(f"DOCX解析器不可用: {e}")
        
        try:
            from .pptx_parser import PptxParser
            self._parsers['pptx'] = PptxParser
        except ImportError as e:
            self.logger.warning(f"PPTX解析器不可用: {e}")
        
        try:
            from .excel_parser import ExcelParser
            self._parsers['xlsx'] = ExcelParser
            self._parsers['xls'] = ExcelParser
        except ImportError as e:
            self.logger.warning(f"Excel解析器不可用: {e}")
        
        try:
            from .epub_parser import EpubParser
            self._parsers['epub'] = EpubParser
        except ImportError as e:
            self.logger.warning(f"EPUB解析器不可用: {e}")
        
        try:
            from .html_parser import HtmlParser
            self._parsers['html'] = HtmlParser
        except ImportError as e:
            self.logger.warning(f"HTML解析器不可用: {e}")
        
        try:
            from .markdown_parser import MarkdownParser
            self._parsers['markdown'] = MarkdownParser
        except ImportError as e:
            self.logger.warning(f"Markdown解析器不可用: {e}")
        
        try:
            from .text_parser import TextParser
            self._parsers['text'] = TextParser
        except ImportError as e:
            self.logger.warning(f"文本解析器不可用: {e}")
        
        self.logger.info(f"已注册 {len(self._parsers)} 个文档解析器")
    
    def create_parser(self, file_path: str, config: Optional[Dict[str, Any]] = None) -> Optional[DocumentParser]:
        """
        根据文件路径创建相应的解析器
        
        Args:
            file_path: 文件路径
            config: 解析器配置
            
        Returns:
            Optional[DocumentParser]: 解析器实例，如果不支持则返回None
        """
        # 检测文件格式
        format_type = FormatDetector.detect_format(file_path)
        if not format_type:
            self.logger.warning(f"无法检测文件格式: {file_path}")
            return None
        
        # 获取解析器类
        parser_class = self._parsers.get(format_type)
        if not parser_class:
            self.logger.warning(f"不支持的文件格式: {format_type}")
            return None
        
        try:
            # 创建解析器实例
            parser = parser_class(config)
            self.logger.debug(f"为文件 {file_path} 创建了 {parser.get_parser_name()} 解析器")
            return parser
        except Exception as e:
            self.logger.error(f"创建解析器失败: {e}")
            return None
    
    def get_supported_formats(self) -> List[str]:
        """
        获取所有支持的格式
        
        Returns:
            List[str]: 支持的格式列表
        """
        return list(self._parsers.keys())
    
    def is_format_supported(self, format_type: str) -> bool:
        """
        检查格式是否被支持
        
        Args:
            format_type: 格式类型
            
        Returns:
            bool: 是否支持
        """
        return format_type in self._parsers
    
    def get_parser_info(self) -> Dict[str, Dict[str, Any]]:
        """
        获取所有解析器的信息
        
        Returns:
            Dict[str, Dict[str, Any]]: 解析器信息
        """
        info = {}
        for format_type, parser_class in self._parsers.items():
            try:
                # 创建临时实例获取信息
                temp_parser = parser_class()
                info[format_type] = {
                    'name': temp_parser.get_parser_name(),
                    'extensions': temp_parser.get_supported_extensions(),
                    'available': True
                }
            except Exception as e:
                info[format_type] = {
                    'name': parser_class.__name__,
                    'extensions': [],
                    'available': False,
                    'error': str(e)
                }
        
        return info


# 全局工厂实例
parser_factory = ParserFactory()
