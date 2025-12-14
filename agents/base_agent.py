"""Base Agent class for all specialized agents"""
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
import time

from openrouter_client import get_default_client
from config import AGENT_ROLES, FREE_MODELS, GOOGLE_MODELS
from utils.logging import get_logger, get_metrics
from utils.cache import cache_llm_response
from utils.rate_limiter import call_llm_with_retry


class BaseAgent(ABC):
    """Base class for all agents in the system"""
    
    def __init__(self, agent_type: str, client: Optional[object] = None):
        self.agent_type = agent_type
        # Pick a default client if one is not injected (OpenRouter or Gemini).
        self.client = client or get_default_client()
        self.role = AGENT_ROLES.get(agent_type, "")

        # Choose model family depending on whether we are running on
        # OpenRouter or Gemini. We don't introspect the client type,
        # instead we select from GOOGLE_MODELS first if available.
        if GOOGLE_MODELS.get("code"):
            self.model = GOOGLE_MODELS["code"]
        else:
            self.model = FREE_MODELS.get("code", "google/gemini-flash-1.5-8b")
        self.conversation_history = []
        
        # Setup logging and metrics
        self.logger = get_logger(f"agent.{agent_type}")
        self.metrics = get_metrics()
    
    def _build_system_message(self, context: Dict[str, Any] = None) -> str:
        """Build system message with role and context"""
        system_msg = self.role
        
        if context:
            context_str = "\n".join([f"{k}: {v}" for k, v in context.items()])
            system_msg += f"\n\nContext:\n{context_str}"
        
        return system_msg
    
    @call_llm_with_retry(max_retries=3, initial_wait=1.0, max_wait=60.0)
    @cache_llm_response(ttl=3600)
    def _call_llm(self, prompt: str, context: Dict[str, Any] = None) -> str:
        """Call LLM with prompt and context (with caching and retry)"""
        start_time = time.time()
        
        self.logger.info(
            "llm_request_started",
            agent=self.agent_type,
            model=self.model,
            prompt_length=len(prompt)
        )
        
        messages = [
            {"role": "system", "content": self._build_system_message(context)}
        ]
        
        # Add conversation history
        messages.extend(self.conversation_history[-5:])  # Last 5 messages
        
        # Add current prompt
        messages.append({"role": "user", "content": prompt})
        
        try:
            response = self.client.chat(messages, model=self.model)
            
            # Calculate duration
            duration = time.time() - start_time
            
            # Update metrics
            self.metrics["llm_requests_total"].labels(
                agent=self.agent_type,
                model=self.model,
                status="success"
            ).inc()
            
            self.metrics["llm_request_duration"].labels(
                agent=self.agent_type,
                model=self.model
            ).observe(duration)
            
            # Estimate tokens (rough approximation: 1 token ≈ 4 characters)
            input_tokens = sum(len(m.get("content", "")) for m in messages) // 4
            output_tokens = len(response) // 4
            
            self.metrics["llm_tokens_total"].labels(
                agent=self.agent_type,
                model=self.model,
                type="input"
            ).inc(input_tokens)
            
            self.metrics["llm_tokens_total"].labels(
                agent=self.agent_type,
                model=self.model,
                type="output"
            ).inc(output_tokens)
            
            self.logger.info(
                "llm_request_completed",
                agent=self.agent_type,
                model=self.model,
                duration=duration,
                response_length=len(response),
                input_tokens=input_tokens,
                output_tokens=output_tokens
            )
            
            # Update conversation history
            self.conversation_history.append({"role": "user", "content": prompt})
            self.conversation_history.append({"role": "assistant", "content": response})
            
            return response
            
        except Exception as e:
            duration = time.time() - start_time
            
            # Update metrics
            self.metrics["llm_requests_total"].labels(
                agent=self.agent_type,
                model=self.model,
                status="error"
            ).inc()
            
            self.logger.error(
                "llm_request_failed",
                agent=self.agent_type,
                model=self.model,
                duration=duration,
                error=str(e),
                error_type=type(e).__name__
            )
            
            raise
    
    @abstractmethod
    def execute(self, task: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Execute agent's main task"""
        pass
    
    def communicate(self, message: str, from_agent: str = None) -> str:
        """Communicate with other agents"""
        context = {}
        if from_agent:
            context["from_agent"] = from_agent
        
        return self._call_llm(message, context)

