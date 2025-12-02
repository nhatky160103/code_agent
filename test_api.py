"""Test script for OpenRouter API connection"""
from openrouter_client import OpenRouterClient
from config import OPENROUTER_API_KEY

def test_api_connection():
    """Test OpenRouter API connection"""
    print("=" * 80)
    print("Testing OpenRouter API Connection")
    print("=" * 80)
    
    if not OPENROUTER_API_KEY:
        print("Error: OPENROUTER_API_KEY not set in .env file")
        return
    
    client = OpenRouterClient()
    
    # Test connection
    print("\n1. Testing API connection...")
    connection_test = client.test_connection()
    print(f"   API Key Set: {connection_test['api_key_set']}")
    print(f"   Base URL: {connection_test['base_url']}")
    print(f"   Endpoint: {connection_test['endpoint']}")
    print(f"   Status: {connection_test['status']}")
    if 'message' in connection_test:
        print(f"   Message: {connection_test['message']}")
    
    if connection_test['status'] != 'success':
        print("\nConnection test failed. Please check your API key and network connection.")
        return
    
    # Get available models
    print("\n2. Fetching available models...")
    models = client.get_available_models()
    if models:
        print(f"   Found {len(models)} free models:")
        for i, model in enumerate(models[:10], 1):  # Show first 10
            model_id = model.get('id', 'N/A')
            print(f"   {i}. {model_id}")
        if len(models) > 10:
            print(f"   ... and {len(models) - 10} more")
    else:
        print("   No free models found or error fetching models")
    
    # Test a simple chat request
    print("\n3. Testing chat completion...")
    test_messages = [
        {"role": "user", "content": "Say hello in one word"}
    ]
    
    # Try with default model
    print("   Trying with default model...")
    response = client.chat(test_messages)
    if response.startswith("Error"):
        print(f"   Error: {response}")
        print("\n   Tip: The model name might be incorrect. Check available models above.")
    else:
        print(f"   Success! Response: {response}")

if __name__ == "__main__":
    test_api_connection()

