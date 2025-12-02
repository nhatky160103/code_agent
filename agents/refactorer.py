"""Refactorer Agent - Refactors code for better quality"""
from typing import Dict, Any
from agents.base_agent import BaseAgent
from agents.code_reader import CodeReaderAgent


class RefactorerAgent(BaseAgent):
    """Agent specialized in refactoring code"""
    
    def __init__(self, client=None):
        super().__init__("refactorer", client)
        self.code_reader = CodeReaderAgent(client)
    
    def refactor_code(self, code: str, file_path: str = "", improvements: str = "") -> Dict[str, Any]:
        """Refactor code for better quality"""
        prompt = f"""
Refactor the following code to improve quality, readability, and maintainability:

File: {file_path}
Specific improvements requested: {improvements or 'General refactoring'}

Original Code:
```python
{code}
```

Please provide:
1. Refactored code
2. List of improvements made
3. Explanation of changes
4. Before/after comparison

Keep the functionality exactly the same, only improve code quality.
"""
        
        refactored = self._call_llm(prompt)
        return {"refactored_code": refactored, "file_path": file_path}
    
    def execute(self, task: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Execute refactoring task"""
        if context is None:
            context = {}
        
        file_path = context.get("file_path", "")
        code = context.get("code", "")
        improvements = context.get("improvements", "")
        
        if not code and file_path:
            code = self.code_reader.read_file(file_path)
        
        if not code:
            return {
                "agent": "refactorer",
                "task": task,
                "error": "No code provided for refactoring",
                "status": "failed"
            }
        
        result = self.refactor_code(code, file_path, improvements)
        
        return {
            "agent": "refactorer",
            "task": task,
            "file_path": file_path,
            "result": result,
            "status": "completed"
        }

