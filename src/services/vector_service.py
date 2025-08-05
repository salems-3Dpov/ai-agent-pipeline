import os
import chromadb
from chromadb.config import Settings
from sentence_transformers import SentenceTransformer
from langchain.schema import Document
from src.config import Config
import logging
from typing import List, Dict, Optional

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Suppress noisy logs
logging.getLogger("chromadb").setLevel(logging.WARNING)
logging.getLogger("sentence_transformers").setLevel(logging.WARNING)

class VectorService:
    """Service for managing vector embeddings and ChromaDB operations with robust error handling."""
    
    def __init__(self):
        self.persist_directory = Config.CHROMA_PERSIST_DIRECTORY
        self.collection_name = Config.COLLECTION_NAME
        self.embedding_model_name = Config.EMBEDDING_MODEL
        
        # Ensure storage directory exists
        os.makedirs(self.persist_directory, exist_ok=True)
        
        try:
            # Initialize embedding model
            self.embedding_model = SentenceTransformer(
                self.embedding_model_name,
                device='cpu'  # Change to 'cuda' if GPU available
            )
            
            # Initialize ChromaDB client with persistent settings
            self.client = chromadb.PersistentClient(
                path=self.persist_directory,
                settings=Settings(
                    anonymized_telemetry=False,
                    allow_reset=True,
                    is_persistent=True
                )
            )
            
            # Initialize collection with automatic creation
            self.collection = self._initialize_collection()
            
            logger.info(f"VectorService initialized successfully. Collection: {self.collection_name}")
            
        except Exception as e:
            logger.error(f"Failed to initialize VectorService: {str(e)}")
            raise RuntimeError(f"Vector service initialization failed: {str(e)}")

    def _initialize_collection(self):
        """Initialize or create the ChromaDB collection with error handling."""
        try:
            # Get existing collection or create new one
            collection = self.client.get_or_create_collection(
                name=self.collection_name,
                metadata={"description": "PDF document embeddings"}
            )
            logger.info(f"Collection '{self.collection_name}' ready (count: {collection.count()})")
            return collection
            
        except Exception as e:
            logger.error(f"Collection initialization failed: {str(e)}")
            raise RuntimeError(f"Could not initialize collection: {str(e)}")

    def generate_embeddings(self, texts: List[str]) -> List[List[float]]:
        """
        Generate embeddings for a list of texts with error handling.
        
        Args:
            texts: List of text strings to embed
            
        Returns:
            List of embedding vectors
            
        Raises:
            RuntimeError: If embedding generation fails
        """
        if not texts:
            return []
            
        try:
            embeddings = self.embedding_model.encode(
                texts,
                show_progress_bar=False,
                normalize_embeddings=True
            )
            return embeddings.tolist()
            
        except Exception as e:
            logger.error(f"Embedding generation failed: {str(e)}")
            raise RuntimeError(f"Failed to generate embeddings: {str(e)}")

    def add_documents(self, documents: List[Document]) -> bool:
        """
        Add documents to the vector database with full error handling.
        
        Args:
            documents: List of Langchain Document objects
            
        Returns:
            bool: True if successful, False if failed
        """
        if not documents:
            logger.warning("No documents provided for addition")
            return False
            
        try:
            # Prepare data for ChromaDB
            texts = [doc.page_content for doc in documents]
            metadatas = [doc.metadata for doc in documents]
            ids = [
                f"doc_{i}_{doc.metadata.get('filename', 'unknown')}_{doc.metadata.get('chunk_id', i)}" 
                for i, doc in enumerate(documents)
            ]
            
            # Generate embeddings
            logger.info(f"Generating embeddings for {len(texts)} documents...")
            embeddings = self.generate_embeddings(texts)
            
            # Add to collection
            self.collection.add(
                embeddings=embeddings,
                documents=texts,
                metadatas=metadatas,
                ids=ids
            )
            
            logger.info(f"Successfully added {len(documents)} documents to collection")
            return True
            
        except Exception as e:
            logger.error(f"Failed to add documents: {str(e)}")
            return False

    def similarity_search(self, query: str, n_results: int = 5) -> List[Dict]:
        """
        Perform similarity search with comprehensive error handling.
        
        Args:
            query: Search query string
            n_results: Number of results to return
            
        Returns:
            List of result dictionaries with content, metadata, and scores
        """
        try:
            # Generate query embedding
            query_embedding = self.generate_embeddings([query])[0]
            
            # Execute search
            results = self.collection.query(
                query_embeddings=[query_embedding],
                n_results=n_results,
                include=['documents', 'metadatas', 'distances']
            )
            
            # Format results
            formatted_results = []
            if results['documents']:
                for i in range(len(results['documents'][0])):
                    formatted_results.append({
                        'content': results['documents'][0][i],
                        'metadata': results['metadatas'][0][i],
                        'score': 1 - results['distances'][0][i]  # Convert distance to similarity score
                    })
            
            logger.debug(f"Found {len(formatted_results)} results for query: '{query[:50]}...'")
            return formatted_results
            
        except Exception as e:
            logger.error(f"Similarity search failed for query '{query[:50]}...': {str(e)}")
            return []

    def get_collection_info(self) -> Dict:
        """Get collection metadata with error handling."""
        try:
            return {
                'name': self.collection_name,
                'count': self.collection.count(),
                'embedding_model': self.embedding_model_name,
                'persist_directory': self.persist_directory
            }
        except Exception as e:
            logger.error(f"Failed to get collection info: {str(e)}")
            return {'error': str(e)}

    def reset_collection(self) -> bool:
        """Reset the collection with proper cleanup."""
        try:
            self.client.delete_collection(name=self.collection_name)
            self.collection = self._initialize_collection()
            logger.info(f"Collection {self.collection_name} has been reset")
            return True
        except Exception as e:
            logger.error(f"Failed to reset collection: {str(e)}")
            return False

    def health_check(self) -> Dict:
        """Check service health with detailed diagnostics."""
        status = {
            'collection_ready': False,
            'embedding_model_ready': False,
            'error': None
        }
        
        try:
            # Check collection
            if hasattr(self, 'collection'):
                status['collection_ready'] = True
                status['document_count'] = self.collection.count()
            
            # Check embedding model
            if hasattr(self, 'embedding_model'):
                status['embedding_model_ready'] = True
                
            return status
            
        except Exception as e:
            status['error'] = str(e)
            return status