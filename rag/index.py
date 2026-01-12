"""
FAISS index management for vector storage and retrieval.
Implements persistence, metadata tracking, and efficient search.
"""

from typing import List, Tuple, Optional
import numpy as np
import faiss
import json
import pickle
from pathlib import Path
from models.schemas import Chunk, Citation
from utils.logger import get_logger
from config import get_settings

logger = get_logger(__name__)


class FAISSIndexManager:
    """Manage FAISS vector index with persistence."""
    
    def __init__(self, index_path: Optional[str] = None):
        """
        Initialize FAISS index manager.
        
        Args:
            index_path: Directory to store index files
        """
        settings = get_settings()
        self.index_path = Path(index_path or settings.faiss_index_path)
        self.index_path.mkdir(parents=True, exist_ok=True)
        
        self.index_file = self.index_path / "faiss.index"
        self.metadata_file = self.index_path / "metadata.pkl"
        
        self.index: Optional[faiss.Index] = None
        self.chunks: List[Chunk] = []
        
        # Load existing index if available
        if self.index_file.exists():
            self.load()
        
        logger.info("faiss_manager_initialized", index_path=str(self.index_path))
    
    def create_index(self, dimension: int = 768):
        """Create a new FAISS index."""
        # Use L2 distance (can switch to inner product for cosine similarity)
        self.index = faiss.IndexFlatL2(dimension)
        logger.info("faiss_index_created", dimension=dimension)
    
    def add_chunks(self, chunks: List[Chunk]):
        """
        Add chunks to the index.
        
        Args:
            chunks: List of chunks with embeddings
        """
        if not chunks:
            logger.warning("no_chunks_to_add")
            return
        
        # Extract embeddings
        embeddings = [chunk.embedding for chunk in chunks]
        
        # Validate embeddings
        if any(e is None for e in embeddings):
            raise ValueError("All chunks must have embeddings")
        
        # Convert to numpy array
        embeddings_array = np.array(embeddings, dtype=np.float32)
        
        # Create index if it doesn't exist
        if self.index is None:
            self.create_index(dimension=embeddings_array.shape[1])
        
        # Add to index
        self.index.add(embeddings_array)
        
        # Store chunks
        self.chunks.extend(chunks)
        
        logger.info("chunks_added_to_index", num_chunks=len(chunks), total=len(self.chunks))
    
    def search(
        self, 
        query_embedding: List[float], 
        top_k: int = 5
    ) -> List[Tuple[Chunk, float]]:
        """
        Search for similar chunks.
        
        Args:
            query_embedding: Query vector
            top_k: Number of results to return
            
        Returns:
            List of (chunk, similarity_score) tuples
        """
        if self.index is None or len(self.chunks) == 0:
            logger.warning("index_empty")
            return []
        
        # Convert to numpy array
        query_array = np.array([query_embedding], dtype=np.float32)
        
        # Search
        distances, indices = self.index.search(query_array, min(top_k, len(self.chunks)))
        
        # Convert L2 distance to similarity score (inverse)
        # Lower distance = higher similarity
        results = []
        for dist, idx in zip(distances[0], indices[0]):
            if idx < len(self.chunks):
                # Convert L2 distance to similarity score (0-1 range)
                # Using exponential decay: score = exp(-distance)
                similarity_score = float(np.exp(-dist))
                results.append((self.chunks[idx], similarity_score))
        
        logger.info("search_completed", query_dim=len(query_embedding), top_k=top_k, results=len(results))
        return results
    
    def save(self):
        """Persist index and metadata to disk."""
        if self.index is None:
            logger.warning("no_index_to_save")
            return
        
        # Save FAISS index
        faiss.write_index(self.index, str(self.index_file))
        
        # Save chunks metadata
        with open(self.metadata_file, 'wb') as f:
            pickle.dump(self.chunks, f)
        
        logger.info("index_saved", num_chunks=len(self.chunks))
    
    def load(self):
        """Load index and metadata from disk."""
        if not self.index_file.exists():
            logger.warning("no_index_file_found")
            return
        
        # Load FAISS index
        self.index = faiss.read_index(str(self.index_file))
        
        # Load chunks metadata
        if self.metadata_file.exists():
            with open(self.metadata_file, 'rb') as f:
                self.chunks = pickle.load(f)
        
        logger.info("index_loaded", num_chunks=len(self.chunks))
    
    def get_stats(self) -> dict:
        """Get index statistics."""
        return {
            'num_chunks': len(self.chunks),
            'index_size': self.index.ntotal if self.index else 0,
            'dimension': self.index.d if self.index else 0,
        }
