import os
from typing import List, Dict, Optional
from pypdf import PdfReader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.schema import Document
import logging
from pathlib import Path
import hashlib

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

class PDFService:
    """Robust PDF processing service with comprehensive error handling."""
    
    def __init__(self, 
                 chunk_size: int = 1000, 
                 chunk_overlap: int = 200,
                 max_pages: int = 1000):
        """
        Initialize PDF service with configurable processing parameters.
        
        Args:
            chunk_size: Character length of text chunks
            chunk_overlap: Overlap between chunks
            max_pages: Safety limit for PDF pages
        """
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.max_pages = max_pages
        
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=self.chunk_size,
            chunk_overlap=self.chunk_overlap,
            length_function=len,
            keep_separator=True,
            separators=["\n\n", "\n", " ", ""]
        )

    def extract_text_from_pdf(self, pdf_path: str) -> str:
        """
        Safely extract text from PDF with comprehensive error handling.
        
        Args:
            pdf_path: Path to PDF file
            
        Returns:
            Extracted text as single string
            
        Raises:
            ValueError: For invalid files or extraction failures
        """
        try:
            if not os.path.exists(pdf_path):
                raise FileNotFoundError(f"PDF file not found: {pdf_path}")
                
            file_size = os.path.getsize(pdf_path)
            if file_size > 50 * 1024 * 1024:
                raise ValueError(f"PDF file too large ({(file_size/1024/1024):.2f}MB > 50MB limit)")
                
            text = ""
            with open(pdf_path, 'rb') as file:
                reader = PdfReader(file)
                
                if len(reader.pages) > self.max_pages:
                    raise ValueError(f"PDF has too many pages ({len(reader.pages)} > {self.max_pages} limit)")
                
                for i, page in enumerate(reader.pages):
                    try:
                        page_text = page.extract_text()
                        if page_text:
                            text += f"{page_text}\n"
                    except Exception as page_error:
                        logger.warning(f"Error extracting page {i+1}: {str(page_error)}")
                        continue
                        
            if not text.strip():
                raise ValueError("PDF text extraction returned empty content")
                
            return text.strip()
            
        except Exception as e:
            logger.error(f"Failed to extract text from {pdf_path}: {str(e)}")
            raise ValueError(f"PDF processing error: {str(e)}")

    def split_text_into_chunks(self, text: str, metadata: Dict = None) -> List[Document]:
        """
        Split text into chunks with enhanced metadata handling.
        
        Args:
            text: Text content to split
            metadata: Base metadata for all chunks
            
        Returns:
            List of Document objects with chunked text
        """
        if not text.strip():
            logger.warning("Empty text provided for chunking")
            return []
            
        try:
            base_metadata = metadata.copy() if metadata else {}
            base_metadata['total_chars'] = len(text)
            
            doc_hash = hashlib.md5(text.encode()).hexdigest()[:8]
            base_metadata['doc_hash'] = doc_hash
            
            chunks = self.text_splitter.split_text(text)
            
            documents = []
            for i, chunk in enumerate(chunks):
                chunk_metadata = base_metadata.copy()
                chunk_metadata.update({
                    'chunk_id': i,
                    'chunk_size': len(chunk),
                    'is_truncated': len(chunk) >= self.chunk_size
                })
                documents.append(Document(
                    page_content=chunk,
                    metadata=chunk_metadata
                ))
                
            logger.info(f"Split text into {len(documents)} chunks (avg: {len(text)/len(documents):.0f} chars/chunk)")
            return documents
            
        except Exception as e:
            logger.error(f"Text chunking failed: {str(e)}")
            raise ValueError(f"Text processing error: {str(e)}")

    def process_pdf(self, pdf_path: str, additional_metadata: Dict = None) -> List[Document]:
        """
        Full PDF processing pipeline with error recovery.
        
        Args:
            pdf_path: Path to PDF file
            additional_metadata: Extra metadata to include
            
        Returns:
            List of processed document chunks
            
        Raises:
            ValueError: For processing failures
        """
        try:
            text = self.extract_text_from_pdf(pdf_path)
            
            metadata = {
                'source': pdf_path,
                'filename': os.path.basename(pdf_path),
                'file_type': 'pdf',
                'processor': 'PDFService'
            }
            
            if additional_metadata:
                metadata.update(additional_metadata)
            
            return self.split_text_into_chunks(text, metadata)
            
        except Exception as e:
            logger.error(f"Failed to process PDF {pdf_path}: {str(e)}")
            raise ValueError(f"PDF processing failed: {str(e)}")

    def process_multiple_pdfs(self, pdf_paths: List[str]) -> List[Document]:
        """
        Process multiple PDFs with fault tolerance.
        
        Args:
            pdf_paths: List of PDF file paths
            
        Returns:
            Combined list of all document chunks
        """
        all_documents = []
        failed_files = []
        
        for pdf_path in pdf_paths:
            try:
                docs = self.process_pdf(pdf_path)
                all_documents.extend(docs)
                logger.info(f"Processed {pdf_path}: {len(docs)} chunks")
            except Exception as e:
                failed_files.append(pdf_path)
                logger.warning(f"Skipped {pdf_path}: {str(e)}")
                continue
                
        if failed_files:
            logger.warning(f"Failed to process {len(failed_files)} files: {failed_files}")
            
        return all_documents

    @staticmethod
    def validate_pdf_path(pdf_path: str) -> bool:
        """Validate PDF file path and extension."""
        try:
            return (
                os.path.exists(pdf_path) and 
                os.path.isfile(pdf_path) and 
                pdf_path.lower().endswith('.pdf')
            )
        except:
            return False