"""
Synthetic Q/A dataset generator for evaluation.
Generates questions from uploaded documents using Gemini.
"""

import json
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any
from vertexai.generative_models import GenerativeModel
from rag.index import FAISSIndexManager
from utils.logger import get_logger
from config import get_settings

logger = get_logger(__name__)


class DatasetGenerator:
    """Generate synthetic Q/A datasets for evaluation."""
    
    def __init__(self, index_manager: FAISSIndexManager):
        """
        Initialize dataset generator.
        
        Args:
            index_manager: FAISS index manager with documents
        """
        self.index_manager = index_manager
        self.settings = get_settings()
        self.llm = GenerativeModel(self.settings.vertex_model)
        logger.info("dataset_generator_initialized")
    
    def generate_dataset(self, num_samples: int = 50) -> Dict[str, Any]:
        """
        Generate synthetic Q/A dataset from indexed documents.
        
        Args:
            num_samples: Number of Q/A pairs to generate
            
        Returns:
            Dataset dictionary with samples
        """
        logger.info("generating_dataset", num_samples=num_samples)
        
        samples = []
        chunks = self.index_manager.chunks
        
        if not chunks:
            logger.warning("no_chunks_available")
            return {'samples': [], 'metadata': {}}
        
        # Sample chunks evenly
        step = max(1, len(chunks) // num_samples)
        selected_chunks = chunks[::step][:num_samples]
        
        for i, chunk in enumerate(selected_chunks):
            logger.debug("generating_qa_pair", index=i+1)
            
            try:
                qa_pair = self._generate_qa_from_chunk(chunk.text, chunk.chunk_id)
                if qa_pair:
                    samples.append(qa_pair)
            except Exception as e:
                logger.warning("qa_generation_failed", index=i+1, error=str(e))
        
        # Create dataset
        dataset = {
            'metadata': {
                'generated_at': datetime.utcnow().isoformat() + 'Z',
                'num_samples': len(samples),
                'num_documents': len(set(c.document_id for c in chunks)),
            },
            'samples': samples
        }
        
        logger.info("dataset_generated", num_samples=len(samples))
        return dataset
    
    def _generate_qa_from_chunk(self, text: str, chunk_id: str) -> Dict[str, Any]:
        """Generate a Q/A pair from a chunk."""
        prompt = f"""Based on the following text, generate ONE specific question that can be answered using this text, and provide the answer.

Text:
{text}

Output format (JSON):
{{
  "question": "...",
  "answer": "..."
}}
"""
        
        try:
            response = self.llm.generate_content(
                prompt,
                generation_config={'temperature': 0.2, 'max_output_tokens': 512}
            )
            
            # Parse JSON response
            response_text = response.text.strip()
            # Remove markdown code blocks if present
            if response_text.startswith('```'):
                response_text = response_text.split('\n', 1)[1]
                response_text = response_text.rsplit('\n```', 1)[0]
            
            qa_data = json.loads(response_text)
            
            return {
                'question': qa_data['question'],
                'expected_answer': qa_data['answer'],
                'source_chunk_id': chunk_id,
            }
        
        except Exception as e:
            logger.error("qa_parsing_failed", error=str(e))
            return None
    
    def save_dataset(self, dataset: Dict[str, Any], output_dir: str = None) -> str:
        """
        Save dataset to disk with versioning.
        
        Args:
            dataset: Dataset dictionary
            output_dir: Optional output directory
            
        Returns:
            Path to saved dataset
        """
        if output_dir is None:
            output_dir = self.settings.eval_datasets_dir
        
        # Create versioned directory
        timestamp = datetime.utcnow().strftime("%Y-%m-%d_%H-%M-%S")
        dataset_dir = Path(output_dir) / timestamp
        dataset_dir.mkdir(parents=True, exist_ok=True)
        
        # Save dataset
        dataset_path = dataset_dir / "dataset.json"
        with open(dataset_path, 'w') as f:
            json.dump(dataset, f, indent=2)
        
        logger.info("dataset_saved", path=str(dataset_path))
        return str(dataset_path)
