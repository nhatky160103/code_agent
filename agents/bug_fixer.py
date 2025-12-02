"""Bug Fixer Agent - Finds and fixes bugs"""
from typing import Dict, Any
from agents.base_agent import BaseAgent
from agents.code_reader import CodeReaderAgent


class BugFixerAgent(BaseAgent):
    """Agent specialized in finding and fixing bugs"""
    
    def __init__(self, client=None):
        super().__init__("bug_fixer", client)
        self.code_reader = CodeReaderAgent(client)
    
    def find_bugs(self, code: str, file_path: str = "") -> Dict[str, Any]:
        """Analyze code for potential bugs"""
        prompt = f"""
Analyze the following code for bugs, errors, and issues:

File: {file_path}

Code:
```python
{code}
```

Please identify:
1. Syntax errors
2. Logic errors
3. Potential runtime errors
4. Security issues
5. Performance problems

Provide specific line numbers and explanations for each issue found.
"""
        
        analysis = self._call_llm(prompt)
        return {"analysis": analysis, "file_path": file_path}
    
    def fix_bug(self, code: str, bug_description: str, file_path: str = "") -> str:
        """Fix a specific bug in code"""
        prompt = f"""
Fix the following bug in the code:

File: {file_path}
Bug Description: {bug_description}

Original Code:
```python
{code}
```

Please provide the fixed code with explanations of what was changed and why.
"""
        
        fixed_code = self._call_llm(prompt)
        return fixed_code
    
    def execute(self, task: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Execute bug fixing task"""
        if context is None:
            context = {}
        
        # Get codebase info from context or read it
        file_path = context.get("file_path", "")
        code = context.get("code", "")
        
        if not code and file_path:
            code = self.code_reader.read_file(file_path)
        elif not code:
            # Analyze entire codebase
            analysis = self.code_reader.analyze_codebase(max_files=10)
            results = []
            
            for path, content in analysis["file_contents"].items():
                bug_analysis = self.find_bugs(content, path)
                results.append(bug_analysis)
            
            summary_prompt = f"""
Task: {task}

I've analyzed multiple files. Here are the bug findings:
{chr(10).join([r['analysis'] for r in results])}

Please provide a summary of all bugs found and prioritize them by severity.
"""
            
            summary = self._call_llm(summary_prompt)
            
            return {
                "agent": "bug_fixer",
                "task": task,
                "bugs_found": results,
                "summary": summary,
                "status": "completed"
            }
        
        # Fix specific bug
        bug_description = context.get("bug_description", "Find and fix all bugs")
        bug_analysis = self.find_bugs(code, file_path)
        fixed_code = self.fix_bug(code, bug_analysis["analysis"], file_path)
        
        return {
            "agent": "bug_fixer",
            "task": task,
            "file_path": file_path,
            "bug_analysis": bug_analysis,
            "fixed_code": fixed_code,
            "status": "completed"
        }

