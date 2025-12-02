"""Simple test to verify the system works"""
import os
import sys

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_imports():
    """Test that all modules can be imported"""
    try:
        from config import OPENROUTER_API_KEY, FREE_MODELS
        print("Config imported successfully")
        
        from openrouter_client import OpenRouterClient
        print("OpenRouterClient imported successfully")
        
        from agents.base_agent import BaseAgent
        print("BaseAgent imported successfully")
        
        from agents import (
            CodeReaderAgent,
            BugFixerAgent,
            RefactorerAgent,
            TesterAgent,
            PRGeneratorAgent,
            ArchitectAgent,
        )
        print("All agents imported successfully")
        
        from workflow import CodeAgentWorkflow
        print("CodeAgentWorkflow imported successfully")
        
        return True
    except ImportError as e:
        print(f"Import error: {e}")
        return False

def test_agent_initialization():
    """Test that agents can be initialized"""
    try:
        from openrouter_client import OpenRouterClient
        from agents import CodeReaderAgent
        
        client = OpenRouterClient()
        agent = CodeReaderAgent(client)
        print("Agent initialization successful")
        return True
    except Exception as e:
        print(f"Agent initialization error: {e}")
        return False

if __name__ == "__main__":
    print("Running simple tests...\n")
    
    test1 = test_imports()
    print()
    test2 = test_agent_initialization()
    
    if test1 and test2:
        print("\nAll tests passed!")
    else:
        print("\nSome tests failed")

