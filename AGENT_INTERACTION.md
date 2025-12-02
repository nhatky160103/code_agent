# Agent Interaction Flow

## Overview

The workflow relies on **LangGraph** to coordinate multiple AI agents. Each agent focuses on a single responsibility and updates a shared state so other agents can reuse its results.

## Agents and Responsibilities

1. **Code Reader**
   - Task: scan and summarize the repository
   - Output: structure overview, technology stack, file inventory
   - Shares with: every downstream agent (provides context)

2. **Bug Fixer**
   - Task: identify defects and produce patched code
   - Input: raw files or patched snippets from Code Reader
   - Output: bug analysis plus fixed code
   - Shares with: Tester (for validation) and PR Generator (for documentation)

3. **Refactorer**
   - Task: improve readability and organization without altering behavior
   - Input: code from Code Reader or Bug Fixer
   - Output: refactored code and a list of improvements
   - Shares with: Tester and PR Generator

4. **Tester**
   - Task: write pytest suites and optionally run them
   - Input: code/context from previous agents
   - Output: generated tests and (if requested) pytest results
   - Shares with: PR Generator

5. **PR Generator**
   - Task: create commit messages and PR descriptions
   - Input: accumulated changes (bug fixes, refactors, tests)
   - Output: ready-to-copy commit text and PR body

6. **Architect**
   - Task: suggest structure improvements and best practices
   - Input: codebase insights from Code Reader
   - Output: architecture recommendations that other agents may reference

## Workflow Diagram

```
+---------------------------------------------------------+
|                     Router Node                         |
|        (decides which agent should execute next)        |
+---------------------------------------------------------+
                         |
         +---------------+---------------+
         |               |               |
         v               v               v
    +---------+    +---------+    +---------+
    |  Code   |    |   Bug   |    | Refactor|
    | Reader  | -> |  Fixer  | -> |   er    |
    +---------+    +---------+    +---------+
         |               |               |
         |               |               |
         v               v               v
    +---------+    +---------+    +---------+
    | Tester  |    |    PR   |    |Architect|
    |         | -> |Generator|    |         |
    +---------+    +---------+    +---------+
```

## Shared State

Every agent receives and updates the same `AgentState` dictionary:

```python
{
    "task": "task description",
    "current_agent": "agent name",
    "results": {
        "code_reader": {...},
        "bug_fixer": {...},
        ...
    },
    "context": {
        "file_path": "...",
        "codebase_info": {...},
        ...
    },
    "completed_agents": ["code_reader", "bug_fixer"],
    "next_action": "tester"
}
```

## Example Flows

### Scenario 1 - Bug fixing and testing

1. Router -> Code Reader: gather context.
2. Code Reader -> State: store structure info.
3. Router -> Bug Fixer: patch code using the shared context.
4. Bug Fixer -> State: attach fixed code and bug notes.
5. Router -> Tester: generate tests using the patched code.
6. Tester -> State: add test code/results.
7. Router -> END: workflow exits.

### Scenario 2 - Full pipeline

1. Code Reader analyzes the repo.
2. Bug Fixer patches defects.
3. Refactorer improves structure.
4. Tester writes/runs tests.
5. PR Generator drafts documentation.
6. Architect suggests long-term improvements (optional branch).

## Communication Pattern

- **Shared state only** - agents never call each other directly.
- **Router-driven** - the router decides the next agent based on the task and which agents already ran.
- **Context propagation** - each agent enriches `context` so downstream agents do not need to repeat work.
- **Result aggregation** - the final response contains outputs from every agent that participated.

## Benefits

1. **Specialization** - each agent focuses on a narrow responsibility.
2. **Reusability** - downstream agents reuse upstream results.
3. **Easy to extend** - add a new node to the graph to introduce a new capability.
4. **Automation** - the router turns a natural-language instruction into an ordered workflow.
5. **Future parallelism** - independent agents can run in parallel with minimal changes.

