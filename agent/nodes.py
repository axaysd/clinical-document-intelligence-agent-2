"""
Agent nodes implementing the workflow steps.
Each node is a function that takes state and returns updated state.
"""

import time
from typing import Dict, Any
from agent.state import AgentState
from models.schemas import AuditEvent, NodeType
from rag.retriever import Retriever
from mcp.client import MCPClient
from safety.validators import SafetyValidator
from safety.filters import ContentFilter
from utils.logger import get_logger
from utils.helpers import get_timestamp
from vertexai.generative_models import GenerativeModel
from config import get_settings

logger = get_logger(__name__)


class AgentNodes:
    """Collection of agent workflow nodes."""
    
    def __init__(self, retriever: Retriever):
        """
        Initialize agent nodes.
        
        Args:
            retriever: RAG retriever instance
        """
        self.retriever = retriever
        self.mcp_client = MCPClient()
        self.safety_validator = SafetyValidator()
        self.content_filter = ContentFilter()
        self.settings = get_settings()
        
        # Initialize Vertex AI Gemini
        self.llm = GenerativeModel(self.settings.vertex_model)
        
        logger.info("agent_nodes_initialized")
    
    def intent_classifier(self, state: AgentState) -> AgentState:
        """
        Classify user intent to determine workflow path.
        
        Args:
            state: Current agent state
            
        Returns:
            Updated state with intent classification
        """
        start = time.time()
        query_lower = state.query.lower()
        
        # Simple heuristic-based classification
        # In production, this could use an LLM classifier
        
        tool_keywords = {
            'calculator': ['calculate', 'compute', 'add', 'subtract', 'multiply', 'divide', 'sum'],
            'phi_detector': ['phi', 'pii', 'personal information', 'protected health', 'privacy'],
        }
        
        needs_tool = False
        for tool, keywords in tool_keywords.items():
            if any(kw in query_lower for kw in keywords):
                needs_tool = True
                break
        
        # Most queries should retrieve from documents
        needs_retrieval = True
        
        if needs_tool and needs_retrieval:
            state.intent = "both"
        elif needs_tool:
            state.intent = "tool_call"
        else:
            state.intent = "retrieve"
        
        # Add audit event
        duration = (time.time() - start) * 1000
        state.add_audit_event(AuditEvent(
            node_type=NodeType.INTENT_CLASSIFIER,
            timestamp=get_timestamp(),
            data={'intent': state.intent},
            duration_ms=duration
        ))
        
        logger.info("intent_classified", intent=state.intent, duration_ms=duration)
        return state
    
    def retriever_node(self, state: AgentState) -> AgentState:
        """
        Retrieve relevant document chunks.
        
        Args:
            state: Current agent state
            
        Returns:
            Updated state with citations
        """
        start = time.time()
        
        # Retrieve citations
        citations = self.retriever.retrieve(state.query, top_k=state.top_k)
        state.citations = citations
        
        # Build context from citations
        context_parts = []
        for i, citation in enumerate(citations):
            full_text = self.retriever.get_chunk_text(citation.chunk_id)
            context_parts.append(f"[{i+1}] {full_text}")
        
        state.retrieved_context = "\n\n".join(context_parts)
        
        # Add audit event
        duration = (time.time() - start) * 1000
        state.add_audit_event(AuditEvent(
            node_type=NodeType.RETRIEVER,
            timestamp=get_timestamp(),
            data={
                'num_citations': len(citations),
                'top_similarity': citations[0].similarity_score if citations else 0.0
            },
            duration_ms=duration
        ))
        
        logger.info("retrieval_completed", num_citations=len(citations), duration_ms=duration)
        return state
    
    def mcp_tool_node(self, state: AgentState) -> AgentState:
        """
        Execute MCP tools based on query.
        
        Args:
            state: Current agent state
            
        Returns:
            Updated state with tool results
        """
        start = time.time()
        
        # Simple heuristic to determine which tools to call
        # In production, use LLM for tool selection
        query_lower = state.query.lower()
        
        # Check for calculator needs
        if any(kw in query_lower for kw in ['calculate', 'compute', 'add', 'multiply', 'divide']):
            # For demo, extract numbers if present
            import re
            numbers = re.findall(r'\d+\.?\d*', state.query)
            if len(numbers) >= 2:
                tool_call = self.mcp_client.call_tool(
                    'calculator',
                    {
                        'operation': 'add',  # Default to add
                        'a': float(numbers[0]),
                        'b': float(numbers[1])
                    }
                )
                state.tool_calls.append(tool_call)
                if tool_call.result:
                    state.tool_results['calculator'] = tool_call.result
        
        # Check for PHI detection needs
        if any(kw in query_lower for kw in ['phi', 'pii', 'personal', 'privacy']):
            # Scan the query itself
            tool_call = self.mcp_client.call_tool(
                'phi_detector',
                {'text': state.query}
            )
            state.tool_calls.append(tool_call)
            if tool_call.result:
                state.tool_results['phi_detector'] = tool_call.result
        
        # Add audit event
        duration = (time.time() - start) * 1000
        state.add_audit_event(AuditEvent(
            node_type=NodeType.MCP_TOOL,
            timestamp=get_timestamp(),
            data={'num_tool_calls': len(state.tool_calls)},
            duration_ms=duration
        ))
        
        logger.info("mcp_tools_executed", num_calls=len(state.tool_calls), duration_ms=duration)
        return state
    
    def synthesizer_node(self, state: AgentState) -> AgentState:
        """
        Generate answer using Vertex AI Gemini with retrieved context.
        
        Args:
            state: Current agent state
            
        Returns:
            Updated state with generated answer
        """
        start = time.time()
        
        # Build prompt with context
        prompt_parts = [
            "You are a clinical document assistant. Answer the question based ONLY on the provided context.",
            "If the context doesn't contain enough information to answer, say so.",
            "",
            "Context from documents:",
            state.retrieved_context,
            ""
        ]
        
        # Add tool results if available
        if state.tool_results:
            prompt_parts.append("Tool execution results:")
            for tool_name, result in state.tool_results.items():
                prompt_parts.append(f"- {tool_name}: {result}")
            prompt_parts.append("")
        
        prompt_parts.append(f"Question: {state.query}")
        prompt_parts.append("")
        prompt_parts.append("Answer (cite sources using [1], [2], etc.):")
        
        prompt = "\n".join(prompt_parts)
        
        try:
            # Generate answer using Gemini
            response = self.llm.generate_content(
                prompt,
                generation_config={
                    'temperature': self.settings.vertex_temperature,
                    'max_output_tokens': self.settings.vertex_max_tokens,
                }
            )
            
            state.answer = response.text
            
        except Exception as e:
            logger.error("synthesis_failed", error=str(e))
            state.answer = "I encountered an error generating the answer. Please try again."
        
        # Add medical disclaimer if needed
        state.answer = self.content_filter.add_medical_disclaimer(state.answer)
        
        # Add audit event
        duration = (time.time() - start) * 1000
        state.add_audit_event(AuditEvent(
            node_type=NodeType.SYNTHESIZER,
            timestamp=get_timestamp(),
            data={'answer_length': len(state.answer)},
            duration_ms=duration
        ))
        
        logger.info("answer_synthesized", answer_length=len(state.answer), duration_ms=duration)
        return state
    
    def safety_node(self, state: AgentState) -> AgentState:
        """
        Validate safety of query and answer.
        
        Args:
            state: Current agent state
            
        Returns:
            Updated state with safety validation
        """
        start = time.time()
        
        # Run safety validation
        validation = self.safety_validator.validate(
            state.query,
            state.answer,
            state.citations
        )
        state.safety_validation = validation
        
        # Apply refusal policy
        should_refuse, refusal_msg = self.safety_validator.apply_refusal_policy(validation)
        state.should_refuse = should_refuse
        state.refusal_message = refusal_msg
        
        # Add audit event
        duration = (time.time() - start) * 1000
        state.add_audit_event(AuditEvent(
            node_type=NodeType.SAFETY_VALIDATOR,
            timestamp=get_timestamp(),
            data={
                'decision': validation.decision.value,
                'grounding_score': validation.grounding_score,
                'confidence_score': validation.confidence_score,
                'flags': validation.flags,
            },
            duration_ms=duration
        ))
        
        logger.info("safety_validated", decision=validation.decision, duration_ms=duration)
        return state
    
    def audit_node(self, state: AgentState) -> AgentState:
        """
        Log audit event (final node).
        
        Args:
            state: Current agent state
            
        Returns:
            Updated state
        """
        start = time.time()
        
        # This is a placeholder - in production, write to persistent storage
        logger.info(
            "audit_complete",
            request_id=state.request_id,
            num_events=len(state.audit_events),
            total_duration_ms=state.get_total_duration_ms()
        )
        
        duration = (time.time() - start) * 1000
        state.add_audit_event(AuditEvent(
            node_type=NodeType.AUDIT_LOGGER,
            timestamp=get_timestamp(),
            data={'audit_logged': True},
            duration_ms=duration
        ))
        
        return state
