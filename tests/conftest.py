import pytest
import tempfile
import shutil
from unittest.mock import patch
from src.config import Config
import sys
import os
from pathlib import Path

root_dir = Path(__file__).parent.parent
sys.path.insert(0, str(root_dir))

from src.config import Config

@pytest.fixture
def mock_config():
    """Fixture to mock configuration for testing."""
    with patch.dict('os.environ', {
        'OPENAI_API_KEY': 'test_key',
        'OPENWEATHERMAP_API_KEY': 'test_weather_key',
        'LANGCHAIN_API_KEY': 'test_langchain_key'
    }):
        yield

@pytest.fixture
def temp_db_dir():
    """Fixture for temporary vector database directory."""
    temp_dir = tempfile.mkdtemp()
    with patch('src.config.Config.CHROMA_PERSIST_DIRECTORY', temp_dir):
        yield temp_dir
    shutil.rmtree(temp_dir, ignore_errors=True)

@pytest.fixture
def mock_llm():
    """Fixture to mock the LLM."""
    with patch('src.pipeline.langgraph_pipeline.ChatOpenAI') as mock:
        mock_instance = mock.return_value
        mock_instance.return_value.content = "Mocked LLM response"
        yield mock_instance

@pytest.fixture
def mock_weather_service():
    """Fixture to mock the weather service."""
    with patch('src.pipeline.langgraph_pipeline.WeatherService') as mock:
        mock_instance = mock.return_value
        mock_instance.get_weather_data.return_value = {
            'status': 'success',
            'city': 'Test City',
            'temperature': 20
        }
        yield mock_instance

@pytest.fixture
def mock_vector_service():
    """Fixture to mock the vector service."""
    with patch('src.pipeline.langgraph_pipeline.VectorService') as mock:
        mock_instance = mock.return_value
        mock_instance.similarity_search.return_value = [{
            'content': 'Test document content',
            'metadata': {'source': 'test.pdf'},
            'score': 0.9
        }]
        yield mock_instance