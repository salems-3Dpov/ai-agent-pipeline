import pytest
import tempfile
import os
from unittest.mock import patch, MagicMock
from langchain.schema import Document
from src.services.pdf_service import PDFService

class TestPDFService:
    """Test cases for PDFService."""
    
    @pytest.fixture
    def pdf_service(self):
        return PDFService(chunk_size=500, chunk_overlap=50)
    
    def test_extract_text_from_pdf(self, pdf_service):
        """Test text extraction from PDF."""
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp_file:
            tmp_path = tmp_file.name
        
        try:
            with patch('src.services.pdf_service.PdfReader') as mock_reader:
                mock_page = MagicMock()
                mock_page.extract_text.return_value = "Sample text"
                mock_reader.return_value.pages = [mock_page]
                
                text = pdf_service.extract_text_from_pdf(tmp_path)
                assert text == "Sample text"
        finally:
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)
    
    def test_split_text_into_chunks(self, pdf_service):
        """Test text splitting into chunks."""
        long_text = " ".join(["word"] * 1000)
        chunks = pdf_service.split_text_into_chunks(long_text, {"source": "test.pdf"})
        assert len(chunks) > 1
        assert all(isinstance(chunk, Document) for chunk in chunks)
        assert all("chunk_id" in chunk.metadata for chunk in chunks)
    
    def test_process_pdf(self, pdf_service):
        """Test full PDF processing."""
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp_file:
            tmp_path = tmp_file.name
        
        try:
            with patch('src.services.pdf_service.PdfReader') as mock_reader:
                mock_page = MagicMock()
                mock_page.extract_text.return_value = "Sample text"
                mock_reader.return_value.pages = [mock_page]
                
                docs = pdf_service.process_pdf(tmp_path)
                assert len(docs) > 0
                assert docs[0].metadata["source"] == tmp_path
        finally:
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)