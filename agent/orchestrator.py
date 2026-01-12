"""
Agent orchestrator implementing the workflow graph.
Lightweight custom implementation (Google ADK alternative).
"""

import time
from agent.state import AgentState
from agent.nodes import AgentNodes
from utils.logger import get_logger
from utils.helpers import get_timestamp

logger = get_logger(__name__)


class AgentOrchestrator:
    """Orchestrate agent workflow execution."""
    
    def __init__(self, agent_nodes: AgentNodes):
        """
        Initialize orchestrator.
        
        Args:
            agent_nodes: Agent nodes instance
        """
        self.nodes = agent_nodes
        logger.info("agent_orchestrator_initialized")
    
    def execute(self, state: AgentState) -> AgentState:
        """
        Execute the agent workflow.
        
        Workflow:
        1. Intent Classification
        2. Conditional routing:
           - If needs retrieval: Retriever Node
           - If needs tools: MCP Tool Node
        3. Answer Synthesizer
        4. Safety Validator
        5. Audit Logger
        
        Args:
            state: Initial agent state
            
        Returns:
            Final agent state with answer or refusal
        """
        logger.info("agent_workflow_started", request_id=state.request_id)
        state.start_time = time.time()
        
        try:
            # Step 1: Classify intent
            state = self.nodes.intent_classifier(state)
            
            # Step 2: Conditional execution based on intent
            if state.intent in ["retrieve", "both"]:
                state = self.nodes.retriever_node(state)
            
            if state.intent in ["tool_call", "both"]:
                state = self.nodes.mcp_tool_node(state)
            
            # Step 3: Synthesize answer
            state = self.nodes.synthesizer_node(state)
            
            # Step 4: Safety validation
            state = self.nodes.safety_node(state)
            
            # If should refuse, replace answer
            if state.should_refuse:
                state.answer = state.refusal_message
                logger.warning("answer_refused", request_id=state.request_id, reason=state.refusal_message)
            
            # Step 5: Audit logging
            state = self.nodes.audit_node(state)
            
        except Exception as e:
            logger.error("agent_workflow_error", request_id=state.request_id, error=str(e))
            state.answer = "An error occurred processing your request. Please try again."
            state.should_refuse = True
        
        finally:
            state.end_time = time.time()
        
        logger.info(
            "agent_workflow_completed",
            request_id=state.request_id,
            duration_ms=state.get_total_duration_ms()
        )
        
        return state
