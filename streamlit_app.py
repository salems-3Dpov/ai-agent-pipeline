import streamlit as st
import os
import tempfile
from src.pipeline.langgraph_pipeline import AIAgentPipeline
from src.services.pdf_service import PDFService
from src.services.vector_service import VectorService
from src.config import Config

# Page configuration
st.set_page_config(
    page_title="AI Agent Pipeline Demo",
    page_icon="🤖",
    layout="wide"
)

def check_service_availability():
    """Check which services are available based on config."""
    return {
        "openai": bool(Config.OPENAI_API_KEY),
        "weather": bool(Config.OPENWEATHERMAP_API_KEY),
        "langsmith": bool(Config.LANGCHAIN_API_KEY),
        "documents": True  # Always available (local ChromaDB)
    }

# Initialize session state
if 'pipeline' not in st.session_state:
    st.session_state.pipeline = None
if 'chat_history' not in st.session_state:
    st.session_state.chat_history = []
if 'documents_loaded' not in st.session_state:
    st.session_state.documents_loaded = False
if 'pipeline_error' not in st.session_state:
    st.session_state.pipeline_error = None

def initialize_pipeline():
    """Initialize the AI pipeline with robust error handling."""
    try:
        if st.session_state.pipeline is None:
            with st.spinner("Initializing AI Pipeline..."):
                try:
                    # First ensure vector database is ready
                    vector_service = VectorService()
                    if vector_service.collection.count() == 0:
                        st.info("Vector database is empty. Please upload documents first.")
                    
                    # Then initialize pipeline
                    st.session_state.pipeline = AIAgentPipeline()
                    st.session_state.pipeline_error = None
                    return True
                except Exception as e:
                    st.session_state.pipeline_error = str(e)
                    if "does not exist" in str(e):
                        st.error("Vector database not initialized. Please upload documents first.")
                    else:
                        st.error(f"Error initializing pipeline: {str(e)}")
                    return False
        return True
    except Exception as e:
        st.session_state.pipeline_error = str(e)
        st.error(f"Critical error during initialization: {str(e)}")
        return False

def load_pdf_documents(uploaded_files):
    """Load PDF documents into the vector database with better error handling."""
    try:
        pdf_service = PDFService()
        vector_service = VectorService()
        
        # Ensure collection exists
        if not hasattr(vector_service, 'collection'):
            st.error("Vector database not properly initialized")
            return 0
        
        all_documents = []
        
        for uploaded_file in uploaded_files:
            with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_file:
                tmp_file.write(uploaded_file.read())
                tmp_path = tmp_file.name
            
            try:
                documents = pdf_service.process_pdf(tmp_path, {
                    'uploaded_filename': uploaded_file.name
                })
                all_documents.extend(documents)
            finally:
                os.unlink(tmp_path)
        
        if all_documents:
            try:
                success = vector_service.add_documents(all_documents)
                if success:
                    st.session_state.documents_loaded = True
                    return len(all_documents)
            except Exception as e:
                st.error(f"Error adding documents to vector database: {str(e)}")
                return 0
        
        return 0
    except Exception as e:
        st.error(f"Error loading PDF documents: {str(e)}")
        return 0

def main():
    """Main Streamlit application."""
    st.title("🤖 AI Agent Pipeline Demo")
    st.markdown("**LangChain + LangGraph + LangSmith Integration**")
    
    # Check available services
    available_services = check_service_availability()
    
    # Show warning banner if services are missing
    if not all(available_services.values()):
        missing_services = []
        if not available_services["openai"]:
            missing_services.append("OpenAI (required)")
        if not available_services["weather"]:
            missing_services.append("Weather")
        if not available_services["langsmith"]:
            missing_services.append("LangSmith")
        
        st.warning(
            f"Some features are disabled because: {', '.join(missing_services)}. "
            "Please check your .env file or environment variables."
        )
    
    # Sidebar for configuration and document upload
    with st.sidebar:
        st.header("⚙️ Configuration")
        
        # Service status with explanations
        st.subheader("Service Status")
        
        # OpenAI
        if available_services["openai"]:
            st.success("✅ OpenAI - Available")
        else:
            st.error("❌ OpenAI - Required for all features")
        
        # Weather
        if available_services["weather"]:
            st.success("✅ Weather - Available")
        else:
            st.warning("⚠️ Weather - Disabled (missing OPENWEATHERMAP_API_KEY)")
        
        # LangSmith
        if available_services["langsmith"]:
            st.success("✅ LangSmith - Available")
        else:
            st.warning("⚠️ LangSmith - Disabled (missing LANGCHAIN_API_KEY)")
        
        st.success("✅ Document Processing - Always Available")
        
        st.divider()
        
        # Document upload section
        st.subheader("📄 Upload PDF Documents")
        uploaded_files = st.file_uploader(
            "Choose PDF files",
            type="pdf",
            accept_multiple_files=True,
            help="Upload PDF documents to enable document-based queries"
        )
        
        if uploaded_files:
            if st.button("Load Documents"):
                with st.spinner("Processing PDF documents..."):
                    num_chunks = load_pdf_documents(uploaded_files)
                    if num_chunks > 0:
                        st.success(f"✅ Loaded {num_chunks} document chunks!")
                    else:
                        st.error("❌ Failed to load documents")
        
        # Vector database info
        if st.session_state.documents_loaded:
            st.success("📚 Documents are loaded and ready!")
        
        st.divider()
        
        # Pipeline status
        st.subheader("🔧 Pipeline Status")
        if st.session_state.pipeline:
            st.success("✅ Pipeline initialized")
        elif st.session_state.pipeline_error:
            st.error(f"⚠️ Pipeline error: {st.session_state.pipeline_error}")
        else:
            st.warning("⚠️ Pipeline not initialized")
    
    # Main chat interface
    st.header("💬 Chat Interface")
    
    # Initialize pipeline
    if not initialize_pipeline():
        st.error("Failed to initialize pipeline. Please check your configuration.")
        st.stop()
    
    # Example queries
    with st.expander("💡 Example Queries"):
        example_queries = [
            "**Document Queries:**",
            "- What is this document about?",
            "- Summarize the main points",
            "- What are the key findings?",
            "",
            "**General Knowledge:**",
            "- Tell me about artificial intelligence",
            "- Explain machine learning concepts"
        ]
        
        if available_services["weather"]:
            example_queries.insert(0, "**Weather Queries:**")
            example_queries.insert(1, "- What's the weather like in New York?")
            example_queries.insert(2, "- Show me the weather forecast for London")
        
        st.markdown("\n".join(example_queries))
    
    # Chat history display
    st.subheader("📝 Chat History")
    
    # Display chat history
    for i, (query, response, metadata) in enumerate(st.session_state.chat_history):
        with st.container():
            st.markdown(f"**You:** {query}")
            st.markdown(f"**AI Agent:** {response}")
            
            if metadata.get("error"):
                st.error(f"Error: {metadata['error']}")
            
            st.divider()
    
    # Chat input
    with st.form("chat_form", clear_on_submit=True):
        query_placeholder = "Enter your question here... ("
        if available_services["weather"]:
            query_placeholder += "weather, "
        query_placeholder += "document queries or general questions)"
        
        query = st.text_input(
            "Ask me anything!",
            placeholder=query_placeholder,
            key="user_input"
        )
        
        col1, col2, col3 = st.columns([1, 1, 4])
        
        with col1:
            submit_button = st.form_submit_button("Send 🚀")
        
        with col2:
            clear_button = st.form_submit_button("Clear History 🗑️")
        
        if clear_button:
            st.session_state.chat_history = []
            st.rerun()
    
    # Process query
    if submit_button and query.strip():
        if st.session_state.pipeline is None:
            st.error("Pipeline is not available. Please check your configuration.")
            st.stop()
        
        with st.spinner("Processing your query..."):
            try:
                # Process query through pipeline
                result = st.session_state.pipeline.process_query(query)
                
                # Add to chat history
                st.session_state.chat_history.append((
                    query,
                    result["response"],
                    {
                        "intent": result["intent"],
                        "success": result["success"],
                        "weather_data": result.get("weather_data"),
                        "retrieved_docs": result.get("retrieved_docs"),
                        "error": result.get("error", "")
                    }
                ))
                
                # Rerun to update display
                st.rerun()
            except Exception as e:
                st.error(f"Error processing query: {str(e)}")
                st.session_state.chat_history.append((
                    query,
                    "I encountered an error processing your request.",
                    {
                        "error": str(e),
                        "success": False
                    }
                ))
                st.rerun()
    
    # Footer
    st.markdown("---")
    st.markdown(
        "Built with ❤️ using LangChain, LangGraph, LangSmith, ChromaDB, and Streamlit"
    )

if __name__ == "__main__":
    def check_system_ready():
        """Check if all required systems are ready."""
        try:
            # Check vector database
            vector_service = VectorService()
            if not hasattr(vector_service, 'collection'):
                st.error("Vector database not initialized. Please upload documents first.")
                return False
            
            # Check OpenAI
            if not Config.OPENAI_API_KEY:
                st.error("OpenAI API key is required")
                return False
                
            return True
        except Exception as e:
            st.error(f"System check failed: {str(e)}")
            return False
    main()
    if not check_system_ready():
        st.stop()