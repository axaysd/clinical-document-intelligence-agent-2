"""
Embedding generation using Vertex AI.
Implements batching and retry logic for production reliability.
"""

from typing import List
import time
from google.cloud import aiplatform
from utils.logger import get_logger
from config import get_settings

logger = get_logger(__name__)


class EmbeddingGenerator:
    """Generate embeddings using Vertex AI."""
    
    def __init__(self):
        """Initialize Vertex AI client."""
        settings = get_settings()
        
        # Initialize Vertex AI
        aiplatform.init(
            project=settings.gcp_project_id,
            location=settings.gcp_location,
        )
        
        self.model_name = f"projects/{settings.gcp_project_id}/locations/{settings.gcp_location}/publishers/google/models/{settings.vertex_embedding_model}"
        logger.info("embedding_generator_initialized", model=settings.vertex_embedding_model)
    
    def generate_embeddings(
        self, 
        texts: List[str], 
        batch_size: int = 100
    ) -> List[List[float]]:
        """
        Generate embeddings for a list of texts.
        
        Args:
            texts: List of text strings to embed
            batch_size: Number of texts to process per API call
            
        Returns:
            List of embedding vectors
        """
        logger.info("generating_embeddings", num_texts=len(texts))
        
        all_embeddings = []
        
        for i in range(0, len(texts), batch_size):
            batch = texts[i:i + batch_size]
            batch_embeddings = self._generate_batch(batch)
            all_embeddings.extend(batch_embeddings)
            
            logger.debug(
                "batch_processed", 
                batch_num=i // batch_size + 1,
                batch_size=len(batch)
            )
        
        logger.info("embeddings_generated", total=len(all_embeddings))
        return all_embeddings
    
    def _generate_batch(self, texts: List[str], max_retries: int = 3) -> List[List[float]]:
        """Generate embeddings for a batch with retry logic."""
        for attempt in range(max_retries):
            try:
                # Use Vertex AI prediction
                from vertexai.language_models import TextEmbeddingModel
                
                model = TextEmbeddingModel.from_pretrained(
                    get_settings().vertex_embedding_model
                )
                
                embeddings = model.get_embeddings(texts)
                return [e.values for e in embeddings]
                
            except Exception as e:
                logger.warning(
                    "embedding_batch_failed",
                    attempt=attempt + 1,
                    error=str(e)
                )
                
                if attempt < max_retries - 1:
                    time.sleep(2 ** attempt)  # Exponential backoff
                else:
                    raise RuntimeError(f"Failed to generate embeddings after {max_retries} attempts: {e}")
    
    def generate_single_embedding(self, text: str) -> List[float]:
        """Generate embedding for a single text (convenience method)."""
        return self.generate_embeddings([text])[0]
