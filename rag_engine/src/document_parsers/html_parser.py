"""
HTML文档解析器

支持HTML格式文档的文本提取、元数据提取和智能分块。
"""

import logging
from typing import List, Optional
from pathlib import Path
from .base_parser import DocumentParser, DocumentMetadata, DocumentChunk

try:
    from bs4 import BeautifulSoup
    import lxml
    HTML_AVAILABLE = True
except ImportError as e:
    logging.warning(f"HTML解析库导入失败: {e}")
    HTML_AVAILABLE = False


class HtmlParser(DocumentParser):
    """HTML文档解析器"""
    
    def __init__(self, config=None):
        super().__init__(config)
        self.extract_metadata_tags = self.config.get('extract_metadata_tags', True)
        self.chunk_by_sections = self.config.get('chunk_by_sections', True)
        self.min_section_length = self.config.get('min_section_length', 50)
        self.remove_tags = self.config.get('remove_tags', ['script', 'style', 'nav', 'footer', 'header'])
    
    def can_parse(self, file_path: str) -> bool:
        """检查是否能解析HTML文件"""
        if not HTML_AVAILABLE:
            return False
        
        extension = Path(file_path).suffix.lower()
        return extension in ['.html', '.htm']
    
    def get_supported_extensions(self) -> List[str]:
        """获取支持的文件扩展名"""
        return ['.html', '.htm']
    
    def extract_metadata(self, file_path: str) -> DocumentMetadata:
        """提取HTML元数据"""
        metadata = DocumentMetadata(format_type='html')
        
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
            
            soup = BeautifulSoup(content, 'lxml' if 'lxml' in str(lxml) else 'html.parser')
            
            if self.extract_metadata_tags:
                # 提取标题
                title_tag = soup.find('title')
                if title_tag:
                    metadata.title = title_tag.text.strip()
                
                # 提取meta标签信息
                meta_tags = soup.find_all('meta')
                for meta in meta_tags:
                    name = meta.get('name', '').lower()
                    content_attr = meta.get('content', '')
                    
                    if name == 'author':
                        metadata.author = content_attr
                    elif name == 'description':
                        metadata.subject = content_attr
                    elif name == 'keywords':
                        metadata.keywords = content_attr
                    elif name == 'generator':
                        metadata.creator = content_attr
            
            # 统计信息
            text = self._extract_text_from_soup(soup)
            metadata.word_count = len(text.split()) if text else 0
            
            # HTML特定信息
            headings = soup.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6'])
            paragraphs = soup.find_all('p')
            links = soup.find_all('a')
            images = soup.find_all('img')
            
            metadata.extra_metadata = {
                'heading_count': len(headings),
                'paragraph_count': len(paragraphs),
                'link_count': len(links),
                'image_count': len(images)
            }
            
            # 文件大小
            metadata.file_size = Path(file_path).stat().st_size
            
        except Exception as e:
            self.logger.error(f"提取HTML元数据失败: {e}")
        
        return metadata
    
    def extract_text(self, file_path: str) -> str:
        """提取HTML全文"""
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
            
            soup = BeautifulSoup(content, 'lxml' if 'lxml' in str(lxml) else 'html.parser')
            text = self._extract_text_from_soup(soup)
            
            return self._clean_text(text)
            
        except Exception as e:
            self.logger.error(f"提取HTML文本失败: {e}")
            return ""
    
    def extract_chunks(self, file_path: str) -> List[DocumentChunk]:
        """提取HTML分块"""
        chunks = []
        base_metadata = {'file_name': Path(file_path).name, 'format_type': 'html'}
        
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
            
            soup = BeautifulSoup(content, 'lxml' if 'lxml' in str(lxml) else 'html.parser')
            
            if self.chunk_by_sections:
                chunks = self._extract_chunks_by_sections(soup, base_metadata)
            else:
                chunks = self._extract_chunks_by_elements(soup, base_metadata)
            
        except Exception as e:
            self.logger.error(f"提取HTML分块失败: {e}")
        
        return chunks
    
    def _extract_text_from_soup(self, soup: BeautifulSoup) -> str:
        """从BeautifulSoup对象中提取文本"""
        # 移除不需要的标签
        for tag_name in self.remove_tags:
            for tag in soup.find_all(tag_name):
                tag.decompose()
        
        # 提取文本
        text = soup.get_text(separator=' ')
        return text
    
    def _extract_chunks_by_sections(self, soup: BeautifulSoup, base_metadata: dict) -> List[DocumentChunk]:
        """按章节分块（基于标题层级）"""
        chunks = []
        
        # 移除不需要的标签
        soup_copy = BeautifulSoup(str(soup), 'html.parser')
        for tag_name in self.remove_tags:
            for tag in soup_copy.find_all(tag_name):
                tag.decompose()
        
        # 找到所有标题
        headings = soup_copy.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6'])
        
        if not headings:
            # 如果没有标题，按段落分块
            return self._extract_chunks_by_elements(soup_copy, base_metadata)
        
        section_counter = 0
        current_section = {'title': None, 'content': [], 'level': 0}
        
        # 遍历所有元素
        for element in soup_copy.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'p', 'div']):
            if element.name in ['h1', 'h2', 'h3', 'h4', 'h5', 'h6']:
                # 这是一个标题
                if current_section['content']:
                    # 保存当前章节
                    chunk = self._create_section_chunk(current_section, base_metadata, section_counter)
                    if chunk:
                        chunks.append(chunk)
                    section_counter += 1
                
                # 开始新章节
                level = int(element.name[1])  # h1->1, h2->2, etc.
                current_section = {
                    'title': element.text.strip(),
                    'content': [],
                    'level': level
                }
            else:
                # 这是内容元素
                text = element.text.strip()
                if text and len(text) >= self.min_section_length:
                    current_section['content'].append(text)
        
        # 处理最后一个章节
        if current_section['content']:
            chunk = self._create_section_chunk(current_section, base_metadata, section_counter)
            if chunk:
                chunks.append(chunk)
        
        return chunks
    
    def _extract_chunks_by_elements(self, soup: BeautifulSoup, base_metadata: dict) -> List[DocumentChunk]:
        """按元素分块"""
        chunks = []
        element_counter = 0
        
        # 移除不需要的标签
        for tag_name in self.remove_tags:
            for tag in soup.find_all(tag_name):
                tag.decompose()
        
        # 提取主要内容元素
        content_elements = soup.find_all(['p', 'div', 'article', 'section'])
        
        for element in content_elements:
            text = element.text.strip()
            if text and len(text) >= self.min_section_length:
                element_counter += 1
                
                chunk_metadata = self._create_chunk_metadata(
                    base_metadata,
                    {
                        'element_number': element_counter,
                        'element_tag': element.name,
                        'chunk_type': 'element'
                    }
                )
                
                chunk = DocumentChunk(
                    text=self._clean_text(text),
                    metadata=chunk_metadata,
                    chunk_id=f"element_{element_counter}",
                    chunk_type='element'
                )
                chunks.append(chunk)
        
        return chunks
    
    def _create_section_chunk(self, section: dict, base_metadata: dict, section_id: int) -> Optional[DocumentChunk]:
        """创建章节分块"""
        if not section['content']:
            return None
        
        # 组合标题和内容
        text_parts = []
        if section['title']:
            text_parts.append(section['title'])
        text_parts.extend(section['content'])
        
        cleaned_text = self._clean_text('\n\n'.join(text_parts))
        
        chunk_metadata = self._create_chunk_metadata(
            base_metadata,
            {
                'section_title': section['title'],
                'section_level': section['level'],
                'section_number': section_id + 1,
                'chunk_type': 'section'
            }
        )
        
        return DocumentChunk(
            text=cleaned_text,
            metadata=chunk_metadata,
            chunk_id=f"section_{section_id + 1}",
            section_title=section['title'],
            chunk_type='section'
        )
