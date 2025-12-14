```
state: 
    task: 
    current_state
    results: 
        planner:
            agent
            task
            plan_markdown
            status
        coder:
            agent
            task
            files_written
            files_failed
            status
        code_reader:
            agent
            task
            analysis
            codebase_info:
                total_files
                files
            status
    context: 
        requirements_text
        plan_markdown
        coder_failed
        total_files # from codebase info
        files # from codebase info
     
    next_action
    completed_agents
    test_status
    test_attempts
```