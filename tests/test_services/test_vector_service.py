import pytest
from unittest.mock import patch, MagicMock
from langchain.schema import Document
from src.services.vector_service import VectorService

class TestVectorService:
    """Test cases for VectorService."""
    
    def test_add_documents(self, temp_db_dir):
        """Test adding documents to vector database."""
        service = VectorService()
        documents = [
            Document(page_content="Test content 1", metadata={"source": "test1.pdf"}),
            Document(page_content="Test content 2", metadata={"source": "test2.pdf"})
        ]
        result = service.add_documents(documents)
        assert result is True
        info = service.get_collection_info()
        assert info["count"] == 2
    
    def test_similarity_search(self, temp_db_dir):
        """Test similarity search functionality."""
        service = VectorService()
        documents = [
            Document(page_content="Machine learning is a subset of AI", metadata={"source": "ml.pdf"}),
            Document(page_content="Deep learning uses neural networks", metadata={"source": "dl.pdf"})
        ]
        service.add_documents(documents)
        
        results = service.similarity_search("artificial intelligence")
        assert len(results) > 0
        assert "content" in results[0]
        assert "metadata" in results[0]
    
    def test_reset_collection(self, temp_db_dir):
        """Test collection reset functionality."""
        service = VectorService()
        documents = [Document(page_content="Test content", metadata={"source": "test.pdf"})]
        service.add_documents(documents)
        assert service.get_collection_info()["count"] == 1
        
        result = service.reset_collection()
        assert result is True
        assert service.get_collection_info()["count"] == 0