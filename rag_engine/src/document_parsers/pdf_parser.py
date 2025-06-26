"""
PDF文档解析器

支持PDF文档的文本提取、元数据提取和智能分块。
"""

import logging
from typing import List, Optional
from pathlib import Path
from .base_parser import DocumentParser, DocumentMetadata, DocumentChunk

try:
    import pdfplumber
    import PyPDF2
    PDFPLUMBER_AVAILABLE = True
    PYPDF2_AVAILABLE = True
except ImportError as e:
    logging.warning(f"PDF解析库导入失败: {e}")
    PDFPLUMBER_AVAILABLE = False
    PYPDF2_AVAILABLE = False


class PDFParser(DocumentParser):
    """PDF文档解析器"""
    
    def __init__(self, config=None):
        super().__init__(config)
        self.use_pdfplumber = PDFPLUMBER_AVAILABLE and self.config.get('use_pdfplumber', True)
        self.extract_images = self.config.get('extract_images', False)
        self.min_page_text_length = self.config.get('min_page_text_length', 50)
    
    def can_parse(self, file_path: str) -> bool:
        """检查是否能解析PDF文件"""
        if not (PDFPLUMBER_AVAILABLE or PYPDF2_AVAILABLE):
            return False
        
        return Path(file_path).suffix.lower() == '.pdf'
    
    def get_supported_extensions(self) -> List[str]:
        """获取支持的文件扩展名"""
        return ['.pdf']
    
    def extract_metadata(self, file_path: str) -> DocumentMetadata:
        """提取PDF元数据"""
        metadata = DocumentMetadata(format_type='pdf')
        
        try:
            if self.use_pdfplumber and PDFPLUMBER_AVAILABLE:
                metadata = self._extract_metadata_pdfplumber(file_path, metadata)
            elif PYPDF2_AVAILABLE:
                metadata = self._extract_metadata_pypdf2(file_path, metadata)
            
            # 设置文件大小
            metadata.file_size = Path(file_path).stat().st_size
            
        except Exception as e:
            self.logger.error(f"提取PDF元数据失败: {e}")
        
        return metadata
    
    def _extract_metadata_pdfplumber(self, file_path: str, metadata: DocumentMetadata) -> DocumentMetadata:
        """使用pdfplumber提取元数据"""
        with pdfplumber.open(file_path) as pdf:
            # 基本信息
            metadata.page_count = len(pdf.pages)
            
            # PDF元数据
            if hasattr(pdf, 'metadata') and pdf.metadata:
                pdf_meta = pdf.metadata
                metadata.title = pdf_meta.get('Title')
                metadata.author = pdf_meta.get('Author')
                metadata.creator = pdf_meta.get('Creator')
                metadata.subject = pdf_meta.get('Subject')
                metadata.keywords = pdf_meta.get('Keywords')
                
                # 日期处理
                if 'CreationDate' in pdf_meta:
                    metadata.creation_date = self._parse_pdf_date(pdf_meta['CreationDate'])
                if 'ModDate' in pdf_meta:
                    metadata.modification_date = self._parse_pdf_date(pdf_meta['ModDate'])
        
        return metadata
    
    def _extract_metadata_pypdf2(self, file_path: str, metadata: DocumentMetadata) -> DocumentMetadata:
        """使用PyPDF2提取元数据"""
        with open(file_path, 'rb') as file:
            pdf_reader = PyPDF2.PdfReader(file)
            
            # 基本信息
            metadata.page_count = len(pdf_reader.pages)
            
            # PDF元数据
            if pdf_reader.metadata:
                pdf_meta = pdf_reader.metadata
                metadata.title = pdf_meta.get('/Title')
                metadata.author = pdf_meta.get('/Author')
                metadata.creator = pdf_meta.get('/Creator')
                metadata.subject = pdf_meta.get('/Subject')
                metadata.keywords = pdf_meta.get('/Keywords')
                
                # 日期处理
                if '/CreationDate' in pdf_meta:
                    metadata.creation_date = self._parse_pdf_date(pdf_meta['/CreationDate'])
                if '/ModDate' in pdf_meta:
                    metadata.modification_date = self._parse_pdf_date(pdf_meta['/ModDate'])
        
        return metadata
    
    def extract_text(self, file_path: str) -> str:
        """提取PDF全文"""
        try:
            if self.use_pdfplumber and PDFPLUMBER_AVAILABLE:
                return self._extract_text_pdfplumber(file_path)
            elif PYPDF2_AVAILABLE:
                return self._extract_text_pypdf2(file_path)
            else:
                raise Exception("没有可用的PDF解析库")
        except Exception as e:
            self.logger.error(f"提取PDF文本失败: {e}")
            return ""
    
    def _extract_text_pdfplumber(self, file_path: str) -> str:
        """使用pdfplumber提取文本"""
        text_parts = []
        
        with pdfplumber.open(file_path) as pdf:
            for page_num, page in enumerate(pdf.pages, 1):
                try:
                    page_text = page.extract_text()
                    if page_text and len(page_text.strip()) >= self.min_page_text_length:
                        text_parts.append(page_text)
                except Exception as e:
                    self.logger.warning(f"提取第{page_num}页文本失败: {e}")
        
        return self._clean_text('\n\n'.join(text_parts))
    
    def _extract_text_pypdf2(self, file_path: str) -> str:
        """使用PyPDF2提取文本"""
        text_parts = []
        
        with open(file_path, 'rb') as file:
            pdf_reader = PyPDF2.PdfReader(file)
            
            for page_num, page in enumerate(pdf_reader.pages, 1):
                try:
                    page_text = page.extract_text()
                    if page_text and len(page_text.strip()) >= self.min_page_text_length:
                        text_parts.append(page_text)
                except Exception as e:
                    self.logger.warning(f"提取第{page_num}页文本失败: {e}")
        
        return self._clean_text('\n\n'.join(text_parts))
    
    def extract_chunks(self, file_path: str) -> List[DocumentChunk]:
        """提取PDF分块（按页分块）"""
        chunks = []
        base_metadata = {'file_name': Path(file_path).name, 'format_type': 'pdf'}
        
        try:
            if self.use_pdfplumber and PDFPLUMBER_AVAILABLE:
                chunks = self._extract_chunks_pdfplumber(file_path, base_metadata)
            elif PYPDF2_AVAILABLE:
                chunks = self._extract_chunks_pypdf2(file_path, base_metadata)
            
        except Exception as e:
            self.logger.error(f"提取PDF分块失败: {e}")
        
        return chunks
    
    def _extract_chunks_pdfplumber(self, file_path: str, base_metadata: dict) -> List[DocumentChunk]:
        """使用pdfplumber按页提取分块"""
        chunks = []
        
        with pdfplumber.open(file_path) as pdf:
            for page_num, page in enumerate(pdf.pages, 1):
                try:
                    page_text = page.extract_text()
                    if page_text and len(page_text.strip()) >= self.min_page_text_length:
                        cleaned_text = self._clean_text(page_text)
                        
                        chunk_metadata = self._create_chunk_metadata(
                            base_metadata,
                            {
                                'page_label': str(page_num),
                                'page_number': page_num,
                                'chunk_type': 'page'
                            }
                        )
                        
                        chunk = DocumentChunk(
                            text=cleaned_text,
                            metadata=chunk_metadata,
                            chunk_id=f"page_{page_num}",
                            page_number=page_num,
                            chunk_type='page'
                        )
                        chunks.append(chunk)
                        
                except Exception as e:
                    self.logger.warning(f"处理第{page_num}页失败: {e}")
        
        return chunks
    
    def _extract_chunks_pypdf2(self, file_path: str, base_metadata: dict) -> List[DocumentChunk]:
        """使用PyPDF2按页提取分块"""
        chunks = []
        
        with open(file_path, 'rb') as file:
            pdf_reader = PyPDF2.PdfReader(file)
            
            for page_num, page in enumerate(pdf_reader.pages, 1):
                try:
                    page_text = page.extract_text()
                    if page_text and len(page_text.strip()) >= self.min_page_text_length:
                        cleaned_text = self._clean_text(page_text)
                        
                        chunk_metadata = self._create_chunk_metadata(
                            base_metadata,
                            {
                                'page_label': str(page_num),
                                'page_number': page_num,
                                'chunk_type': 'page'
                            }
                        )
                        
                        chunk = DocumentChunk(
                            text=cleaned_text,
                            metadata=chunk_metadata,
                            chunk_id=f"page_{page_num}",
                            page_number=page_num,
                            chunk_type='page'
                        )
                        chunks.append(chunk)
                        
                except Exception as e:
                    self.logger.warning(f"处理第{page_num}页失败: {e}")
        
        return chunks
    
    def _parse_pdf_date(self, date_str: str) -> Optional[str]:
        """解析PDF日期格式"""
        if not date_str:
            return None
        
        try:
            # PDF日期格式通常是 D:YYYYMMDDHHmmSSOHH'mm'
            if date_str.startswith('D:'):
                date_str = date_str[2:]
            
            # 提取年月日
            if len(date_str) >= 8:
                year = date_str[:4]
                month = date_str[4:6]
                day = date_str[6:8]
                return f"{year}-{month}-{day}"
        except Exception:
            pass
        
        return date_str
