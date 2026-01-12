"""
Retrieval orchestration combining embeddings, FAISS search, and citation generation.
"""

from typing import List
from models.schemas import Citation, Chunk
from rag.embeddings import EmbeddingGenerator
from rag.index import FAISSIndexManager
from utils.logger import get_logger
from utils.helpers import truncate_text

logger = get_logger(__name__)


class Retriever:
    """Orchestrate document retrieval with citation generation."""
    
    def __init__(self, index_manager: FAISSIndexManager):
        """
        Initialize retriever.
        
        Args:
            index_manager: FAISS index manager instance
        """
        self.index_manager = index_manager
        self.embedding_generator = EmbeddingGenerator()
        logger.info("retriever_initialized")
    
    def retrieve(self, query: str, top_k: int = 5) -> List[Citation]:
        """
        Retrieve relevant chunks for a query.
        
        Args:
            query: Question or search query
            top_k: Number of results to return
            
        Returns:
            List of citations with similarity scores
        """
        logger.info("retrieving_chunks", query_length=len(query), top_k=top_k)
        
        # Generate query embedding
        query_embedding = self.embedding_generator.generate_single_embedding(query)
        
        # Search index
        results = self.index_manager.search(query_embedding, top_k=top_k)
        
        # Convert to citations
        citations = []
        for chunk, similarity_score in results:
            citation = Citation(
                chunk_id=chunk.chunk_id,
                document_id=chunk.document_id,
                similarity_score=similarity_score,
                snippet=truncate_text(chunk.text, max_length=200),
                page_number=chunk.page_number,
            )
            citations.append(citation)
        
        logger.info("retrieval_complete", num_citations=len(citations))
        return citations
    
    def get_chunk_text(self, chunk_id: str) -> str:
        """Get full text for a chunk ID."""
        for chunk in self.index_manager.chunks:
            if chunk.chunk_id == chunk_id:
                return chunk.text
        return ""
