import re
from typing import Dict, Any, List
from langgraph.graph import StateGraph, END
from langchain_openai import ChatOpenAI
from langchain.schema import HumanMessage, SystemMessage
from src.config import Config
from src.services.weather_service import WeatherService
from src.services.vector_service import VectorService

class PipelineState:
    """State class for the LangGraph pipeline."""
    
    def __init__(self, **kwargs):
        self.query: str = kwargs.get("query", "")
        self.intent: str = kwargs.get("intent", "")
        self.weather_data: Dict = kwargs.get("weather_data", {})
        self.retrieved_docs: List[Dict] = kwargs.get("retrieved_docs", [])
        self.response: str = kwargs.get("response", "")
        self.error: str = kwargs.get("error", "")
        self.success: bool = kwargs.get("success", True)

class AIAgentPipeline:
    """AI Agent Pipeline using LangGraph for decision making and processing."""
    
    def __init__(self):
        try:
            Config.validate_config(required_services=["openai"])
            
            self.llm = ChatOpenAI(
                model=Config.LLM_MODEL,
                temperature=0.1,
                api_key=Config.OPENAI_API_KEY
            )
            
            if Config.OPENWEATHERMAP_API_KEY:
                self.weather_service = WeatherService()
            else:
                self.weather_service = None
                print("Weather service disabled - OPENWEATHERMAP_API_KEY not set")
            
            self.vector_service = VectorService()
            
            self.graph = self._build_graph()
            
        except Exception as e:
            raise RuntimeError(f"Error initializing pipeline: {str(e)}")

    
    def _build_graph(self) -> StateGraph:
        """Build the LangGraph workflow."""
        
        workflow = StateGraph(dict)
        
        workflow.add_node("classify_intent", self._classify_intent_node)
        workflow.add_node("fetch_weather", self._fetch_weather_node)
        workflow.add_node("retrieve_documents", self._retrieve_documents_node)
        workflow.add_node("generate_response", self._generate_response_node)
        
        workflow.set_entry_point("classify_intent")
        
        workflow.add_conditional_edges(
            "classify_intent",
            self._route_based_on_intent,
            {
                "weather": "fetch_weather",
                "document": "retrieve_documents",
                "general": "generate_response"
            }
        )
        
        workflow.add_edge("fetch_weather", "generate_response")
        workflow.add_edge("retrieve_documents", "generate_response")
        workflow.add_edge("generate_response", END)
        
        return workflow.compile()
    
    def _classify_intent_node(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Node to classify user intent (weather, document, or general)."""
        
        query = state.get("query", "").lower()
        
        weather_keywords = [
            "weather", "temperature", "rain", "sunny", "cloudy", "humidity",
            "humid", "forecast", "climate", "cold", "hot", "wind", "snow", "storm"
        ]
        
        document_keywords = [
            "document", "pdf", "file", "paper", "report", "article",
            "research", "study", "analysis", "content", "text"
        ]
        
        if any(keyword in query for keyword in weather_keywords):
            state["intent"] = "weather"
        elif any(keyword in query for keyword in document_keywords):
            state["intent"] = "document"
        else:
            state["intent"] = "document"
        
        print(f"Classified intent: {state['intent']} for query: {query}")
        return state
    
    def _route_based_on_intent(self, state: Dict[str, Any]) -> str:
        """Route to appropriate node based on classified intent."""
        return state["intent"]
    
    def _fetch_weather_node(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Node to fetch weather data."""
        
        query = state["query"]
        
        city_match = re.search(r'weather.*?(?:in|for|of)\s+([a-zA-Z\s]+)', query, re.IGNORECASE)
        if not city_match:
            city_match = re.search(r'([a-zA-Z\s]+)\s+weather', query, re.IGNORECASE)
        
        if city_match:
            city = city_match.group(1).strip()
        else:
            city = "London"
        
        print(f"Fetching weather for city: {city}")
        
        weather_data = self.weather_service.get_weather_data(city)
        state["weather_data"] = weather_data
        
        return state
    
    def _retrieve_documents_node(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Node to retrieve relevant documents from vector database."""
        
        query = state["query"]
        
        print(f"Retrieving documents for query: {query}")
        
        retrieved_docs = self.vector_service.similarity_search(query, n_results=3)
        state["retrieved_docs"] = retrieved_docs
        
        return state
    
    def _generate_response_node(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Node to generate final response using LLM."""
        
        query = state["query"]
        intent = state["intent"]
        
        try:
            if intent == "weather":
                response = self._generate_weather_response(state)
            elif intent == "document":
                response = self._generate_document_response(state)
            else:
                response = self._generate_general_response(state)
            
            state["response"] = response
            
        except Exception as e:
            state["error"] = f"Error generating response: {str(e)}"
            state["response"] = "I apologize, but I encountered an error while processing your request."
            state["success"] = False
        
        return state
    
    def _generate_weather_response(self, state: Dict[str, Any]) -> str:
        """Generate response for weather queries."""
        
        weather_data = state["weather_data"]
        
        if weather_data.get("status") == "error":
            return f"I couldn't fetch the weather data: {weather_data.get('error', 'Unknown error')}"
        
        formatted_weather = self.weather_service.format_weather_response(weather_data)
        
        system_message = SystemMessage(content="""
        You are a helpful weather assistant. Based on the weather data provided, 
        give a conversational and informative response about the current weather conditions.
        Be friendly and include relevant details that would be useful to the user.
        """)
        
        human_message = HumanMessage(content=f"""
        User asked: {state['query']}
        Weather data: {formatted_weather}
        
        Please provide a friendly and informative response about the weather.
        """)
        
        response = self.llm([system_message, human_message])
        return response.content
    
    def _generate_document_response(self, state: Dict[str, Any]) -> str:
        """Generate response for document-based queries using RAG."""
        
        retrieved_docs = state["retrieved_docs"]
        
        if not retrieved_docs:
            return "I couldn't find any relevant information in the documents to answer your question."
        
        context = "\n\n".join([
            f"Document {i+1}:\n{doc['content']}"
            for i, doc in enumerate(retrieved_docs)
        ])
        
        system_message = SystemMessage(content="""
        You are a helpful assistant that answers questions based on provided document context.
        Use only the information from the given context to answer questions.
        If the context doesn't contain enough information to answer the question,
        say so clearly. Be accurate and cite relevant parts of the context when possible.
        """)
        
        human_message = HumanMessage(content=f"""
        User question: {state['query']}
        
        Context from documents:
        {context}
        
        Please answer the user's question based on the provided context.
        """)
        
        response = self.llm([system_message, human_message])
        return response.content
    
    def _generate_general_response(self, state: Dict[str, Any]) -> str:
        """Generate response for general queries."""
        
        system_message = SystemMessage(content="""
        You are a helpful AI assistant. Answer the user's question in a friendly and informative way.
        """)
        
        human_message = HumanMessage(content=state["query"])
        
        response = self.llm([system_message, human_message])
        return response.content
    
    def process_query(self, query: str) -> Dict[str, Any]:
        """
        Process a user query through the LangGraph pipeline.
        
        Args:
            query (str): User query
            
        Returns:
            Dict[str, Any]: Pipeline result with response and metadata
        """
        
        initial_state = {
            "query": query,
            "intent": "",
            "weather_data": {},
            "retrieved_docs": [],
            "response": "",
            "error": ""
        }
        
        try:
            result = self.graph.invoke(initial_state)
            
            if result.get("error"):
                return {
                    "success": False,
                    "response": result.get("response", "I encountered an error processing your request."),
                    "error": result["error"],
                    "intent": result.get("intent", "unknown"),
                    "weather_data": result.get("weather_data", {}),
                    "retrieved_docs": result.get("retrieved_docs", [])
                }
                
            return {
                "success": True,
                "response": result.get("response", "No response generated"),
                "intent": result.get("intent", "unknown"),
                "weather_data": result.get("weather_data", {}),
                "retrieved_docs": result.get("retrieved_docs", []),
                "error": result.get("error", "")
            }
            
        except Exception as e:
            return {
                "success": False,
                "response": "I apologize, but I encountered an error while processing your request.",
                "error": str(e),
                "intent": "unknown",
                "weather_data": {},
                "retrieved_docs": []
            }