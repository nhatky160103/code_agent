"""Architect Agent - Suggests project structure and best practices"""
from typing import Dict, Any
from agents.base_agent import BaseAgent
from agents.code_reader import CodeReaderAgent


class ArchitectAgent(BaseAgent):
    """Agent specialized in suggesting project structure and architecture"""
    
    def __init__(self, client=None):
        super().__init__("architect", client)
        self.code_reader = CodeReaderAgent(client)
    
    def suggest_structure(self, current_structure: Dict[str, Any] = None) -> Dict[str, Any]:
        """Suggest improved project structure"""
        prompt = f"""
Based on the current project structure:

{self._format_structure(current_structure) if current_structure else 'No structure provided'}

Please suggest:
1. Improved directory structure
2. File organization best practices
3. Naming conventions
4. Module/package structure
5. Configuration management
6. Documentation structure

Provide specific recommendations with explanations.
"""
        
        suggestions = self._call_llm(prompt)
        return {"suggestions": suggestions}
    
    def suggest_best_practices(self, codebase_info: Dict[str, Any]) -> Dict[str, Any]:
        """Suggest best practices for the codebase"""
        prompt = f"""
Analyze the codebase and suggest best practices:

Codebase Info:
- Total files: {codebase_info.get('total_files', 0)}
- Technologies: {codebase_info.get('technologies', 'Unknown')}
- Structure: {codebase_info.get('structure', 'Unknown')}

Please suggest:
1. Code organization improvements
2. Design patterns to apply
3. Testing strategies
4. Documentation improvements
5. CI/CD recommendations
6. Security best practices
"""
        
        practices = self._call_llm(prompt)
        return {"best_practices": practices}
    
    def _format_structure(self, structure: Dict[str, Any]) -> str:
        """Format structure for display"""
        # Simple formatting
        return str(structure)
    
    def execute(self, task: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Execute architecture suggestion task"""
        if context is None:
            context = {}
        # Fallback nếu code_reader lỗi hoặc không trả về đầy đủ trường
        try:
            analysis = self.code_reader.analyze_codebase()
            total_files = analysis.get("total_files", 0)
            files = analysis.get("files", [])
        except Exception as e:
            print(f"[Architect] Error running code_reader: {e}")
            total_files = 0
            files = []
        if not isinstance(files, list):
            print(f"[Architect] code_reader files is not a list, value: {files}")
            files = []
        structure_info = {
            "total_files": total_files,
            "files": files,
            "structure": "Analyzed from codebase"
        }
        suggestions = self.suggest_structure(structure_info)
        best_practices = self.suggest_best_practices(structure_info)
        return {
            "agent": "architect",
            "task": task,
            "structure_suggestions": suggestions,
            "best_practices": best_practices,
            "status": "completed"
        }

