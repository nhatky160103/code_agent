"""Base Agent class for all specialized agents"""
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from openrouter_client import OpenRouterClient
from config import AGENT_ROLES, FREE_MODELS


class BaseAgent(ABC):
    """Base class for all agents in the system"""
    
    def __init__(self, agent_type: str, client: Optional[OpenRouterClient] = None):
        self.agent_type = agent_type
        self.client = client or OpenRouterClient()
        self.role = AGENT_ROLES.get(agent_type, "")
        self.model = FREE_MODELS.get("code", "google/gemini-flash-1.5-8b")
        self.conversation_history = []
    
    def _build_system_message(self, context: Dict[str, Any] = None) -> str:
        """Build system message with role and context"""
        system_msg = self.role
        
        if context:
            context_str = "\n".join([f"{k}: {v}" for k, v in context.items()])
            system_msg += f"\n\nContext:\n{context_str}"
        
        return system_msg
    
    def _call_llm(self, prompt: str, context: Dict[str, Any] = None) -> str:
        """Call LLM with prompt and context"""
        messages = [
            {"role": "system", "content": self._build_system_message(context)}
        ]
        
        # Add conversation history
        messages.extend(self.conversation_history[-5:])  # Last 5 messages
        
        # Add current prompt
        messages.append({"role": "user", "content": prompt})
        
        response = self.client.chat(messages, model=self.model)
        
        # Update conversation history
        self.conversation_history.append({"role": "user", "content": prompt})
        self.conversation_history.append({"role": "assistant", "content": response})
        
        return response
    
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

