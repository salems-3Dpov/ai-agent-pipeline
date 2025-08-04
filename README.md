# AI Agent Pipeline

A robust AI agent pipeline using LangChain, LangGraph, and LangSmith for document processing, weather information retrieval, and general question answering.

## Features

- **Multi-modal AI Pipeline**: Handles weather queries, document-based questions, and general knowledge
- **Document Processing**: PDF text extraction and chunking with metadata
- **Vector Database**: ChromaDB for document storage and retrieval
- **Weather Service**: OpenWeatherMap integration for real-time weather data
- **Interactive Modes**: CLI and Streamlit UI interfaces
- **LangGraph Workflow**: State-based decision making for query routing

## Project Structure

```
ai-agent-pipeline/
├── src/
│   ├── pipeline/
│   │   └── langgraph_pipeline.py       # Main AI pipeline logic
│   ├── services/
│   │   ├── pdf_service.py              # PDF processing service
│   │   ├── vector_service.py           # Vector database operations
│   │   └── weather_service.py          # Weather API integration
│   └── config.py                       # Configuration management
├── main.py                             # CLI entry point
├── streamlit_app.py                    # Web UI interface
├── setup.py                            # Package configuration
└── README.md                           # This file
```

## Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/avinash00134/ai-agent-pipeline.git
   cd ai-agent-pipeline
   ```

2. Create and activate a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # Linux/MacOS
   venv\Scripts\activate    # Windows
   ```

3. Install dependencies:
   ```bash
   pip install -e .
   ```

4. Create a `.env` file with your API keys:
   ```env
   OPENAI_API_KEY=your_openai_key
   OPENWEATHERMAP_API_KEY=your_weather_key
   LANGCHAIN_API_KEY=your_langsmith_key  # Optional
   ```

## Usage

### Command Line Interface

```bash
# Interactive mode
python main.py --interactive

# Single query mode
python main.py --query "What's the weather in London?"

# Load PDF documents
python main.py --load-pdfs document1.pdf document2.pdf

# Show configuration
python main.py --config

# Launch Streamlit UI
python main.py --streamlit
```

### Streamlit Web Interface

```bash
streamlit run streamlit_app.py
```

Or use the CLI command:
```bash
python main.py --streamlit
```

### As a Package

After installation, you can use the pipeline in your own code:

```python
from src.pipeline.langgraph_pipeline import AIAgentPipeline

pipeline = AIAgentPipeline()
result = pipeline.process_query("What's the weather in Paris?")
print(result["response"])
```

## Configuration

Edit the `.env` file or set environment variables to configure:

| Variable | Description | Default |
|----------|-------------|---------|
| `OPENAI_API_KEY` | OpenAI API key | Required |
| `OPENWEATHERMAP_API_KEY` | OpenWeatherMap API key | Optional |
| `LANGCHAIN_API_KEY` | LangSmith API key | Optional |
| `LLM_MODEL` | OpenAI model to use | `gpt-3.5-turbo` |
| `EMBEDDING_MODEL` | Sentence Transformer model | `all-MiniLM-L6-v2` |
| `CHROMA_PERSIST_DIRECTORY` | ChromaDB storage path | `./chroma_db` |
| `COLLECTION_NAME` | Chroma collection name | `pdf_documents` |

## Requirements

- Python 3.8+
- Required packages (see `requirements.txt`):
  - langchain
  - langgraph
  - chromadb
  - sentence-transformers
  - pypdf
  - openai
  - streamlit (for UI)
  - python-dotenv