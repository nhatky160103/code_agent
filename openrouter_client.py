"""OpenRouter API Client for free AI models"""
import json
from typing import Optional, Dict, Any
import requests
from config import OPENROUTER_API_KEY, OPENROUTER_BASE_URL, FREE_MODELS


class OpenRouterClient:
    """Client for interacting with OpenRouter API"""
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or OPENROUTER_API_KEY
        self.base_url = OPENROUTER_BASE_URL
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://github.com/code-agent",
            "X-Title": "Code Agent",
        }
    
    def chat(
        self,
        messages: list,
        model: str = None,
        temperature: float = 0.7,
        max_tokens: int = 2000,
    ) -> str:
        """Send chat request to OpenRouter"""
        if not model:
            model = FREE_MODELS["code"]
        
        payload = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }
        
        try:
            url = f"{self.base_url}/chat/completions"
            response = requests.post(
                url,
                headers=self.headers,
                json=payload,
                timeout=60
            )
            
            # Better error handling
            if response.status_code == 404:
                error_detail = response.text
                return f"Error 404: Endpoint not found. URL: {url}\nModel: {model}\nResponse: {error_detail}"
            elif response.status_code == 401:
                return f"Error 401: Unauthorized. Please check your API key."
            elif response.status_code == 400:
                error_detail = response.text
                return f"Error 400: Bad Request. Model '{model}' may be invalid.\nResponse: {error_detail}"
            
            response.raise_for_status()
            result = response.json()
            return result["choices"][0]["message"]["content"]
        except requests.exceptions.RequestException as e:
            return f"Error calling OpenRouter API: {str(e)}\nURL: {url if 'url' in locals() else 'N/A'}\nModel: {model}"
        except Exception as e:
            return f"Error calling OpenRouter API: {str(e)}"
    
    def get_available_models(self) -> list:
        """Get list of available free models"""
        try:
            response = requests.get(
                f"{self.base_url}/models",
                headers=self.headers,
                timeout=30
            )
            response.raise_for_status()
            models = response.json().get("data", [])
            # Filter free models
            free_models = [m for m in models if m.get("pricing", {}).get("prompt") == "0"]
            return free_models
        except Exception as e:
            print(f"Error fetching models: {e}")
            return []
    
    def test_connection(self) -> Dict[str, Any]:
        """Test API connection and return status"""
        result = {
            "api_key_set": bool(self.api_key),
            "base_url": self.base_url,
            "endpoint": f"{self.base_url}/chat/completions",
            "status": "unknown"
        }
        
        if not self.api_key:
            result["status"] = "error"
            result["message"] = "API key not set"
            return result
        
        try:
            # Try a simple request to test connection
            response = requests.get(
                f"{self.base_url}/models",
                headers=self.headers,
                timeout=10
            )
            if response.status_code == 200:
                result["status"] = "success"
                result["message"] = "API connection successful"
            else:
                result["status"] = "error"
                result["message"] = f"API returned status {response.status_code}: {response.text[:200]}"
        except Exception as e:
            result["status"] = "error"
            result["message"] = str(e)
        
        return result

