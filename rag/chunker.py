"""
Text chunking with overlap and metadata preservation.
Implements sentence-aware chunking to avoid breaking mid-sentence.
"""

from typing import List, Dict
from models.schemas import Chunk
from utils.helpers import generate_chunk_id
from utils.logger import get_logger

logger = get_logger(__name__)


class TextChunker:
    """Chunk text with overlap and metadata preservation."""
    
    def __init__(self, chunk_size: int = 512, chunk_overlap: int = 64):
        """
        Initialize chunker.
        
        Args:
            chunk_size: Target characters per chunk
            chunk_overlap: Characters to overlap between chunks
        """
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
    
    def chunk_document(
        self, 
        pages: List[Dict[str, any]], 
        document_id: str
    ) -> List[Chunk]:
        """
        Chunk document pages into overlapping chunks.
        
        Args:
            pages: List of page dicts with 'text' and 'page_number'
            document_id: Unique document identifier
            
        Returns:
            List of Chunk objects with metadata
        """
        logger.info("chunking_document", doc_id=document_id, num_pages=len(pages))
        
        all_chunks = []
        chunk_index = 0
        
        for page in pages:
            text = page['text']
            page_number = page['page_number']
            
            if not text.strip():
                continue
            
            # Split into chunks with overlap
            chunks = self._split_text_with_overlap(text)
            
            for chunk_text in chunks:
                if not chunk_text.strip():
                    continue
                
                chunk = Chunk(
                    chunk_id=generate_chunk_id(document_id, chunk_index),
                    document_id=document_id,
                    text=chunk_text,
                    page_number=page_number,
                    metadata={
                        'chunk_index': chunk_index,
                        'page_number': page_number,
                    }
                )
                all_chunks.append(chunk)
                chunk_index += 1
        
        logger.info("chunking_complete", doc_id=document_id, num_chunks=len(all_chunks))
        return all_chunks
    
    def _split_text_with_overlap(self, text: str) -> List[str]:
        """Split text into overlapping chunks."""
        if len(text) <= self.chunk_size:
            return [text]
        
        chunks = []
        start = 0
        last_end = 0
        
        while start < len(text):
            end = start + self.chunk_size
            
            # If not at the end, try to break at sentence boundary
            if end < len(text):
                # Look for sentence endings in the last 100 chars
                search_start = max(start, end - 100)
                sentence_ends = ['.', '!', '?', '\n']
                
                best_break = end
                for i in range(end, search_start, -1):
                    if text[i] in sentence_ends:
                        best_break = i + 1
                        break
                
                end = best_break
            
            chunk = text[start:end].strip()
            if chunk:
                chunks.append(chunk)
            
            # Move start forward with overlap
            start = end - self.chunk_overlap
            
            # Prevent infinite loop - if we're not making progress, jump ahead
            if start <= last_end:
                start = end
            
            last_end = end
        
        return chunks
