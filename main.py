import argparse
import sys
import os
import subprocess
from pathlib import Path
from typing import List, Optional, Dict, Any

# Add src to path
sys.path.append(str(Path(__file__).parent / "./src"))

from src.pipeline.langgraph_pipeline import AIAgentPipeline
from src.services.pdf_service import PDFService
from src.services.vector_service import VectorService
from src.config import Config

class CLIDisplay:
    """Handles console display formatting and colors."""
    
    @staticmethod
    def print_header(text: str) -> None:
        print(f"\n\033[1;36m{text}\033[0m")
        print("=" * len(text))
    
    @staticmethod
    def print_success(text: str) -> None:
        print(f"\033[1;32m✓ {text}\033[0m")
    
    @staticmethod
    def print_warning(text: str) -> None:
        print(f"\033[1;33m⚠  {text}\033[0m")
    
    @staticmethod
    def print_error(text: str) -> None:
        print(f"\033[1;31m✗ {text}\033[0m")
    
    @staticmethod
    def print_info(text: str) -> None:
        print(f"\033[1;34mℹ  {text}\033[0m")

def setup_vector_database(pdf_paths: List[str]) -> bool:
    """Load PDF documents into the vector database with validation."""
    CLIDisplay.print_header("Setting Up Vector Database")
    
    pdf_service = PDFService()
    vector_service = VectorService()
    
    try:
        CLIDisplay.print_info("Resetting existing collection...")
        vector_service.reset_collection()
        
        all_documents = []
        failed_files = []
        
        for pdf_path in pdf_paths:
            if not os.path.exists(pdf_path):
                CLIDisplay.print_error(f"PDF file not found: {pdf_path}")
                failed_files.append(pdf_path)
                continue
            
            try:
                CLIDisplay.print_info(f"Processing {os.path.basename(pdf_path)}...")
                documents = pdf_service.process_pdf(pdf_path)
                all_documents.extend(documents)
                CLIDisplay.print_success(f"Processed {len(documents)} chunks")
            except Exception as e:
                CLIDisplay.print_error(f"Error processing {pdf_path}: {str(e)}")
                failed_files.append(pdf_path)
        
        if not all_documents:
            CLIDisplay.print_error("No valid documents were processed")
            if failed_files:
                CLIDisplay.print_info(f"Failed files: {', '.join(failed_files)}")
            return False
        
        CLIDisplay.print_info(f"Adding {len(all_documents)} chunks to database...")
        if vector_service.add_documents(all_documents):
            CLIDisplay.print_success("Vector database setup complete!")
            if failed_files:
                CLIDisplay.print_warning(f"Note: {len(failed_files)} files failed processing")
            return True
        
        CLIDisplay.print_error("Failed to add documents to vector database")
        return False
    
    except Exception as e:
        CLIDisplay.print_error(f"Database setup failed: {str(e)}")
        return False

def interactive_mode() -> None:
    """Run the pipeline in interactive chat mode."""
    CLIDisplay.print_header("AI Agent Pipeline - Interactive Mode")
    print("Available query types:")
    print("- 🌤️  Weather: 'What's the weather in Paris?'")
    print("- 📄 Documents: 'What does the document say about AI?'")
    print("- 💬 General: 'Explain quantum computing'")
    print("\nType 'quit', 'exit', or 'q' to end session")
    print("=" * 50)
    
    try:
        pipeline = AIAgentPipeline()
        
        while True:
            try:
                query = input("\n\033[1;35mYou:\033[0m ").strip()
                
                if query.lower() in {'quit', 'exit', 'q'}:
                    CLIDisplay.print_info("Ending session. Goodbye!")
                    break
                
                if not query:
                    continue
                
                CLIDisplay.print_info("Processing query...")
                result = pipeline.process_query(query)
                
                print(f"\n\033[1;34mAI:\033[0m {result['response']}")
                print(f"\033[1;90m[Intent: {result['intent'].title()}]")
                
                if result['weather_data']:
                    city = result['weather_data'].get('city', 'Unknown')
                    print(f"\033[1;90m[Weather data for {city}]")
                
                if result['retrieved_docs']:
                    print(f"\033[1;90m[Found {len(result['retrieved_docs'])} relevant documents]")
                
                if result['error']:
                    CLIDisplay.print_warning(f"Note: {result['error']}")
            
            except KeyboardInterrupt:
                CLIDisplay.print_info("\nSession interrupted. Goodbye!")
                break
            except Exception as e:
                CLIDisplay.print_error(f"Processing error: {str(e)}")
    
    except Exception as e:
        CLIDisplay.print_error(f"Failed to initialize pipeline: {str(e)}")
        CLIDisplay.print_info("Please check your configuration and API keys.")

def single_query_mode(query: str) -> None:
    """Process a single query with detailed output."""
    CLIDisplay.print_header(f"Processing Query: '{query}'")
    
    try:
        pipeline = AIAgentPipeline()
        result = pipeline.process_query(query)
        
        print(f"\n\033[1;34mResponse:\033[0m {result['response']}")
        print(f"\033[1;32mIntent:\033[0m {result['intent']}")
        print(f"\033[1;32mSuccess:\033[0m {result['success']}")
        
        if result['weather_data']:
            CLIDisplay.print_header("Weather Data")
            print(result['weather_data'])
        
        if result['retrieved_docs']:
            CLIDisplay.print_header(f"Retrieved Documents ({len(result['retrieved_docs'])})")
            for i, doc in enumerate(result['retrieved_docs'][:3], 1):
                print(f"\n\033[1;33mDocument {i}:\033[0m")
                print(f"Source: {doc.get('metadata', {}).get('source', 'Unknown')}")
                print(f"Content: {doc['content'][:200]}...")
        
        if result['error']:
            CLIDisplay.print_error(f"Error: {result['error']}")
    
    except Exception as e:
        CLIDisplay.print_error(f"Query processing failed: {str(e)}")

def show_config() -> bool:
    """Display current configuration status."""
    CLIDisplay.print_header("Configuration Status")
    
    try:
        Config.validate_config()
        CLIDisplay.print_success("All required API keys are configured")
    except ValueError as e:
        CLIDisplay.print_error(f"Configuration error: {str(e)}")
        return False
    
    print(f"\n\033[1;36mAI Model Configuration:\033[0m")
    print(f"  LLM Model: {Config.LLM_MODEL}")
    print(f"  Embedding Model: {Config.EMBEDDING_MODEL}")
    
    print(f"\n\033[1;36mServices Configuration:\033[0m")
    print(f"  Vector DB Path: {Config.CHROMA_PERSIST_DIRECTORY}")
    print(f"  LangSmith Project: {Config.LANGCHAIN_PROJECT}")
    
    try:
        vector_service = VectorService()
        info = vector_service.get_collection_info()
        print(f"\n\033[1;36mVector Database Status:\033[0m")
        print(f"  Documents stored: {info['count']}")
        print(f"  Collection: {info['name']}")
    except Exception as e:
        CLIDisplay.print_error(f"Vector DB check failed: {str(e)}")
    
    return True

def main() -> None:
    """Main entry point for the CLI interface."""
    parser = argparse.ArgumentParser(
        description="AI Agent Pipeline - Document Processing and Question Answering",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    
    parser.add_argument(
        "-i", "--interactive", 
        action="store_true",
        help="Run in interactive chat mode"
    )
    parser.add_argument(
        "-q", "--query", 
        type=str,
        help="Process a single query"
    )
    parser.add_argument(
        "--load-pdfs", 
        nargs="+",
        metavar="FILE",
        help="Load PDF files into vector database"
    )
    parser.add_argument(
        "--config", 
        action="store_true",
        help="Show current configuration status"
    )
    parser.add_argument(
        "--streamlit", 
        action="store_true",
        help="Launch Streamlit web interface"
    )
    
    args = parser.parse_args()
    
    try:
        if args.config:
            if not show_config():
                sys.exit(1)
            return
        
        if args.load_pdfs:
            if not setup_vector_database(args.load_pdfs):
                sys.exit(1)
            return
        
        if args.streamlit:
            CLIDisplay.print_header("Launching Streamlit Interface")
            subprocess.run(["streamlit", "run", "streamlit_app.py"])
            return
        
        if args.query:
            single_query_mode(args.query)
            return
        
        interactive_mode()
    
    except KeyboardInterrupt:
        CLIDisplay.print_info("\nOperation cancelled by user")
        sys.exit(0)
    except Exception as e:
        CLIDisplay.print_error(f"Fatal error: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()