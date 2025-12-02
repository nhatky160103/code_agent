"""LangGraph workflow for multi-agent code agent system"""
from typing import TypedDict, Literal
from langgraph.graph import StateGraph, END

from agents import (
    CodeReaderAgent,
    BugFixerAgent,
    RefactorerAgent,
    TesterAgent,
    PRGeneratorAgent,
    ArchitectAgent,
)
from openrouter_client import OpenRouterClient


class AgentState(TypedDict):
    """State shared between agents"""
    task: str
    current_agent: str
    results: dict
    context: dict
    next_action: str
    completed_agents: list


class CodeAgentWorkflow:
    """Main workflow orchestrator using LangGraph"""
    
    def __init__(self, api_key: str = None):
        self.client = OpenRouterClient(api_key)
        
        # Initialize all agents
        self.code_reader = CodeReaderAgent(self.client)
        self.bug_fixer = BugFixerAgent(self.client)
        self.refactorer = RefactorerAgent(self.client)
        self.tester = TesterAgent(self.client)
        self.pr_generator = PRGeneratorAgent(self.client)
        self.architect = ArchitectAgent(self.client)
        
        # Build workflow graph
        self.workflow = self._build_workflow()
    
    def _build_workflow(self) -> StateGraph:
        """Build LangGraph workflow"""
        workflow = StateGraph(AgentState)
        
        # Add nodes (agents)
        workflow.add_node("code_reader", self._code_reader_node)
        workflow.add_node("bug_fixer", self._bug_fixer_node)
        workflow.add_node("refactorer", self._refactorer_node)
        workflow.add_node("tester", self._tester_node)
        workflow.add_node("pr_generator", self._pr_generator_node)
        workflow.add_node("architect", self._architect_node)
        workflow.add_node("router", self._router_node)
        
        # Set entry point
        workflow.set_entry_point("router")
        
        # Define edges
        workflow.add_conditional_edges(
            "router",
            self._should_continue,
            {
                "code_reader": "code_reader",
                "bug_fixer": "bug_fixer",
                "refactorer": "refactorer",
                "tester": "tester",
                "pr_generator": "pr_generator",
                "architect": "architect",
                "end": END,
            }
        )
        
        # All agents route back to router
        workflow.add_edge("code_reader", "router")
        workflow.add_edge("bug_fixer", "router")
        workflow.add_edge("refactorer", "router")
        workflow.add_edge("tester", "router")
        workflow.add_edge("pr_generator", "router")
        workflow.add_edge("architect", "router")
        
        return workflow.compile()
    
    def _router_node(self, state: AgentState) -> AgentState:
        """Router node decides which agent to call next"""
        task = state.get("task", "")
        completed = state.get("completed_agents", [])
        results = state.get("results", {})
        
        # Determine next agent based on task and completed agents
        task_lower = task.lower()
        
        if "code_reader" not in completed and ("read" in task_lower or "analyze" in task_lower or "understand" in task_lower):
            return {**state, "current_agent": "code_reader", "next_action": "code_reader"}
        
        if "bug_fixer" not in completed and ("bug" in task_lower or "fix" in task_lower or "error" in task_lower):
            return {**state, "current_agent": "bug_fixer", "next_action": "bug_fixer"}
        
        if "refactorer" not in completed and ("refactor" in task_lower or "improve" in task_lower or "clean" in task_lower):
            return {**state, "current_agent": "refactorer", "next_action": "refactorer"}
        
        if "tester" not in completed and ("test" in task_lower or "testcase" in task_lower):
            return {**state, "current_agent": "tester", "next_action": "tester"}
        
        if "architect" not in completed and ("structure" in task_lower or "architecture" in task_lower or "suggest" in task_lower):
            return {**state, "current_agent": "architect", "next_action": "architect"}
        
        if "pr_generator" not in completed and ("pr" in task_lower or "pull request" in task_lower or "commit" in task_lower):
            return {**state, "current_agent": "pr_generator", "next_action": "pr_generator"}
        
        # Default: start with code reader if not done
        if "code_reader" not in completed:
            return {**state, "current_agent": "code_reader", "next_action": "code_reader"}
        
        # All done
        return {**state, "next_action": "end"}
    
    def _should_continue(self, state: AgentState) -> str:
        """Determine next step"""
        return state.get("next_action", "end")
    
    def _code_reader_node(self, state: AgentState) -> AgentState:
        """Code reader agent node"""
        task = state.get("task", "")
        context = state.get("context", {})
        results = state.get("results", {})
        completed = state.get("completed_agents", [])
        
        print(f"[Code Reader] Processing: {task}")
        result = self.code_reader.execute(task, context)
        
        results["code_reader"] = result
        if "code_reader" not in completed:
            completed.append("code_reader")
        
        # Update context with codebase info for other agents
        if "codebase_info" in result:
            context.update(result["codebase_info"])
        
        return {
            **state,
            "results": results,
            "context": context,
            "completed_agents": completed,
        }
    
    def _bug_fixer_node(self, state: AgentState) -> AgentState:
        """Bug fixer agent node"""
        task = state.get("task", "")
        context = state.get("context", {})
        results = state.get("results", {})
        completed = state.get("completed_agents", [])
        
        print(f"[Bug Fixer] Processing: {task}")
        
        # Get codebase info from code reader if available
        if "code_reader" in results:
            codebase_info = results["code_reader"].get("codebase_info", {})
            context.update(codebase_info)
        
        result = self.bug_fixer.execute(task, context)
        
        results["bug_fixer"] = result
        if "bug_fixer" not in completed:
            completed.append("bug_fixer")
        
        return {
            **state,
            "results": results,
            "context": context,
            "completed_agents": completed,
        }
    
    def _refactorer_node(self, state: AgentState) -> AgentState:
        """Refactorer agent node"""
        task = state.get("task", "")
        context = state.get("context", {})
        results = state.get("results", {})
        completed = state.get("completed_agents", [])
        
        print(f"[Refactorer] Processing: {task}")
        
        # Get info from previous agents
        if "code_reader" in results:
            codebase_info = results["code_reader"].get("codebase_info", {})
            context.update(codebase_info)
        
        result = self.refactorer.execute(task, context)
        
        results["refactorer"] = result
        if "refactorer" not in completed:
            completed.append("refactorer")
        
        return {
            **state,
            "results": results,
            "context": context,
            "completed_agents": completed,
        }
    
    def _tester_node(self, state: AgentState) -> AgentState:
        """Tester agent node"""
        task = state.get("task", "")
        context = state.get("context", {})
        results = state.get("results", {})
        completed = state.get("completed_agents", [])
        
        print(f"[Tester] Processing: {task}")
        
        # Get code info from other agents
        if "code_reader" in results:
            codebase_info = results["code_reader"].get("codebase_info", {})
            context.update(codebase_info)
        
        if "bug_fixer" in results:
            fixed_code = results["bug_fixer"].get("fixed_code", "")
            if fixed_code:
                context["code"] = fixed_code
        
        result = self.tester.execute(task, context)
        
        results["tester"] = result
        if "tester" not in completed:
            completed.append("tester")
        
        return {
            **state,
            "results": results,
            "context": context,
            "completed_agents": completed,
        }
    
    def _pr_generator_node(self, state: AgentState) -> AgentState:
        """PR generator agent node"""
        task = state.get("task", "")
        context = state.get("context", {})
        results = state.get("results", {})
        completed = state.get("completed_agents", [])
        
        print(f"[PR Generator] Processing: {task}")
        
        # Collect all changes from other agents
        changes = {}
        commits = []
        
        if "bug_fixer" in results:
            changes["bug_fixes"] = results["bug_fixer"].get("bug_analysis", {})
        
        if "refactorer" in results:
            changes["refactoring"] = results["refactorer"].get("result", {})
        
        if "tester" in results:
            changes["tests"] = results["tester"].get("test_code", "")
        
        context["changes"] = changes
        context["commits"] = commits
        
        result = self.pr_generator.execute(task, context)
        
        results["pr_generator"] = result
        if "pr_generator" not in completed:
            completed.append("pr_generator")
        
        return {
            **state,
            "results": results,
            "context": context,
            "completed_agents": completed,
        }
    
    def _architect_node(self, state: AgentState) -> AgentState:
        """Architect agent node"""
        task = state.get("task", "")
        context = state.get("context", {})
        results = state.get("results", {})
        completed = state.get("completed_agents", [])
        
        print(f"[Architect] Processing: {task}")
        
        # Get codebase info
        if "code_reader" in results:
            codebase_info = results["code_reader"].get("codebase_info", {})
            context.update(codebase_info)
        
        result = self.architect.execute(task, context)
        
        results["architect"] = result
        if "architect" not in completed:
            completed.append("architect")
        
        return {
            **state,
            "results": results,
            "context": context,
            "completed_agents": completed,
        }
    
    def run(self, task: str, initial_context: dict = None) -> dict:
        """Run the workflow with a task"""
        initial_state: AgentState = {
            "task": task,
            "current_agent": "",
            "results": {},
            "context": initial_context or {},
            "next_action": "",
            "completed_agents": [],
        }
        
        print(f"\nStarting Code Agent workflow for task: {task}\n")
        
        # Run the workflow
        final_state = self.workflow.invoke(initial_state)
        
        print(f"\nWorkflow completed successfully.\n")
        print(f"Completed agents: {final_state.get('completed_agents', [])}\n")
        
        return final_state

