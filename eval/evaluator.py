"""
Evaluation job runner to execute queries and collect results.
"""

import json
from pathlib import Path
from typing import List, Dict, Any
import time
from agent.orchestrator import AgentOrchestrator
from agent.state import AgentState
from utils.logger import get_logger
from utils.helpers import generate_request_id, generate_session_id

logger = get_logger(__name__)


class Evaluator:
    """Run evaluation on golden datasets."""
    
    def __init__(self, agent_orchestrator: AgentOrchestrator):
        """
        Initialize evaluator.
        
        Args:
            agent_orchestrator: Agent orchestrator instance
        """
        self.orchestrator = agent_orchestrator
        logger.info("evaluator_initialized")
    
    def run_evaluation(self, dataset_path: str) -> Dict[str, Any]:
        """
        Run evaluation on a dataset.
        
        Args:
            dataset_path: Path to dataset JSON file
            
        Returns:
            Evaluation results with predictions and metadata
        """
        logger.info("running_evaluation", dataset_path=dataset_path)
        
        # Load dataset
        with open(dataset_path, 'r') as f:
            dataset = json.load(f)
        
        samples = dataset['samples']
        predictions = []
        latencies = []
        
        for i, sample in enumerate(samples):
            logger.debug("evaluating_sample", index=i+1, total=len(samples))
            
            # Create agent state
            state = AgentState(
                query=sample['question'],
                session_id=generate_session_id(),
                request_id=generate_request_id(),
                top_k=5
            )
            
            # Execute agent
            start = time.time()
            result_state = self.orchestrator.execute(state)
            latency = (time.time() - start) * 1000
            
            latencies.append(latency)
            
            # Collect prediction
            prediction = {
                'question': sample['question'],
                'expected_answer': sample['expected_answer'],
                'predicted_answer': result_state.answer,
                'source_chunk_id': sample.get('source_chunk_id'),
                'num_citations': len(result_state.citations),
                'grounding_score': result_state.safety_validation.grounding_score if result_state.safety_validation else 0.0,
                'confidence_score': result_state.safety_validation.confidence_score if result_state.safety_validation else 0.0,
                'was_refused': result_state.should_refuse,
                'latency_ms': latency,
            }
            predictions.append(prediction)
        
        # Compile results
        results = {
            'dataset_metadata': dataset.get('metadata', {}),
            'predictions': predictions,
            'summary': {
                'total_samples': len(samples),
                'evaluated': len(predictions),
                'latencies_ms': latencies,
            }
        }
        
        logger.info("evaluation_completed", total=len(predictions))
        return results
