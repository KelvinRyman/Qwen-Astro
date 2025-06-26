"""
Markdown文档解析器

支持Markdown格式文档的文本提取、元数据提取和智能分块。
"""

import logging
import re
from typing import List, Optional, Dict, Any
from pathlib import Path
from .base_parser import DocumentParser, DocumentMetadata, DocumentChunk

try:
    import markdown
    from markdown.extensions import toc
    MARKDOWN_AVAILABLE = True
except ImportError as e:
    logging.warning(f"Markdown解析库导入失败: {e}")
    MARKDOWN_AVAILABLE = False


class MarkdownParser(DocumentParser):
    """Markdown文档解析器"""
    
    def __init__(self, config=None):
        super().__init__(config)
        self.extract_frontmatter = self.config.get('extract_frontmatter', True)
        self.chunk_by_headers = self.config.get('chunk_by_headers', True)
        self.min_section_length = self.config.get('min_section_length', 50)
        self.preserve_code_blocks = self.config.get('preserve_code_blocks', True)
    
    def can_parse(self, file_path: str) -> bool:
        """检查是否能解析Markdown文件"""
        if not MARKDOWN_AVAILABLE:
            return False
        
        extension = Path(file_path).suffix.lower()
        return extension in ['.md', '.markdown']
    
    def get_supported_extensions(self) -> List[str]:
        """获取支持的文件扩展名"""
        return ['.md', '.markdown']
    
    def extract_metadata(self, file_path: str) -> DocumentMetadata:
        """提取Markdown元数据"""
        metadata = DocumentMetadata(format_type='markdown')
        
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
            
            # 提取frontmatter
            if self.extract_frontmatter:
                frontmatter = self._extract_frontmatter(content)
                if frontmatter:
                    metadata.title = frontmatter.get('title')
                    metadata.author = frontmatter.get('author')
                    metadata.subject = frontmatter.get('description')
                    metadata.keywords = frontmatter.get('tags')
                    metadata.creation_date = frontmatter.get('date')
            
            # 如果没有从frontmatter获取标题，尝试从第一个标题获取
            if not metadata.title:
                first_header = self._extract_first_header(content)
                if first_header:
                    metadata.title = first_header
            
            # 统计信息
            text = self._extract_plain_text(content)
            metadata.word_count = len(text.split()) if text else 0
            
            # Markdown特定统计
            headers = re.findall(r'^#+\s+(.+)$', content, re.MULTILINE)
            code_blocks = re.findall(r'```[\s\S]*?```', content)
            links = re.findall(r'\[([^\]]+)\]\([^)]+\)', content)
            images = re.findall(r'!\[([^\]]*)\]\([^)]+\)', content)
            
            metadata.extra_metadata = {
                'header_count': len(headers),
                'code_block_count': len(code_blocks),
                'link_count': len(links),
                'image_count': len(images),
                'line_count': len(content.splitlines())
            }
            
            # 文件大小
            metadata.file_size = Path(file_path).stat().st_size
            
        except Exception as e:
            self.logger.error(f"提取Markdown元数据失败: {e}")
        
        return metadata
    
    def extract_text(self, file_path: str) -> str:
        """提取Markdown全文"""
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
            
            # 移除frontmatter
            content = self._remove_frontmatter(content)
            
            # 提取纯文本
            text = self._extract_plain_text(content)
            
            return self._clean_text(text)
            
        except Exception as e:
            self.logger.error(f"提取Markdown文本失败: {e}")
            return ""
    
    def extract_chunks(self, file_path: str) -> List[DocumentChunk]:
        """提取Markdown分块"""
        chunks = []
        base_metadata = {'file_name': Path(file_path).name, 'format_type': 'markdown'}
        
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
            
            # 移除frontmatter
            content = self._remove_frontmatter(content)
            
            if self.chunk_by_headers:
                chunks = self._extract_chunks_by_headers(content, base_metadata)
            else:
                chunks = self._extract_chunks_by_paragraphs(content, base_metadata)
            
        except Exception as e:
            self.logger.error(f"提取Markdown分块失败: {e}")
        
        return chunks
    
    def _extract_frontmatter(self, content: str) -> Optional[Dict[str, Any]]:
        """提取YAML frontmatter"""
        try:
            if content.startswith('---\n'):
                end_index = content.find('\n---\n', 4)
                if end_index != -1:
                    frontmatter_text = content[4:end_index]
                    # 简单的YAML解析（仅支持基本键值对）
                    frontmatter = {}
                    for line in frontmatter_text.split('\n'):
                        if ':' in line:
                            key, value = line.split(':', 1)
                            key = key.strip()
                            value = value.strip().strip('"\'')
                            frontmatter[key] = value
                    return frontmatter
        except Exception as e:
            self.logger.warning(f"解析frontmatter失败: {e}")
        
        return None
    
    def _remove_frontmatter(self, content: str) -> str:
        """移除frontmatter"""
        if content.startswith('---\n'):
            end_index = content.find('\n---\n', 4)
            if end_index != -1:
                return content[end_index + 5:]
        return content
    
    def _extract_first_header(self, content: str) -> Optional[str]:
        """提取第一个标题"""
        match = re.search(r'^#+\s+(.+)$', content, re.MULTILINE)
        return match.group(1).strip() if match else None
    
    def _extract_plain_text(self, content: str) -> str:
        """提取纯文本（移除Markdown语法）"""
        # 移除代码块
        if not self.preserve_code_blocks:
            content = re.sub(r'```[\s\S]*?```', '', content)
            content = re.sub(r'`[^`]+`', '', content)
        
        # 移除链接，保留文本
        content = re.sub(r'\[([^\]]+)\]\([^)]+\)', r'\1', content)
        
        # 移除图片
        content = re.sub(r'!\[([^\]]*)\]\([^)]+\)', r'\1', content)
        
        # 移除标题标记
        content = re.sub(r'^#+\s+', '', content, flags=re.MULTILINE)
        
        # 移除粗体和斜体标记
        content = re.sub(r'\*\*([^*]+)\*\*', r'\1', content)
        content = re.sub(r'\*([^*]+)\*', r'\1', content)
        content = re.sub(r'__([^_]+)__', r'\1', content)
        content = re.sub(r'_([^_]+)_', r'\1', content)
        
        # 移除列表标记
        content = re.sub(r'^\s*[-*+]\s+', '', content, flags=re.MULTILINE)
        content = re.sub(r'^\s*\d+\.\s+', '', content, flags=re.MULTILINE)
        
        # 移除引用标记
        content = re.sub(r'^>\s*', '', content, flags=re.MULTILINE)
        
        return content
    
    def _extract_chunks_by_headers(self, content: str, base_metadata: dict) -> List[DocumentChunk]:
        """按标题分块"""
        chunks = []
        
        # 按标题分割内容
        sections = self._split_by_headers(content)
        
        for section_idx, section in enumerate(sections):
            if section['content'].strip() and len(section['content'].strip()) >= self.min_section_length:
                # 组合标题和内容
                text_parts = []
                if section['title']:
                    text_parts.append(section['title'])
                text_parts.append(section['content'])
                
                section_text = '\n\n'.join(text_parts)
                cleaned_text = self._clean_text(self._extract_plain_text(section_text))
                
                chunk_metadata = self._create_chunk_metadata(
                    base_metadata,
                    {
                        'section_title': section['title'],
                        'section_level': section['level'],
                        'section_number': section_idx + 1,
                        'chunk_type': 'section'
                    }
                )
                
                chunk = DocumentChunk(
                    text=cleaned_text,
                    metadata=chunk_metadata,
                    chunk_id=f"section_{section_idx + 1}",
                    section_title=section['title'],
                    chunk_type='section'
                )
                chunks.append(chunk)
        
        return chunks
    
    def _extract_chunks_by_paragraphs(self, content: str, base_metadata: dict) -> List[DocumentChunk]:
        """按段落分块"""
        chunks = []
        
        # 按双换行分割段落
        paragraphs = content.split('\n\n')
        paragraph_counter = 0
        
        for paragraph in paragraphs:
            paragraph = paragraph.strip()
            if paragraph and len(paragraph) >= self.min_section_length:
                paragraph_counter += 1
                
                cleaned_text = self._clean_text(self._extract_plain_text(paragraph))
                
                chunk_metadata = self._create_chunk_metadata(
                    base_metadata,
                    {
                        'paragraph_number': paragraph_counter,
                        'chunk_type': 'paragraph'
                    }
                )
                
                chunk = DocumentChunk(
                    text=cleaned_text,
                    metadata=chunk_metadata,
                    chunk_id=f"paragraph_{paragraph_counter}",
                    chunk_type='paragraph'
                )
                chunks.append(chunk)
        
        return chunks
    
    def _split_by_headers(self, content: str) -> List[Dict[str, Any]]:
        """按标题分割内容"""
        sections = []
        lines = content.split('\n')
        current_section = {'title': None, 'content': [], 'level': 0}
        
        for line in lines:
            header_match = re.match(r'^(#+)\s+(.+)$', line)
            
            if header_match:
                # 保存当前章节
                if current_section['content']:
                    current_section['content'] = '\n'.join(current_section['content'])
                    sections.append(current_section)
                
                # 开始新章节
                level = len(header_match.group(1))
                title = header_match.group(2).strip()
                current_section = {
                    'title': title,
                    'content': [],
                    'level': level
                }
            else:
                # 添加到当前章节内容
                current_section['content'].append(line)
        
        # 处理最后一个章节
        if current_section['content']:
            current_section['content'] = '\n'.join(current_section['content'])
            sections.append(current_section)
        
        return sections
