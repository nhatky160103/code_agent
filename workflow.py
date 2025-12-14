"""LangGraph workflow for multi-agent code agent system"""
import time
from typing import TypedDict
from langgraph.graph import StateGraph, END

from agents import (
    CodeReaderAgent,
    BugFixerAgent,
    RefactorerAgent,
    PRGeneratorAgent,
    ArchitectAgent,
    RequirementsPlannerAgent,
    CoderAgent,
)
from openrouter_client import get_default_client
from utils.logging import get_logger, get_metrics


class AgentState(TypedDict):
    task: str
    current_agent: str
    results: dict
    context: dict
    next_action: str
    completed_agents: list


logger = get_logger("code_agent.workflow")
metrics = get_metrics()


class CodeAgentWorkflow:
    """Main workflow orchestrator using LangGraph (no tester version)"""

    def __init__(self, api_key: str = None):
        self.client = get_default_client(api_key)

        # Initialize agents (đã bỏ TesterAgent)
        self.planner = RequirementsPlannerAgent(self.client)
        self.coder = CoderAgent(self.client)
        self.code_reader = CodeReaderAgent(self.client)
        self.bug_fixer = BugFixerAgent(self.client)
        self.refactorer = RefactorerAgent(self.client)
        self.pr_generator = PRGeneratorAgent(self.client)
        self.architect = ArchitectAgent(self.client)

        self.workflow = self._build_workflow()

    def _build_workflow(self) -> StateGraph:
        workflow = StateGraph(AgentState)

        workflow.add_node("planner", self._planner_node)
        workflow.add_node("coder", self._coder_node)
        workflow.add_node("code_reader", self._code_reader_node)
        workflow.add_node("bug_fixer", self._bug_fixer_node)
        workflow.add_node("refactorer", self._refactorer_node)
        workflow.add_node("pr_generator", self._pr_generator_node)
        workflow.add_node("architect", self._architect_node)
        workflow.add_node("router", self._router_node)

        workflow.set_entry_point("router")

        workflow.add_conditional_edges(
            "router",
            self._should_continue,
            {
                "planner": "planner",
                "coder": "coder",
                "code_reader": "code_reader",
                "bug_fixer": "bug_fixer",
                "refactorer": "refactorer",
                "pr_generator": "pr_generator",
                "architect": "architect",
                "end": END,
            }
        )

        for agent in ["planner", "coder", "code_reader", "bug_fixer", "refactorer", "pr_generator", "architect"]:
            workflow.add_edge(agent, "router")

        return workflow.compile()

    # -----------------------------
    # Router
    # -----------------------------
    def _router_node(self, state: AgentState) -> AgentState:
        task = state.get("task", "")
        completed = state.get("completed_agents", [])
        context = state.get("context", {})

        task_lower = task.lower()

        # Auto-flow (no tester)
        if any(w in task_lower for w in ["build", "create", "app", "feature"]):
            order = ["planner", "coder", "code_reader", "bug_fixer", "pr_generator", "architect"]
            for agent in order:
                if agent not in completed:
                    return {**state, "current_agent": agent, "next_action": agent}
            return {**state, "next_action": "end"}

        # Keyword routing
        if "read" in task_lower or "analyze" in task_lower:
            if "code_reader" not in completed:
                return {**state, "current_agent": "code_reader", "next_action": "code_reader"}

        if any(k in task_lower for k in ["bug", "fix"]):
            if "bug_fixer" not in completed:
                return {**state, "current_agent": "bug_fixer", "next_action": "bug_fixer"}

        if any(k in task_lower for k in ["refactor", "improve"]):
            if "refactorer" not in completed:
                return {**state, "current_agent": "refactorer", "next_action": "refactorer"}

        if any(k in task_lower for k in ["architecture", "structure"]):
            if "architect" not in completed:
                return {**state, "current_agent": "architect", "next_action": "architect"}

        if "pr" in task_lower:
            if "pr_generator" not in completed:
                return {**state, "current_agent": "pr_generator", "next_action": "pr_generator"}

        # Default
        if "code_reader" not in completed:
            return {**state, "current_agent": "code_reader", "next_action": "code_reader"}

        return {**state, "next_action": "end"}

    def _should_continue(self, state: AgentState) -> str:
        return state.get("next_action", "end")

    def _with_retry(self, agent_fn, agent_name: str, state: AgentState, max_retries=3):
        """Generic retry wrapper for agent node execution."""
        last_exc = None
        for attempt in range(1, max_retries+1):
            try:
                return agent_fn(state)
            except Exception as exc:
                print(f"[{agent_name}] Retry {attempt} failed: {exc}")
                last_exc = exc
        # Nếu vẫn fail sau max_retries lần
        results = state["results"]
        results[agent_name] = {"error": str(last_exc)}
        return {**state, "results": results}

    # -----------------------------
    # AGENT NODES
    # -----------------------------
    def _planner_node(self, state: AgentState) -> AgentState:
        def call_fn(s):
            start_time = time.time()
            task = s["task"]
            context = s["context"]
            results = s["results"]
            completed = s["completed_agents"]
            
            logger.info("agent_started", agent="planner", task=task)
            metrics["agent_executions_total"].labels(agent="planner", status="started").inc()
            
            try:
                result = self.planner.execute(task, context)
                results["planner"] = result
                context["plan_markdown"] = result.get("plan_markdown", "")
                completed.append("planner")
                
                duration = time.time() - start_time
                metrics["agent_execution_duration"].labels(agent="planner").observe(duration)
                metrics["agent_executions_total"].labels(agent="planner", status="success").inc()
                logger.info("agent_completed", agent="planner", duration=duration)
                
                return {**s, "results": results, "context": context, "completed_agents": completed}
            except Exception as e:
                duration = time.time() - start_time
                metrics["agent_executions_total"].labels(agent="planner", status="error").inc()
                logger.error("agent_failed", agent="planner", duration=duration, error=str(e))
                raise
        return self._with_retry(call_fn, "planner", state)

    def _coder_node(self, state: AgentState) -> AgentState:
        def call_fn(s):
            start_time = time.time()
            task = s["task"]
            context = s["context"]
            results = s["results"]
            completed = s["completed_agents"]
            
            logger.info("agent_started", agent="coder", task=task)
            metrics["agent_executions_total"].labels(agent="coder", status="started").inc()
            
            try:
                result = self.coder.execute(task, context)
                results["coder"] = result
                completed.append("coder")
                
                duration = time.time() - start_time
                metrics["agent_execution_duration"].labels(agent="coder").observe(duration)
                metrics["agent_executions_total"].labels(agent="coder", status="success").inc()
                logger.info("agent_completed", agent="coder", duration=duration)
                
                return {**s, "results": results, "context": context, "completed_agents": completed}
            except Exception as e:
                duration = time.time() - start_time
                metrics["agent_executions_total"].labels(agent="coder", status="error").inc()
                logger.error("agent_failed", agent="coder", duration=duration, error=str(e))
                raise
        return self._with_retry(call_fn, "coder", state)

    def _code_reader_node(self, state: AgentState) -> AgentState:
        def call_fn(s):
            start_time = time.time()
            task = s["task"]
            context = s["context"]
            results = s["results"]
            completed = s["completed_agents"]
            
            logger.info("agent_started", agent="code_reader", task=task)
            metrics["agent_executions_total"].labels(agent="code_reader", status="started").inc()
            
            try:
                result = self.code_reader.execute(task, context)
                results["code_reader"] = result
                info = result.get("codebase_info", {})
                context.update(info)
                completed.append("code_reader")
                
                duration = time.time() - start_time
                metrics["agent_execution_duration"].labels(agent="code_reader").observe(duration)
                metrics["agent_executions_total"].labels(agent="code_reader", status="success").inc()
                logger.info("agent_completed", agent="code_reader", duration=duration)
                
                return {**s, "results": results, "context": context, "completed_agents": completed}
            except Exception as e:
                duration = time.time() - start_time
                metrics["agent_executions_total"].labels(agent="code_reader", status="error").inc()
                logger.error("agent_failed", agent="code_reader", duration=duration, error=str(e))
                raise
        return self._with_retry(call_fn, "code_reader", state)

    def _bug_fixer_node(self, state: AgentState) -> AgentState:
        def call_fn(s):
            start_time = time.time()
            task = s["task"]
            context = s["context"]
            results = s["results"]
            completed = s["completed_agents"]
            
            logger.info("agent_started", agent="bug_fixer", task=task)
            metrics["agent_executions_total"].labels(agent="bug_fixer", status="started").inc()
            
            try:
                result = self.bug_fixer.execute(task, context)
                results["bug_fixer"] = result
                completed.append("bug_fixer")
                
                duration = time.time() - start_time
                metrics["agent_execution_duration"].labels(agent="bug_fixer").observe(duration)
                metrics["agent_executions_total"].labels(agent="bug_fixer", status="success").inc()
                logger.info("agent_completed", agent="bug_fixer", duration=duration)
                
                return {**s, "results": results, "context": context, "completed_agents": completed}
            except Exception as e:
                duration = time.time() - start_time
                metrics["agent_executions_total"].labels(agent="bug_fixer", status="error").inc()
                logger.error("agent_failed", agent="bug_fixer", duration=duration, error=str(e))
                raise
        return self._with_retry(call_fn, "bug_fixer", state)

    def _refactorer_node(self, state: AgentState) -> AgentState:
        def call_fn(s):
            start_time = time.time()
            task = s["task"]
            context = s["context"]
            results = s["results"]
            completed = s["completed_agents"]
            
            logger.info("agent_started", agent="refactorer", task=task)
            metrics["agent_executions_total"].labels(agent="refactorer", status="started").inc()
            
            try:
                result = self.refactorer.execute(task, context)
                results["refactorer"] = result
                completed.append("refactorer")
                
                duration = time.time() - start_time
                metrics["agent_execution_duration"].labels(agent="refactorer").observe(duration)
                metrics["agent_executions_total"].labels(agent="refactorer", status="success").inc()
                logger.info("agent_completed", agent="refactorer", duration=duration)
                
                return {**s, "results": results, "context": context, "completed_agents": completed}
            except Exception as e:
                duration = time.time() - start_time
                metrics["agent_executions_total"].labels(agent="refactorer", status="error").inc()
                logger.error("agent_failed", agent="refactorer", duration=duration, error=str(e))
                raise
        return self._with_retry(call_fn, "refactorer", state)

    def _pr_generator_node(self, state: AgentState) -> AgentState:
        def call_fn(s):
            start_time = time.time()
            task = s["task"]
            context = s["context"]
            results = s["results"]
            completed = s["completed_agents"]
            
            logger.info("agent_started", agent="pr_generator", task=task)
            metrics["agent_executions_total"].labels(agent="pr_generator", status="started").inc()
            
            try:
                result = self.pr_generator.execute(task, context)
                results["pr_generator"] = result
                completed.append("pr_generator")
                
                duration = time.time() - start_time
                metrics["agent_execution_duration"].labels(agent="pr_generator").observe(duration)
                metrics["agent_executions_total"].labels(agent="pr_generator", status="success").inc()
                logger.info("agent_completed", agent="pr_generator", duration=duration)
                
                return {**s, "results": results, "context": context, "completed_agents": completed}
            except Exception as e:
                duration = time.time() - start_time
                metrics["agent_executions_total"].labels(agent="pr_generator", status="error").inc()
                logger.error("agent_failed", agent="pr_generator", duration=duration, error=str(e))
                raise
        return self._with_retry(call_fn, "pr_generator", state)

    def _architect_node(self, state: AgentState) -> AgentState:
        def call_fn(s):
            start_time = time.time()
            task = s["task"]
            context = s["context"]
            results = s["results"]
            completed = s["completed_agents"]
            
            logger.info("agent_started", agent="architect", task=task)
            metrics["agent_executions_total"].labels(agent="architect", status="started").inc()
            
            try:
                result = self.architect.execute(task, context)
                results["architect"] = result
                completed.append("architect")
                
                duration = time.time() - start_time
                metrics["agent_execution_duration"].labels(agent="architect").observe(duration)
                metrics["agent_executions_total"].labels(agent="architect", status="success").inc()
                logger.info("agent_completed", agent="architect", duration=duration)
                
                return {**s, "results": results, "context": context, "completed_agents": completed}
            except Exception as e:
                duration = time.time() - start_time
                metrics["agent_executions_total"].labels(agent="architect", status="error").inc()
                logger.error("agent_failed", agent="architect", duration=duration, error=str(e))
                raise
        return self._with_retry(call_fn, "architect", state)

    # ============================================================
    # RUN METHOD
    # ============================================================
    def run(self, task: str, initial_context: dict = None) -> dict:
        """Run the workflow with a task"""
        start_time = time.time()
        workflow_id = f"workflow_{int(time.time())}"
        
        initial_state: AgentState = {
            "task": task,
            "current_agent": "",
            "results": {},
            "context": initial_context or {},
            "next_action": "",
            "completed_agents": [],
        }

        logger.info(
            "workflow_started",
            workflow_id=workflow_id,
            task=task,
            context_keys=list(initial_context.keys()) if initial_context else []
        )
        metrics["workflow_total"].labels(status="started").inc()
        metrics["active_workflows"].inc()

        try:
            final_state = self.workflow.invoke(initial_state)
            duration = time.time() - start_time
            
            completed_agents = final_state.get("completed_agents", [])
            
            logger.info(
                "workflow_completed",
                workflow_id=workflow_id,
                duration=duration,
                completed_agents=completed_agents,
                results_keys=list(final_state.get("results", {}).keys())
            )
            metrics["workflow_duration"].labels(status="success").observe(duration)
            metrics["workflow_total"].labels(status="success").inc()
            metrics["active_workflows"].dec()
            
            print(f"\n{'='*60}")
            print(f"✅ Workflow Completed Successfully")
            print(f"{'='*60}")
            print(f"Duration: {duration:.2f}s")
            print(f"Agents run: {completed_agents}")

        except Exception as e:
            duration = time.time() - start_time
            
            logger.error(
                "workflow_failed",
                workflow_id=workflow_id,
                duration=duration,
                error=str(e),
                error_type=type(e).__name__,
                exc_info=True
            )
            metrics["workflow_duration"].labels(status="error").observe(duration)
            metrics["workflow_total"].labels(status="error").inc()
            metrics["active_workflows"].dec()
            
            print(f"\n{'='*60}")
            print(f"❌ Workflow Failed")
            print(f"{'='*60}")
            print(f"Error: {e}")
            import traceback
            traceback.print_exc()

        return final_state


# ============================================================
# GRAPH EXPORT (như code gốc)
# ============================================================
if __name__ == "__main__":
    workflow = CodeAgentWorkflow()
    workflow_graph = workflow._build_workflow()
    mermaid = workflow_graph.get_graph(xray=True).draw_mermaid()

    output_path = "workflow_graph.md"
    with open(output_path, "w", encoding="utf-8") as f:
        f.write("```mermaid\n")
        f.write(mermaid)
        f.write("\n```")

    print(f"Graph đã được lưu vào: {output_path}")
