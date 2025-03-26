🧱 Aletheia: Core Project Foundations (v1.0)
🧠 Vision Summary
Aletheia is a modular, GPT-powered financial reasoning agent that analyzes markets using composable agent logic, structured memory, and multi-step causal inference. The foundation layer should support:

Multi-agent orchestration

State memory (belief system)

Incremental analysis building

Reusability & transparency of reasoning

Plug-in structure for future agents

🧱 1. Project Structure (Block-Based)

aletheia/
│
├── core/               # Central logic layer
│   ├── orchestrator.py        # Runs the agent loop
│   ├── state_manager.py       # Loads, updates, stores belief state
│   └── task_router.py         # Sends tasks to the correct agent(s)
│
├── agents/            # Modular agents (GPT roles)
│   ├── event_parser.py
│   ├── narrative_tracker.py
│   ├── causal_reasoner.py
│   ├── flow_estimator.py
│   ├── scenario_forecaster.py
│   ├── report_composer.py
│   └── ...
│
├── prompts/           # System prompts + templates
│   └── [agent_name].txt
│
├── memory/            # Agent memory (could be JSON or vector DB)
│   └── belief_state.json
│
├── interface/         # CLI, notebook, or API input/output
│   └── run_agent.py
│
├── data/              # External data (feeds, saved articles, etc.)
│
└── utils/             # Common helpers (API wrappers, logging)

TODO:
- Change Scenarios Agent to generate scenarios based on current narratives (ONGOING)
- Improve prompt tuner (ONGOING)
- Introduce info filtering before running its through the model ( A new agent that fitlters information to define if its relevant or not )
- Introduce new agents to complement analysis on narratives, gather more data about certain subjects
- Later Introduce new agents to Define market positions based on beleif state
- Introduce market position tracker, manager
