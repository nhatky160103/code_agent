"""
Smart LLM Client with Intelligent Rate Limiting and Context Management
Handles multiple LLM providers with adaptive retry strategies
"""

import os
import time
import json
from typing import Optional, Dict, Any, List
from enum import Enum
import structlog
from utils.rate_limiter import AdaptiveRateLimiter, Priority

logger = structlog.get_logger(__name__)


class LLMProvider(Enum):
    """Supported LLM providers"""
    GEMINI = "gemini"
    OPENAI = "openai"
    CLAUDE = "claude"
    OPENROUTER = "openrouter"


class ContextStrategy(Enum):
    """Strategies for managing context across multiple API calls"""
    FULL_CONTEXT = "full"          # Include all previous context
    SLIDING_WINDOW = "sliding"     # Keep only recent N messages
    SUMMARY = "summary"            # Summarize older context
    HIERARCHICAL = "hierarchical"   # Key points + recent details


class SmartLLMClient:
    """
    Intelligent LLM client with:
    - Adaptive rate limiting
    - Context management strategies
    - Provider failover
    - Cost optimization
    - Automatic retry with exponential backoff
    """
    
    def __init__(
        self,
        provider: LLMProvider = LLMProvider.GEMINI,
        api_key: Optional[str] = None,
        model: Optional[str] = None,
        max_requests_per_minute: int = 15,
        max_context_tokens: int = 30000,
        context_strategy: ContextStrategy = ContextStrategy.SLIDING_WINDOW,
        enable_caching: bool = True
    ):
        self.provider = provider
        self.api_key = api_key or self._get_api_key(provider)
        self.model = model or self._get_default_model(provider)
        self.max_context_tokens = max_context_tokens
        self.context_strategy = context_strategy
        self.enable_caching = enable_caching
        
        # Initialize rate limiter
        self.rate_limiter = AdaptiveRateLimiter(
            max_requests_per_minute=max_requests_per_minute,
            max_concurrent_requests=3,
            base_delay_seconds=5.0,
            max_delay_seconds=120.0
        )
        
        # Context management
        self.conversation_history: List[Dict[str, str]] = []
        self.context_summaries: List[str] = []
        
        # Response cache
        self.response_cache: Dict[str, Any] = {}
        
        # Initialize provider client
        self._initialize_provider()
        
        logger.info(
            "llm_client_initialized",
            provider=provider.value,
            model=self.model,
            max_rpm=max_requests_per_minute,
            context_strategy=context_strategy.value
        )
    
    def _get_api_key(self, provider: LLMProvider) -> str:
        """Get API key from environment"""
        env_vars = {
            LLMProvider.GEMINI: "GEMINI_API_KEY",
            LLMProvider.OPENAI: "OPENAI_API_KEY",
            LLMProvider.CLAUDE: "ANTHROPIC_API_KEY",
            LLMProvider.OPENROUTER: "OPENROUTER_API_KEY"
        }
        
        key = os.getenv(env_vars.get(provider, ""))
        if not key:
            raise ValueError(f"API key not found for {provider.value}. Set {env_vars[provider]} env var.")
        return key
    
    def _get_default_model(self, provider: LLMProvider) -> str:
        """Get default model for provider"""
        defaults = {
            LLMProvider.GEMINI: "gemini-2.5-flash",
            LLMProvider.OPENAI: "gpt-4-turbo-preview",
            LLMProvider.CLAUDE: "claude-3-5-sonnet-20241022",
            LLMProvider.OPENROUTER: "anthropic/claude-3.5-sonnet"
        }
        return defaults.get(provider, "gemini-2.5-flash")
    
    def _initialize_provider(self):
        """Initialize specific provider client"""
        if self.provider == LLMProvider.GEMINI:
            try:
                import google.generativeai as genai
                genai.configure(api_key=self.api_key)
                self.client = genai.GenerativeModel(self.model)
            except ImportError:
                raise ImportError("google-generativeai package required for Gemini")
        
        elif self.provider == LLMProvider.OPENAI:
            try:
                from openai import OpenAI
                self.client = OpenAI(api_key=self.api_key)
            except ImportError:
                raise ImportError("openai package required for OpenAI")
        
        elif self.provider == LLMProvider.CLAUDE:
            try:
                from anthropic import Anthropic
                self.client = Anthropic(api_key=self.api_key)
            except ImportError:
                raise ImportError("anthropic package required for Claude")
        
        elif self.provider == LLMProvider.OPENROUTER:
            try:
                from openai import OpenAI
                self.client = OpenAI(
                    base_url="https://openrouter.ai/api/v1",
                    api_key=self.api_key
                )
            except ImportError:
                raise ImportError("openai package required for OpenRouter")
    
    def _manage_context(
        self,
        new_message: str,
        system_prompt: Optional[str] = None
    ) -> List[Dict[str, str]]:
        """
        Intelligently manage conversation context based on strategy
        
        Returns optimized message list for API call
        """
        # Add new message to history
        self.conversation_history.append({
            "role": "user",
            "content": new_message
        })
        
        if self.context_strategy == ContextStrategy.FULL_CONTEXT:
            # Return all history
            messages = self.conversation_history.copy()
        
        elif self.context_strategy == ContextStrategy.SLIDING_WINDOW:
            # Keep only last N messages (e.g., last 10 exchanges)
            window_size = 20  # 10 user + 10 assistant messages
            messages = self.conversation_history[-window_size:]
        
        elif self.context_strategy == ContextStrategy.SUMMARY:
            # Summarize old context, keep recent messages
            recent_count = 10
            if len(self.conversation_history) > recent_count:
                # Keep recent messages
                recent_messages = self.conversation_history[-recent_count:]
                
                # Add summary of older context if available
                messages = []
                if self.context_summaries:
                    messages.append({
                        "role": "system",
                        "content": f"Previous conversation summary: {self.context_summaries[-1]}"
                    })
                messages.extend(recent_messages)
            else:
                messages = self.conversation_history.copy()
        
        elif self.context_strategy == ContextStrategy.HIERARCHICAL:
            # Keep key decisions + recent details
            messages = self._build_hierarchical_context()
        
        else:
            messages = self.conversation_history.copy()
        
        # Add system prompt if provided
        if system_prompt:
            messages.insert(0, {
                "role": "system",
                "content": system_prompt
            })
        
        # Estimate tokens and truncate if needed
        messages = self._truncate_to_token_limit(messages)
        
        return messages
    
    def _build_hierarchical_context(self) -> List[Dict[str, str]]:
        """Build hierarchical context with key points + recent details"""
        # This is a simplified version - in production, you'd use actual summarization
        if len(self.conversation_history) <= 15:
            return self.conversation_history.copy()
        
        # Take first few (initial requirements)
        key_messages = self.conversation_history[:3]
        
        # Take recent messages
        recent_messages = self.conversation_history[-10:]
        
        # Add summary bridge
        middle_summary = {
            "role": "system",
            "content": f"[{len(self.conversation_history) - 13} messages summarized: Task planning and file generation in progress]"
        }
        
        return key_messages + [middle_summary] + recent_messages
    
    def _truncate_to_token_limit(
        self,
        messages: List[Dict[str, str]]
    ) -> List[Dict[str, str]]:
        """Truncate messages to fit within token limit"""
        # Rough estimation: 1 token ≈ 4 characters
        estimated_tokens = sum(len(m["content"]) // 4 for m in messages)
        
        if estimated_tokens <= self.max_context_tokens:
            return messages
        
        logger.warning(
            "context_truncated",
            estimated_tokens=estimated_tokens,
            limit=self.max_context_tokens
        )
        
        # Remove oldest messages until within limit
        while estimated_tokens > self.max_context_tokens and len(messages) > 2:
            # Keep system message and most recent message
            if messages[0].get("role") == "system":
                # Remove second message
                removed = messages.pop(1)
            else:
                # Remove first message
                removed = messages.pop(0)
            
            estimated_tokens -= len(removed["content"]) // 4
        
        return messages
    
    def _generate_cache_key(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        **kwargs
    ) -> str:
        """Generate cache key for request"""
        import hashlib
        cache_data = {
            "prompt": prompt,
            "system_prompt": system_prompt,
            "model": self.model,
            **kwargs
        }
        cache_str = json.dumps(cache_data, sort_keys=True)
        return hashlib.md5(cache_str.encode()).hexdigest()
    
    def _call_provider_api(
        self,
        messages: List[Dict[str, str]],
        **kwargs
    ) -> str:
        """Make actual API call to provider"""
        if self.provider == LLMProvider.GEMINI:
            # Gemini uses different message format
            # Convert messages to Gemini format
            prompt_parts = []
            for msg in messages:
                role = msg["role"]
                content = msg["content"]
                if role == "system":
                    prompt_parts.append(f"System: {content}\n")
                elif role == "user":
                    prompt_parts.append(f"User: {content}\n")
                elif role == "assistant":
                    prompt_parts.append(f"Assistant: {content}\n")
            
            prompt = "\n".join(prompt_parts)
            response = self.client.generate_content(
                prompt,
                generation_config=kwargs.get("generation_config")
            )
            return response.text
        
        elif self.provider == LLMProvider.OPENAI:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                **kwargs
            )
            return response.choices[0].message.content
        
        elif self.provider == LLMProvider.CLAUDE:
            # Separate system message
            system_msg = None
            user_messages = []
            for msg in messages:
                if msg["role"] == "system":
                    system_msg = msg["content"]
                else:
                    user_messages.append(msg)
            
            response = self.client.messages.create(
                model=self.model,
                max_tokens=kwargs.get("max_tokens", 4096),
                system=system_msg,
                messages=user_messages
            )
            return response.content[0].text
        
        elif self.provider == LLMProvider.OPENROUTER:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                **kwargs
            )
            return response.choices[0].message.content
        
        else:
            raise ValueError(f"Unsupported provider: {self.provider}")
    
    async def generate_async(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        priority: Priority = Priority.MEDIUM,
        context: Optional[str] = None,
        use_cache: bool = True,
        **kwargs
    ) -> str:
        """
        Generate response with intelligent rate limiting (async)
        
        Args:
            prompt: User prompt/message
            system_prompt: Optional system prompt
            priority: Request priority level
            context: Description for logging
            use_cache: Whether to use response cache
            **kwargs: Additional provider-specific parameters
        
        Returns:
            Generated text response
        """
        # Check cache
        if use_cache and self.enable_caching:
            cache_key = self._generate_cache_key(prompt, system_prompt, **kwargs)
            if cache_key in self.response_cache:
                logger.info("cache_hit", context=context)
                return self.response_cache[cache_key]
        
        # Prepare messages with context management
        messages = self._manage_context(prompt, system_prompt)
        
        # Execute with rate limiting and retry
        async def api_call():
            return self._call_provider_api(messages, **kwargs)
        
        response = await self.rate_limiter.execute_with_retry(
            api_call,
            max_retries=5,
            priority=priority,
            context=context or f"Generate: {prompt[:50]}..."
        )
        
        # Add response to history
        self.conversation_history.append({
            "role": "assistant",
            "content": response
        })
        
        # Cache response
        if use_cache and self.enable_caching:
            self.response_cache[cache_key] = response
        
        return response
    
    def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        priority: Priority = Priority.MEDIUM,
        context: Optional[str] = None,
        use_cache: bool = True,
        **kwargs
    ) -> str:
        """
        Generate response (sync version)
        
        See generate_async for parameters
        """
        import asyncio
        
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        
        return loop.run_until_complete(
            self.generate_async(
                prompt,
                system_prompt=system_prompt,
                priority=priority,
                context=context,
                use_cache=use_cache,
                **kwargs
            )
        )
    
    def batch_generate(
        self,
        prompts: List[Dict[str, Any]],
        delay_between: float = 5.0
    ) -> List[str]:
        """
        Generate multiple responses in batch with intelligent spacing
        
        Args:
            prompts: List of dicts with 'prompt', 'priority', 'context', etc.
            delay_between: Base delay between requests
        
        Returns:
            List of generated responses
        """
        import asyncio
        
        async def batch_process():
            results = []
            
            # Sort by priority
            sorted_prompts = sorted(
                prompts,
                key=lambda p: p.get('priority', Priority.MEDIUM).value
            )
            
            for i, prompt_config in enumerate(sorted_prompts):
                response = await self.generate_async(**prompt_config)
                results.append(response)
                
                # Adaptive delay based on rate limiter status
                if i < len(sorted_prompts) - 1:
                    status = self.rate_limiter.get_status()
                    if status['tokens_available'] < 2:
                        # Low on tokens, wait longer
                        await asyncio.sleep(delay_between * 2)
                    else:
                        await asyncio.sleep(delay_between)
            
            return results
        
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        
        return loop.run_until_complete(batch_process())
    
    def get_status(self) -> Dict[str, Any]:
        """Get comprehensive client status"""
        return {
            "provider": self.provider.value,
            "model": self.model,
            "conversation_length": len(self.conversation_history),
            "cache_size": len(self.response_cache),
            "rate_limiter": self.rate_limiter.get_status(),
            "context_strategy": self.context_strategy.value
        }
    
    def reset_conversation(self):
        """Reset conversation history"""
        self.conversation_history = []
        self.context_summaries = []
        logger.info("conversation_reset")
    
    def clear_cache(self):
        """Clear response cache"""
        self.response_cache = {}
        logger.info("cache_cleared")
