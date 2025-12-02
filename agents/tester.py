"""Tester Agent - Writes and runs tests"""
import subprocess
import os
from typing import Dict, Any, List
from agents.base_agent import BaseAgent
from agents.code_reader import CodeReaderAgent
from config import WORKSPACE_PATH


class TesterAgent(BaseAgent):
    """Agent specialized in writing and running tests"""
    
    def __init__(self, client=None):
        super().__init__("tester", client)
        self.code_reader = CodeReaderAgent(client)
        self.workspace_path = WORKSPACE_PATH
    
    def write_test(self, code: str, file_path: str = "") -> str:
        """Write test cases for given code"""
        prompt = f"""
Write comprehensive test cases for the following code:

File: {file_path}

Code:
```python
{code}
```

Please provide:
1. Unit tests covering all functions
2. Edge cases
3. Error handling tests
4. Integration tests if applicable

Write tests in pytest format.
"""
        
        test_code = self._call_llm(prompt)
        return test_code
    
    def run_tests(self, test_file: str = None) -> Dict[str, Any]:
        """Run tests using pytest"""
        try:
            if test_file:
                cmd = ["pytest", test_file, "-v"]
            else:
                cmd = ["pytest", "-v"]
            
            result = subprocess.run(
                cmd,
                cwd=self.workspace_path,
                capture_output=True,
                text=True,
                timeout=60
            )
            
            return {
                "success": result.returncode == 0,
                "stdout": result.stdout,
                "stderr": result.stderr,
                "return_code": result.returncode
            }
        except subprocess.TimeoutExpired:
            return {
                "success": False,
                "error": "Test execution timeout",
                "stdout": "",
                "stderr": ""
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "stdout": "",
                "stderr": ""
            }
    
    def execute(self, task: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Execute testing task"""
        if context is None:
            context = {}
        
        file_path = context.get("file_path", "")
        code = context.get("code", "")
        action = context.get("action", "write")  # "write" or "run"
        
        if action == "write":
            if not code and file_path:
                code = self.code_reader.read_file(file_path)
            
            if not code:
                return {
                    "agent": "tester",
                    "task": task,
                    "error": "No code provided for test writing",
                    "status": "failed"
                }
            
            test_code = self.write_test(code, file_path)
            
            return {
                "agent": "tester",
                "task": task,
                "test_code": test_code,
                "file_path": file_path,
                "status": "completed"
            }
        
        elif action == "run":
            test_file = context.get("test_file")
            test_results = self.run_tests(test_file)
            
            return {
                "agent": "tester",
                "task": task,
                "test_results": test_results,
                "status": "completed"
            }
        
        return {
            "agent": "tester",
            "task": task,
            "error": f"Unknown action: {action}",
            "status": "failed"
        }

