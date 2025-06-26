"""
纯文本文档解析器

支持纯文本格式文档的文本提取、元数据提取和智能分块。
"""

import logging
from typing import List, Optional
from pathlib import Path
from .base_parser import DocumentParser, DocumentMetadata, DocumentChunk


class TextParser(DocumentParser):
    """纯文本文档解析器"""
    
    def __init__(self, config=None):
        super().__init__(config)
        self.chunk_size = self.config.get('chunk_size', 1000)
        self.chunk_overlap = self.config.get('chunk_overlap', 100)
        self.detect_encoding = self.config.get('detect_encoding', True)
        self.min_chunk_length = self.config.get('min_chunk_length', 50)
    
    def can_parse(self, file_path: str) -> bool:
        """检查是否能解析文本文件"""
        extension = Path(file_path).suffix.lower()
        return extension == '.txt' or extension == ''
    
    def get_supported_extensions(self) -> List[str]:
        """获取支持的文件扩展名"""
        return ['.txt']
    
    def extract_metadata(self, file_path: str) -> DocumentMetadata:
        """提取文本元数据"""
        metadata = DocumentMetadata(format_type='text')
        
        try:
            # 文件基本信息
            file_path_obj = Path(file_path)
            metadata.file_size = file_path_obj.stat().st_size
            
            # 尝试从文件名提取标题
            metadata.title = file_path_obj.stem
            
            # 读取文件内容进行统计
            content = self._read_file_content(file_path)
            if content:
                lines = content.splitlines()
                words = content.split()
                
                metadata.word_count = len(words)
                metadata.extra_metadata = {
                    'line_count': len(lines),
                    'character_count': len(content),
                    'encoding': self._detect_file_encoding(file_path)
                }
                
                # 尝试从第一行提取标题（如果第一行较短且像标题）
                if lines and len(lines[0].strip()) < 100 and not lines[0].strip().endswith('.'):
                    potential_title = lines[0].strip()
                    if potential_title and len(potential_title.split()) <= 10:
                        metadata.title = potential_title
            
        except Exception as e:
            self.logger.error(f"提取文本元数据失败: {e}")
        
        return metadata
    
    def extract_text(self, file_path: str) -> str:
        """提取文本全文"""
        try:
            content = self._read_file_content(file_path)
            return self._clean_text(content) if content else ""
        except Exception as e:
            self.logger.error(f"提取文本失败: {e}")
            return ""
    
    def extract_chunks(self, file_path: str) -> List[DocumentChunk]:
        """提取文本分块"""
        chunks = []
        base_metadata = {'file_name': Path(file_path).name, 'format_type': 'text'}
        
        try:
            content = self._read_file_content(file_path)
            if not content:
                return chunks
            
            # 按段落分块（优先）或按字符数分块
            if '\n\n' in content:
                chunks = self._extract_chunks_by_paragraphs(content, base_metadata)
            else:
                chunks = self._extract_chunks_by_size(content, base_metadata)
            
        except Exception as e:
            self.logger.error(f"提取文本分块失败: {e}")
        
        return chunks
    
    def _read_file_content(self, file_path: str) -> Optional[str]:
        """读取文件内容，自动检测编码"""
        encodings = ['utf-8', 'gbk', 'gb2312', 'gb18030', 'big5', 'latin1']
        
        if self.detect_encoding:
            # 尝试检测编码
            try:
                import chardet
                with open(file_path, 'rb') as f:
                    raw_data = f.read()
                detected = chardet.detect(raw_data)
                if detected['encoding'] and detected['confidence'] > 0.7:
                    encodings.insert(0, detected['encoding'])
            except ImportError:
                pass
        
        # 尝试不同编码读取文件
        for encoding in encodings:
            try:
                with open(file_path, 'r', encoding=encoding, errors='ignore') as f:
                    content = f.read()
                    # 检查是否有乱码
                    if '�' not in content or encoding == encodings[-1]:
                        return content
            except Exception:
                continue
        
        return None
    
    def _detect_file_encoding(self, file_path: str) -> str:
        """检测文件编码"""
        try:
            import chardet
            with open(file_path, 'rb') as f:
                raw_data = f.read(10000)  # 读取前10KB检测编码
            detected = chardet.detect(raw_data)
            return detected['encoding'] if detected['encoding'] else 'unknown'
        except ImportError:
            return 'utf-8'
        except Exception:
            return 'unknown'
    
    def _extract_chunks_by_paragraphs(self, content: str, base_metadata: dict) -> List[DocumentChunk]:
        """按段落分块"""
        chunks = []
        paragraphs = content.split('\n\n')
        
        current_chunk = []
        current_length = 0
        chunk_counter = 0
        
        for paragraph in paragraphs:
            paragraph = paragraph.strip()
            if not paragraph:
                continue
            
            paragraph_length = len(paragraph)
            
            # 如果当前块加上新段落超过限制，先保存当前块
            if current_length + paragraph_length > self.chunk_size and current_chunk:
                chunk_text = '\n\n'.join(current_chunk)
                if len(chunk_text) >= self.min_chunk_length:
                    chunk = self._create_text_chunk(chunk_text, base_metadata, chunk_counter)
                    chunks.append(chunk)
                    chunk_counter += 1
                
                # 重叠处理：保留最后一个段落
                if self.chunk_overlap > 0 and current_chunk:
                    overlap_text = current_chunk[-1]
                    if len(overlap_text) <= self.chunk_overlap:
                        current_chunk = [overlap_text]
                        current_length = len(overlap_text)
                    else:
                        current_chunk = []
                        current_length = 0
                else:
                    current_chunk = []
                    current_length = 0
            
            current_chunk.append(paragraph)
            current_length += paragraph_length
        
        # 处理最后一个块
        if current_chunk:
            chunk_text = '\n\n'.join(current_chunk)
            if len(chunk_text) >= self.min_chunk_length:
                chunk = self._create_text_chunk(chunk_text, base_metadata, chunk_counter)
                chunks.append(chunk)
        
        return chunks
    
    def _extract_chunks_by_size(self, content: str, base_metadata: dict) -> List[DocumentChunk]:
        """按字符数分块"""
        chunks = []
        chunk_counter = 0
        
        start = 0
        content_length = len(content)
        
        while start < content_length:
            end = start + self.chunk_size
            
            # 如果不是最后一块，尝试在单词边界分割
            if end < content_length:
                # 向后查找空格或换行符
                for i in range(end, min(end + 100, content_length)):
                    if content[i] in [' ', '\n', '\t']:
                        end = i
                        break
            
            chunk_text = content[start:end].strip()
            
            if len(chunk_text) >= self.min_chunk_length:
                chunk = self._create_text_chunk(chunk_text, base_metadata, chunk_counter)
                chunks.append(chunk)
                chunk_counter += 1
            
            # 计算下一个块的起始位置（考虑重叠）
            start = max(start + 1, end - self.chunk_overlap)
        
        return chunks
    
    def _create_text_chunk(self, text: str, base_metadata: dict, chunk_id: int) -> DocumentChunk:
        """创建文本分块"""
        cleaned_text = self._clean_text(text)
        
        chunk_metadata = self._create_chunk_metadata(
            base_metadata,
            {
                'chunk_number': chunk_id + 1,
                'chunk_type': 'text',
                'character_count': len(text),
                'word_count': len(text.split())
            }
        )
        
        return DocumentChunk(
            text=cleaned_text,
            metadata=chunk_metadata,
            chunk_id=f"text_{chunk_id + 1}",
            chunk_type='text'
        )
