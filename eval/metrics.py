"""
Metrics calculation for evaluation including LLM-as-judge.
"""

import numpy as np
from typing import Dict, Any, List
from vertexai.generative_models import GenerativeModel
from models.schemas import EvalMetrics
from utils.logger import get_logger
from config import get_settings

logger = get_logger(__name__)


class MetricsCalculator:
    """Calculate evaluation metrics."""
    
    def __init__(self):
        """Initialize metrics calculator."""
        self.settings = get_settings()
        self.llm = GenerativeModel(self.settings.vertex_model)
        logger.info("metrics_calculator_initialized")
    
    def calculate_metrics(self, eval_results: Dict[str, Any]) -> EvalMetrics:
        """
        Calculate metrics from evaluation results.
        
        Args:
            eval_results: Results from evaluator
            
        Returns:
            Evaluation metrics
        """
        logger.info("calculating_metrics")
        
        predictions = eval_results['predictions']
        
        # Calculate groundedness scores using LLM-as-judge
        groundedness_scores = []
        for pred in predictions:
            if not pred['was_refused']:
                score = self._judge_groundedness(
                    pred['predicted_answer'],
                    pred.get('source_chunk_id', '')
                )
                groundedness_scores.append(score)
        
        # Calculate correctness scores
        correctness_scores = []
        for pred in predictions:
            if not pred['was_refused']:
                score = self._judge_correctness(
                    pred['expected_answer'],
                    pred['predicted_answer']
                )
                correctness_scores.append(score)
        
        # Calculate latency percentiles
        latencies = eval_results['summary']['latencies_ms']
        p50 = float(np.percentile(latencies, 50)) if latencies else 0.0
        p95 = float(np.percentile(latencies, 95)) if latencies else 0.0
        p99 = float(np.percentile(latencies, 99)) if latencies else 0.0
        
        # Calculate refusal rate
        total = len(predictions)
        refused = sum(1 for p in predictions if p['was_refused'])
        refusal_rate = refused / total if total > 0 else 0.0
        
        # Create metrics
        metrics = EvalMetrics(
            dataset_version=eval_results['dataset_metadata'].get('generated_at', 'unknown'),
            total_samples=total,
            groundedness_avg=float(np.mean(groundedness_scores)) if groundedness_scores else 0.0,
            correctness_avg=float(np.mean(correctness_scores)) if correctness_scores else 0.0,
            latency_p50_ms=p50,
            latency_p95_ms=p95,
            latency_p99_ms=p99,
            refusal_rate=refusal_rate,
            details={
                'groundedness_scores': groundedness_scores,
                'correctness_scores': correctness_scores,
                'refusal_count': refused,
            }
        )
        
        logger.info("metrics_calculated", groundedness=metrics.groundedness_avg, correctness=metrics.correctness_avg)
        return metrics
    
    def _judge_groundedness(self, answer: str, source_chunk_id: str) -> float:
        """
        Use LLM to judge if answer is grounded in source.
        
        Returns:
            Groundedness score (0-1)
        """
        # Simplified version - in production, retrieve actual source text
        prompt = f"""Rate the groundedness of the following answer on a scale of 0.0 to 1.0.
Groundedness means the answer is supported by facts and doesn't make unsupported claims.

Answer: {answer}

Output only a number between 0.0 and 1.0:"""
        
        try:
            response = self.llm.generate_content(
                prompt,
                generation_config={'temperature': 0.0, 'max_output_tokens': 10}
            )
            score = float(response.text.strip())
            return max(0.0, min(1.0, score))
        except Exception as e:
            logger.warning("groundedness_judgment_failed", error=str(e))
            return 0.5  # Default neutral score
    
    def _judge_correctness(self, expected: str, predicted: str) -> float:
        """
        Use LLM to judge correctness of answer vs expected.
        
        Returns:
            Correctness score (0-1)
        """
        prompt = f"""Compare the predicted answer with the expected answer and rate their semantic similarity on a scale of 0.0 to 1.0.
1.0 means they convey the same meaning, 0.0 means completely different.

Expected Answer: {expected}

Predicted Answer: {predicted}

Output only a number between 0.0 and 1.0:"""
        
        try:
            response = self.llm.generate_content(
                prompt,
                generation_config={'temperature': 0.0, 'max_output_tokens': 10}
            )
            score = float(response.text.strip())
            return max(0.0, min(1.0, score))
        except Exception as e:
            logger.warning("correctness_judgment_failed", error=str(e))
            return 0.5  # Default neutral score
