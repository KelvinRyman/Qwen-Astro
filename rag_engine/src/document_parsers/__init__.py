"""
多格式文档解析器模块

支持的文档格式：
- PDF (.pdf)
- Microsoft Word (.docx, .doc)
- Microsoft PowerPoint (.pptx, .ppt)
- Microsoft Excel (.xlsx, .xls)
- EPUB电子书 (.epub)
- HTML (.html, .htm)
- Markdown (.md)
"""

from .base_parser import DocumentParser
from .format_detector import FormatDetector
from .parser_factory import ParserFactory

__all__ = [
    'DocumentParser',
    'FormatDetector', 
    'ParserFactory'
]
