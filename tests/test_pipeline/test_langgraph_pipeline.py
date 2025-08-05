import pytest
from unittest.mock import patch, MagicMock
from src.pipeline.langgraph_pipeline import AIAgentPipeline, PipelineState
from src.config import Config

@pytest.fixture
def mock_config():
    with patch('src.config.Config.validate_config') as mock:
        mock.return_value = True
        yield mock

@pytest.fixture
def mock_llm():
    with patch('src.pipeline.langgraph_pipeline.ChatOpenAI') as mock:
        mock_instance = mock.return_value
        mock_instance.return_value.content = "Mocked response"
        yield mock_instance

@pytest.fixture
def mock_weather_service():
    with patch('src.pipeline.langgraph_pipeline.WeatherService') as mock:
        mock_instance = mock.return_value
        mock_instance.get_weather_data.return_value = {
            'status': 'success',
            'city': 'Test City',
            'temperature': 20,
            'description': 'sunny'
        }
        mock_instance.format_weather_response.return_value = "Formatted weather data"
        yield mock_instance

@pytest.fixture
def mock_vector_service():
    with patch('src.pipeline.langgraph_pipeline.VectorService') as mock:
        mock_instance = mock.return_value
        mock_instance.similarity_search.return_value = [{
            'content': 'Test document content',
            'metadata': {'source': 'test.pdf'},
            'score': 0.9
        }]
        yield mock_instance

class TestPipelineState:
    """Test cases for PipelineState model."""
    
    def test_pipeline_state_defaults(self):
        """Test PipelineState default values."""
        state = PipelineState()
        assert state.query == ""
        assert state.intent == ""
        assert state.weather_data == {}
        assert state.retrieved_docs == []
        assert state.response == ""
        assert state.error == ""
        assert state.success is True

    def test_pipeline_state_with_values(self):
        """Test PipelineState with provided values."""
        state = PipelineState(
            query="test query",
            intent="weather",
            response="test response"
        )
        assert state.query == "test query"
        assert state.intent == "weather"
        assert state.response == "test response"

class TestAIAgentPipeline:
    """Test cases for AIAgentPipeline."""
    
    def test_initialization(self, mock_config, mock_llm, mock_weather_service, mock_vector_service):
        """Test pipeline initialization."""
        pipeline = AIAgentPipeline()
        assert pipeline.llm is not None
        assert pipeline.weather_service is not None
        assert pipeline.vector_service is not None
        assert pipeline.graph is not None
        mock_config.assert_called_once_with(required_services=["openai"])
    
    @pytest.mark.parametrize("query,expected_intent", [
        ("What's the weather in London?", "weather"),
        ("Tell me about the documents", "document"),
        ("Explain AI", "document"),
        ("How humid is it in Paris?", "weather"),
        ("What does this PDF say?", "document")
    ])
    def test_classify_intent(self, mock_config, mock_llm, query, expected_intent):
        """Test intent classification."""
        pipeline = AIAgentPipeline()
        state = {"query": query}
        result = pipeline._classify_intent_node(state)
        assert result["intent"] == expected_intent
    
    def test_route_based_on_intent(self, mock_config, mock_llm):
        """Test routing based on intent."""
        pipeline = AIAgentPipeline()
        
        state = {"intent": "weather"}
        route = pipeline._route_based_on_intent(state)
        assert route == "weather"
        
        state = {"intent": "document"}
        route = pipeline._route_based_on_intent(state)
        assert route == "document"
        
        state = {"intent": "general"}
        route = pipeline._route_based_on_intent(state)
        assert route == "general"
    
    def test_fetch_weather_node(self, mock_config, mock_llm, mock_weather_service):
        """Test weather data fetching."""
        pipeline = AIAgentPipeline()
        state = {
            "query": "What's the weather in London?",
            "intent": "weather"
        }
        
        result = pipeline._fetch_weather_node(state)
        assert result["weather_data"]["status"] == 'success'
        mock_weather_service.get_weather_data.assert_called_once()
    
    def test_retrieve_documents_node(self, mock_config, mock_llm, mock_vector_service):
        """Test document retrieval."""
        pipeline = AIAgentPipeline()
        state = {
            "query": "Tell me about AI",
            "intent": "document"
        }
        
        result = pipeline._retrieve_documents_node(state)
        assert len(result["retrieved_docs"]) == 1
        mock_vector_service.similarity_search.assert_called_once_with(
            "Tell me about AI", n_results=3
        )
        
    def test_generate_weather_response(self, mock_config, mock_llm, mock_weather_service):
        """Test weather response generation."""
        mock_llm.return_value.content = "Weather in London: 15°C, cloudy"
        
        pipeline = AIAgentPipeline()
        state = {
            "query": "What's the weather in London?",
            "weather_data": {
                'status': 'success',
                'city': 'London',
                'country': 'GB',
                'temperature': 15,
                'feels_like': 14,
                'description': 'cloudy',
                'humidity': 78,
                'pressure': 1012,
                'wind_speed': 5,
                'visibility': 10000
            }
        }

        response = pipeline._generate_weather_response(state)
        assert "Weather in London" in response
    
    def test_process_query_weather(self, mock_config, mock_llm, mock_weather_service):
        """Test complete query processing for weather."""
        pipeline = AIAgentPipeline()
        
        mock_weather_service.get_weather_data.return_value = {
            'status': 'success',
            'city': 'London',
            'country': 'GB',
            'temperature': 15,
            'description': 'cloudy'
        }
        mock_llm.return_value.content = "Weather in London: 15°C, cloudy"

        result = pipeline.process_query("What's the weather in London?")
        
        assert result["success"] is True
        assert result["intent"] == "weather"
        assert "London" in result["response"]

    def test_process_query_document(self, mock_config, mock_llm, mock_vector_service):
        """Test complete query processing for documents."""
        pipeline = AIAgentPipeline()
        
        mock_vector_service.similarity_search.return_value = [{
            'content': 'Test document content about AI',
            'metadata': {'source': 'test.pdf'},
            'score': 0.9
        }]
        mock_llm.return_value.content = "AI is a field of computer science..."

        result = pipeline.process_query("Tell me about AI")
        
        assert result["success"] is True
        assert result["intent"] == "document"
        assert "AI" in result["response"]
        assert len(result["retrieved_docs"]) == 1

    def test_process_query_error_handling(self, mock_config, mock_llm):
        """Test error handling in query processing."""
        pipeline = AIAgentPipeline()
        
        with patch.object(pipeline.weather_service, 'get_weather_data', side_effect=Exception("Test error")):
            result = pipeline.process_query("What's the weather in London?")
            
            assert result["success"] is False
            assert "error" in result
            assert "Test error" in result["error"]