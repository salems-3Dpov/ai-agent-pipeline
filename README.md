# AI Agent Pipeline

A sophisticated AI agent system built with LangGraph that combines document retrieval, weather services, and intelligent query processing. The pipeline automatically determines user intent and routes queries to appropriate services while maintaining conversation context.

## 🚀 Features

- **Multi-Modal Query Processing**: Handles weather queries, document Q&A, and general conversations
- **Smart Intent Detection**: Automatically classifies user queries and routes to appropriate handlers
- **Document Retrieval**: PDF processing with vector database storage using ChromaDB
- **Weather Integration**: Real-time weather data retrieval
- **Multiple Interfaces**: Command-line, interactive mode, and Streamlit web UI
- **LangSmith Integration**: Built-in observability and debugging
- **Modular Architecture**: Clean separation of services and pipeline logic

## 📋 Prerequisites

- Python 3.8+
- OpenAI API key
- Weather API key (OpenWeatherMap)
- Git

## 🛠️ Installation

1. **Clone the repository**
```bash
git clone https://github.com/avinash00134/ai-agent-pipeline
cd ai-agent-pipeline
```

2. **Create virtual environment**
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. **Install dependencies**
```bash
pip install -r requirements.txt
```

## ⚙️ Configuration

Create a `.env` file in the root directory with the following variables:

```env
# Required API Keys
OPENAI_API_KEY=your_openai_api_key_here
WEATHER_API_KEY=your_weather_api_key_here

# Optional: LangSmith (for debugging and observability)
LANGCHAIN_API_KEY=your_langsmith_api_key
LANGCHAIN_PROJECT=ai-agent-pipeline
LANGCHAIN_TRACING_V2=true

# Model Configuration (optional - defaults provided)
LLM_MODEL=gpt-3.5-turbo
EMBEDDING_MODEL=all-MiniLM-L6-v2

# Vector Database (optional - defaults provided)
CHROMA_PERSIST_DIRECTORY=./chroma_db
```

### API Key Setup

1. **OpenAI API Key**: Get from [OpenAI Platform](https://platform.openai.com/api-keys)
2. **Weather API Key**: Get from [OpenWeatherMap](https://openweathermap.org/api) or similar service
3. **LangSmith API Key** (optional): Get from [LangSmith](https://smith.langchain.com/)

## 🚀 Usage

### Command Line Interface

**Check configuration status:**
```bash
python main.py --config
```

**Load PDF documents into vector database:**
```bash
python main.py --load-pdfs document1.pdf document2.pdf folder/*.pdf
```

**Process a single query:**
```bash
python main.py --query "What's the weather in London?"
```

**Interactive mode:**
```bash
python main.py --interactive
# or simply
python main.py
```

**Launch Streamlit web interface:**
```bash
python main.py --streamlit
```

### Interactive Mode Example

```
🤖 AI Agent Pipeline - Interactive Mode
==================================================
You can ask about:
🌤️  Weather: 'What's the weather in London?'
📄 Documents: 'What does this document say about...?'
💬 General: Any other questions
Type 'quit' to exit
==================================================

💬 Your question: What's the weather like in Paris?
🔄 Processing...

🤖 Response: The current weather in Paris is 22°C with clear skies...
🎯 Intent: weather
🌤️  Weather data retrieved for: Paris
```

### Streamlit Web Interface

The Streamlit interface provides a user-friendly web UI for interacting with the pipeline:

```bash
streamlit run streamlit_app.py
```

## 📊 Project Structure

```
ai-agent-pipeline/
├── src/
│   ├── pipeline/
│   │   └── langgraph_pipeline.py
│   ├── services/
│   │   ├── pdf_service.py
│   │   ├── vector_service.py
│   │   └── weather_service.py
│   └── config.py
├── tests/
│   ├── test_pipeline/
│   │   └── test_langgraph_pipeline.py
│   ├── test_services/
│   │   ├── test_pdf_service.py
│   │   ├── test_vector_service.py
│   │   └── test_weather_service.py
│   └── conftest.py
├── main.py
├── streamlit_app.py
├── setup.py
└── README.md
```

## 🔧 Core Components

### Pipeline Architecture

The system uses LangGraph to create a stateful pipeline that:

1. **Intent Classification**: Determines if query is weather-related, document-related, or general
2. **Service Routing**: Routes to appropriate service (Weather, Vector DB, or LLM)
3. **Response Generation**: Combines retrieved data with LLM-generated responses
4. **Context Management**: Maintains conversation state across interactions

### Services

- **PDFService**: Extracts and chunks text from PDF documents
- **VectorService**: Manages ChromaDB for document storage and retrieval
- **WeatherService**: Fetches real-time weather data
- **AIAgentPipeline**: Orchestrates the entire workflow

## 💡 Usage Examples

### Weather Queries
```python
# These queries will be routed to weather service
"What's the weather in Tokyo?"
"Is it raining in Seattle?"
"Show me the forecast for New York"
```

### Document Queries
```python
# These queries will search your loaded documents
"What does the document say about machine learning?"
"Summarize the key findings from the research paper"
"Find information about data privacy policies"
```

### General Queries
```python
# These will be handled by the general LLM
"Explain quantum computing"
"Write a poem about spring"
"Help me plan a vacation"
```

## 🔍 Monitoring and Debugging

If you've configured LangSmith, you can monitor pipeline execution:

1. Visit [LangSmith](https://smith.langchain.com/)
2. Navigate to your project (configured in `LANGCHAIN_PROJECT`)
3. View detailed traces of pipeline execution, including:
   - Intent classification decisions
   - Service routing
   - Retrieval results
   - Response generation

## 🐛 Troubleshooting

### Common Issues

**Configuration Errors:**
```bash
python main.py --config
```
Use this command to verify all API keys are properly set.

**Vector Database Issues:**
```bash
# Reset the vector database
python -c "from src.services.vector_service import VectorService; VectorService().reset_collection()"
```

**PDF Processing Errors:**
- Ensure PDFs are not password-protected
- Check file permissions
- Verify PDF files are not corrupted

### Error Messages

- `❌ Configuration error`: Missing or invalid API keys
- `❌ PDF file not found`: Check file paths
- `❌ Failed to initialize pipeline`: Usually configuration-related

## 📦 Dependencies

Key dependencies include:

- `langchain` - LLM framework
- `langgraph` - Stateful pipeline orchestration
- `streamlit` - Web interface
- `chromadb` - Vector database
- `openai` - OpenAI API integration
- `requests` - HTTP requests for weather API
- `pypdf` - PDF processing
- `python-dotenv` - Environment variable management



## 🆘 Support

If you encounter issues or have questions:

1. Check the troubleshooting section above
2. Review the configuration with `python main.py --config`
3. Check the logs for detailed error messages
4. Open an issue on GitHub with:
   - Your configuration (without API keys)
   - Error messages
   - Steps to reproduce

## 🔄 Version History

- **v1.0.0**: Initial release with core pipeline functionality
- **v1.1.0**: Added Streamlit web interface
- **v1.2.0**: Enhanced error handling and configuration validation

---

**Made with ❤️ using LangGraph and LangChain**
