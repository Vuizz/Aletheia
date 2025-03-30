🧱 Aletheia — Financial Reasoning Agent Framework
“Aletheia” (Ancient Greek: ἀλήθεια) means truth or disclosure. This system is built to reveal structured, data-backed insights about financial markets.

🧠 Project Overview
Aletheia is a multi-agent GPT-powered reasoning system for real-time analysis of financial news and macro events. It extracts structured events from raw articles, enriches them with contextual data, and incrementally builds an interpretable belief state. This enables human-readable forecasting, scenario modeling, and asset-level impact detection.

Key Features:

Modular agent-based architecture

Stepwise reasoning over structured memory

Event-to-impact pipelines (narratives, tickers, scenarios)

Composable and explainable logic

Lightweight JSON-based memory storage

aletheia/
│
├── core/               # Central system architecture
│   ├── orchestrator.py        # Agent loop controller
│   ├── state_manager.py       # Belief state I/O
│   └── task_router.py         # Task delegation engine
│
├── agents/            # Core logic agents
│   ├── event_parser.py              # Parses news into structured events
│   ├── entity_expander.py           # Identifies actors, sectors, regions, themes
│   ├── event_grounder.py            # Gathers factual data/statistics/context
│   ├── asset_impact_mapper.py       # Maps events to ticker symbols + impact
│   └── ... (future agents)
│
├── prompts/           # System prompts (modular and agent-specific)
│   └── [agent_name].txt
│
├── memory/            # Persistent shared state
│   ├── belief_state.json             # Current system memory
│   └── versions/                     # Historical snapshots
│
├── interface/         # User interaction (CLI / notebook)
│   └── run_agent.py
│
├── utils/             # Shared helpers
│   ├── logging_utils.py
│   ├── json_repair.py
│   └── ...
│
├── validators/        # Optional validators / QA modules
│
└── data/              # Raw or processed financial input


🧠 Active Agents
Agent Name	Purpose
EventParserAgent	Converts raw news into clean, typed financial events
EntityExpanderAgent	Detects key actors, sectors, regions, and themes
EventGroundingAgent	Enriches events with statistics and economic context
AssetImpactMapperAgent	Maps grounded events to affected assets and forecasts their direction


⚙️ Usage
You can run the system manually using the orchestrator:
python run.py
Agents work incrementally: each builds upon the output of the previous. Intermediate outputs are stored in memory/belief_state.json.

You can also test agents individually via their AgentRunner class.

📜 Philosophy
“The goal is not to predict markets perfectly.
It’s to reason through them better, step by step.”

Aletheia is about clarity, modularity, and trust — not black-box prediction.