"""
EPUB电子书解析器

支持EPUB格式电子书的文本提取、元数据提取和智能分块。
"""

import logging
from typing import List, Optional
from pathlib import Path
from .base_parser import DocumentParser, DocumentMetadata, DocumentChunk

try:
    import ebooklib
    from ebooklib import epub
    from bs4 import BeautifulSoup
    EPUB_AVAILABLE = True
except ImportError as e:
    logging.warning(f"EPUB解析库导入失败: {e}")
    EPUB_AVAILABLE = False


class EpubParser(DocumentParser):
    """EPUB电子书解析器"""
    
    def __init__(self, config=None):
        super().__init__(config)
        self.extract_toc = self.config.get('extract_toc', True)
        self.chunk_by_chapter = self.config.get('chunk_by_chapter', True)
        self.min_chapter_length = self.config.get('min_chapter_length', 100)
    
    def can_parse(self, file_path: str) -> bool:
        """检查是否能解析EPUB文件"""
        if not EPUB_AVAILABLE:
            return False
        
        return Path(file_path).suffix.lower() == '.epub'
    
    def get_supported_extensions(self) -> List[str]:
        """获取支持的文件扩展名"""
        return ['.epub']
    
    def extract_metadata(self, file_path: str) -> DocumentMetadata:
        """提取EPUB元数据"""
        metadata = DocumentMetadata(format_type='epub')
        
        try:
            book = epub.read_epub(file_path)
            
            # 基本元数据
            metadata.title = book.get_metadata('DC', 'title')[0][0] if book.get_metadata('DC', 'title') else None
            metadata.author = book.get_metadata('DC', 'creator')[0][0] if book.get_metadata('DC', 'creator') else None
            metadata.subject = book.get_metadata('DC', 'subject')[0][0] if book.get_metadata('DC', 'subject') else None
            metadata.language = book.get_metadata('DC', 'language')[0][0] if book.get_metadata('DC', 'language') else None
            
            # 出版信息
            publisher = book.get_metadata('DC', 'publisher')
            publication_date = book.get_metadata('DC', 'date')
            
            # 统计信息
            chapter_count = 0
            total_word_count = 0
            
            for item in book.get_items():
                if item.get_type() == ebooklib.ITEM_DOCUMENT:
                    chapter_count += 1
                    try:
                        content = item.get_content().decode('utf-8')
                        soup = BeautifulSoup(content, 'html.parser')
                        text = soup.get_text()
                        total_word_count += len(text.split())
                    except Exception:
                        pass
            
            metadata.word_count = total_word_count
            metadata.extra_metadata = {
                'chapter_count': chapter_count,
                'publisher': publisher[0][0] if publisher else None,
                'publication_date': publication_date[0][0] if publication_date else None,
                'identifier': book.get_metadata('DC', 'identifier')[0][0] if book.get_metadata('DC', 'identifier') else None
            }
            
            # 文件大小
            metadata.file_size = Path(file_path).stat().st_size
            
        except Exception as e:
            self.logger.error(f"提取EPUB元数据失败: {e}")
        
        return metadata
    
    def extract_text(self, file_path: str) -> str:
        """提取EPUB全文"""
        try:
            book = epub.read_epub(file_path)
            text_parts = []
            
            for item in book.get_items():
                if item.get_type() == ebooklib.ITEM_DOCUMENT:
                    try:
                        content = item.get_content().decode('utf-8')
                        text = self._extract_text_from_html(content)
                        if text and len(text.strip()) >= self.min_chapter_length:
                            text_parts.append(text)
                    except Exception as e:
                        self.logger.warning(f"提取章节文本失败: {e}")
            
            return self._clean_text('\n\n'.join(text_parts))
            
        except Exception as e:
            self.logger.error(f"提取EPUB文本失败: {e}")
            return ""
    
    def extract_chunks(self, file_path: str) -> List[DocumentChunk]:
        """提取EPUB分块（按章节分块）"""
        chunks = []
        base_metadata = {'file_name': Path(file_path).name, 'format_type': 'epub'}
        
        try:
            book = epub.read_epub(file_path)
            
            if self.chunk_by_chapter:
                chunks = self._extract_chunks_by_chapter(book, base_metadata)
            else:
                chunks = self._extract_chunks_by_document(book, base_metadata)
            
        except Exception as e:
            self.logger.error(f"提取EPUB分块失败: {e}")
        
        return chunks
    
    def _extract_chunks_by_chapter(self, book, base_metadata: dict) -> List[DocumentChunk]:
        """按章节分块"""
        chunks = []
        chapter_counter = 0
        
        # 尝试获取目录结构
        toc_map = self._build_toc_map(book) if self.extract_toc else {}
        
        for item in book.get_items():
            if item.get_type() == ebooklib.ITEM_DOCUMENT:
                try:
                    content = item.get_content().decode('utf-8')
                    text = self._extract_text_from_html(content)
                    
                    if text and len(text.strip()) >= self.min_chapter_length:
                        chapter_counter += 1
                        
                        # 尝试获取章节标题
                        chapter_title = toc_map.get(item.get_name()) or self._extract_title_from_html(content)
                        
                        chunk_metadata = self._create_chunk_metadata(
                            base_metadata,
                            {
                                'chapter_number': chapter_counter,
                                'chapter_title': chapter_title,
                                'chapter_id': item.get_name(),
                                'chunk_type': 'chapter'
                            }
                        )
                        
                        chunk = DocumentChunk(
                            text=self._clean_text(text),
                            metadata=chunk_metadata,
                            chunk_id=f"chapter_{chapter_counter}",
                            section_title=chapter_title,
                            chunk_type='chapter'
                        )
                        chunks.append(chunk)
                        
                except Exception as e:
                    self.logger.warning(f"处理章节失败: {e}")
        
        return chunks
    
    def _extract_chunks_by_document(self, book, base_metadata: dict) -> List[DocumentChunk]:
        """按文档分块"""
        chunks = []
        doc_counter = 0
        
        for item in book.get_items():
            if item.get_type() == ebooklib.ITEM_DOCUMENT:
                try:
                    content = item.get_content().decode('utf-8')
                    text = self._extract_text_from_html(content)
                    
                    if text and len(text.strip()) >= self.min_chapter_length:
                        doc_counter += 1
                        
                        chunk_metadata = self._create_chunk_metadata(
                            base_metadata,
                            {
                                'document_number': doc_counter,
                                'document_id': item.get_name(),
                                'chunk_type': 'document'
                            }
                        )
                        
                        chunk = DocumentChunk(
                            text=self._clean_text(text),
                            metadata=chunk_metadata,
                            chunk_id=f"document_{doc_counter}",
                            chunk_type='document'
                        )
                        chunks.append(chunk)
                        
                except Exception as e:
                    self.logger.warning(f"处理文档失败: {e}")
        
        return chunks
    
    def _extract_text_from_html(self, html_content: str) -> str:
        """从HTML内容中提取文本"""
        try:
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # 移除脚本和样式标签
            for tag in soup(['script', 'style']):
                tag.decompose()
            
            # 提取文本
            text = soup.get_text()
            return text
        except Exception as e:
            self.logger.warning(f"从HTML提取文本失败: {e}")
            return ""
    
    def _extract_title_from_html(self, html_content: str) -> Optional[str]:
        """从HTML内容中提取标题"""
        try:
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # 尝试从title标签获取
            title_tag = soup.find('title')
            if title_tag and title_tag.text.strip():
                return title_tag.text.strip()
            
            # 尝试从h1标签获取
            h1_tag = soup.find('h1')
            if h1_tag and h1_tag.text.strip():
                return h1_tag.text.strip()
            
            # 尝试从h2标签获取
            h2_tag = soup.find('h2')
            if h2_tag and h2_tag.text.strip():
                return h2_tag.text.strip()
                
        except Exception:
            pass
        
        return None
    
    def _build_toc_map(self, book) -> dict:
        """构建目录映射"""
        toc_map = {}
        
        try:
            def process_toc_item(item, level=0):
                if isinstance(item, tuple):
                    # (Section, [children])
                    section, children = item
                    if hasattr(section, 'href'):
                        toc_map[section.href] = section.title
                    for child in children:
                        process_toc_item(child, level + 1)
                elif hasattr(item, 'href'):
                    # NavPoint
                    toc_map[item.href] = item.title
            
            for item in book.toc:
                process_toc_item(item)
                
        except Exception as e:
            self.logger.warning(f"构建目录映射失败: {e}")
        
        return toc_map
