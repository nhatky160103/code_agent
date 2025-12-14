"""Google AI Studio (Gemini) client used as an alternative LLM backend.

If GOOGLE_API_KEY is set in the environment/.env, the system can use
Gemini models directly instead of (or in addition to) OpenRouter.
"""
from __future__ import annotations

from typing import Optional, List, Dict, Any
import time
import random
from collections import deque

import google.generativeai as genai

from config import GOOGLE_API_KEY, GOOGLE_MODELS


class GoogleAIClient:
    """Minimal chat client wrapping google-generativeai for Gemini models."""

    # Simple in-process rate limiter to stay under free-tier RPM.
    _request_window = deque()
    _max_per_minute = 4  # below the free tier 5 RPM to give headroom

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or GOOGLE_API_KEY
        if not self.api_key:
            raise ValueError("GOOGLE_API_KEY is not set.")

        genai.configure(api_key=self.api_key)
        print("[LLM] Using Google Gemini backend")

    def _build_prompt_from_messages(self, messages: List[Dict[str, str]]) -> str:
        """Flatten OpenAI-style messages into a single prompt string.

        This preserves roles in a simple textual form, which is usually
        sufficient for Gemini chat-style prompting.
        """
        parts = []
        for msg in messages:
            role = msg.get("role", "user")
            content = msg.get("content", "")
            parts.append(f"{role}:\n{content}")
        return "\n\n".join(parts)

    def chat(
        self,
        messages: List[Dict[str, str]],
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 2048,
    ) -> str:
        """Send a chat-style request to Gemini and return the text response."""
        # Default to a good general model if none specified.
        model_name = model or GOOGLE_MODELS.get("code", "gemini-2.5-pro")

        prompt = self._build_prompt_from_messages(messages)
        
        # For code generation tasks, use higher token limit to avoid truncation
        # Gemini models support up to 8192 output tokens for most models
        effective_max_tokens = max(max_tokens, 8192) if max_tokens < 8192 else max_tokens

        # --- naive rate limiting to avoid 429 on free tier ---
        now = time.time()
        while self._request_window and now - self._request_window[0] > 60:
            self._request_window.popleft()
        if len(self._request_window) >= self._max_per_minute:
            wait_for = 60 - (now - self._request_window[0]) + random.uniform(0, 1.0)
            print(f"[LLM] Gemini throttle: sleeping {wait_for:.1f}s to respect RPM")
            time.sleep(wait_for)
        self._request_window.append(time.time())

        try:
            gen_model = genai.GenerativeModel(model_name)
            response = gen_model.generate_content(
                prompt,
                generation_config={
                    "temperature": temperature,
                    "max_output_tokens": effective_max_tokens,
                },
            )
            
            # Check if response has valid content
            if not response.candidates:
                return f"Error calling Google Gemini model '{model_name}': No candidates returned"
            
            candidate = response.candidates[0]
            finish_reason = getattr(candidate, "finish_reason", None)
            
            # Helper to extract text from parts robustly
            def extract_text_from_candidate(cand):
                """Extract text from candidate, trying multiple methods."""
                # Method 1: Try response.text (standard way)
                try:
                    if hasattr(response, "text") and response.text:
                        return response.text
                except (ValueError, AttributeError):
                    pass
                
                # Method 2: Extract from candidate.content.parts
                if hasattr(cand, "content") and cand.content:
                    if hasattr(cand.content, "parts") and cand.content.parts:
                        text_parts = []
                        for part in cand.content.parts:
                            # Try different ways to get text
                            if hasattr(part, "text") and part.text:
                                text_parts.append(str(part.text))
                            elif isinstance(part, str):
                                text_parts.append(part)
                            elif hasattr(part, "__dict__"):
                                # Try to find text in dict-like structure
                                part_dict = part.__dict__
                                if "text" in part_dict:
                                    text_parts.append(str(part_dict["text"]))
                        if text_parts:
                            return "".join(text_parts)
                
                # Method 3: Try to stringify the whole candidate
                try:
                    candidate_str = str(cand)
                    if candidate_str and len(candidate_str) > 10:
                        return candidate_str
                except Exception:
                    pass
                
                return None
            
            # finish_reason 2 = MAX_TOKENS (response was truncated)
            # finish_reason 3 = SAFETY (content was blocked)
            if finish_reason == 2:
                # Try to extract partial content
                partial_text = extract_text_from_candidate(candidate)
                if partial_text:
                    print(f"[LLM] Warning: Response truncated (finish_reason=MAX_TOKENS), returning partial content ({len(partial_text)} chars)")
                    return partial_text
                return f"Error calling Google Gemini model '{model_name}': Response truncated (finish_reason=MAX_TOKENS) but could not extract any text content"
            elif finish_reason == 3:
                return f"Error calling Google Gemini model '{model_name}': Content blocked by safety filters (finish_reason=SAFETY)"
            
            # Normal case: extract text
            text = extract_text_from_candidate(candidate)
            if text:
                return text
            
            return f"Error calling Google Gemini model '{model_name}': Could not extract text from response (finish_reason={finish_reason})"
        except Exception as exc:  # noqa: BLE001
            # If rate limit hit despite throttling, backoff and retry once more
            err_lower = str(exc).lower()
            if any(kw in err_lower for kw in ["rate", "quota", "429"]):
                backoff = 15 + random.uniform(0, 3)
                print(f"[LLM] Gemini rate-limit/quota hit, backing off {backoff:.1f}s")
                time.sleep(backoff)
                try:
                    gen_model = genai.GenerativeModel(model_name)
                    response = gen_model.generate_content(
                        prompt,
                        generation_config={
                            "temperature": temperature,
                            "max_output_tokens": effective_max_tokens,
                        },
                    )
                    if not response.candidates:
                        return f"Error calling Google Gemini model '{model_name}': No candidates returned"
                    candidate = response.candidates[0]
                    finish_reason = getattr(candidate, "finish_reason", None)
                    # reuse extractor from above via small helper
                    def extract_text_from_candidate(cand):
                        try:
                            if hasattr(response, "text") and response.text:
                                return response.text
                        except (ValueError, AttributeError):
                            pass
                        if hasattr(cand, "content") and cand.content:
                            if hasattr(cand.content, "parts") and cand.content.parts:
                                text_parts = []
                                for part in cand.content.parts:
                                    if hasattr(part, "text") and part.text:
                                        text_parts.append(str(part.text))
                                    elif isinstance(part, str):
                                        text_parts.append(part)
                                    elif hasattr(part, "__dict__"):
                                        part_dict = part.__dict__
                                        if "text" in part_dict:
                                            text_parts.append(str(part_dict["text"]))
                                if text_parts:
                                    return "".join(text_parts)
                        try:
                            candidate_str = str(cand)
                            if candidate_str and len(candidate_str) > 10:
                                return candidate_str
                        except Exception:
                            pass
                        return None
                    if finish_reason == 2:
                        partial_text = extract_text_from_candidate(candidate)
                        if partial_text:
                            print(f"[LLM] Warning: Response truncated (finish_reason=MAX_TOKENS), returning partial content ({len(partial_text)} chars)")
                            return partial_text
                        return f"Error calling Google Gemini model '{model_name}': Response truncated (finish_reason=MAX_TOKENS) but could not extract any text content"
                    if finish_reason == 3:
                        return f"Error calling Google Gemini model '{model_name}': Content blocked by safety filters (finish_reason=SAFETY)"
                    text = extract_text_from_candidate(candidate)
                    if text:
                        return text
                    return f"Error calling Google Gemini model '{model_name}': Could not extract text from response (finish_reason={finish_reason})"
                except Exception as retry_exc:  # noqa: BLE001
                    return f"Error calling Google Gemini model '{model_name}': {retry_exc}"

            return f"Error calling Google Gemini model '{model_name}': {exc}"


