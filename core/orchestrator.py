import json
import logging
import asyncio
from core.state_manager import load_state, save_state
from agents.event_parser import EventParserAgent
from agents.narrative_tracker import NarrativeTrackerAgent
from agents.causal_reasoner import CausalReasonerAgent
from agents.scenario_forecaster import ScenarioForecasterAgent
from agents.report_composer import ReportComposerAgent
from agents.ticker_linker import TickerLinkerAgent
from agents.meta_evaluator import MetaEvaluatorAgent

async def run_analysis(user_input):
    logging.info("--- New Session Started ---")
    state = load_state()
    summaries = []

    # Step 1: Parse events
    event_agent = EventParserAgent()
    state = await event_agent.run(state, user_input)
    summaries.append(event_agent.summary)

    # Step 1.5 - 3: Run independent agents concurrently (Ticker, Narrative, Causal)
    ticker_agent = TickerLinkerAgent()
    narrative_agent = NarrativeTrackerAgent()
    causal_agent = CausalReasonerAgent()

    ticker_task = asyncio.create_task(ticker_agent.run(state))
    narrative_task = asyncio.create_task(narrative_agent.run(state))
    causal_task = asyncio.create_task(causal_agent.run(state))

    # Await them all together
    ticker_result, narrative_result, causal_result = await asyncio.gather(
        ticker_task, narrative_task, causal_task
    )

    # Merge states and collect summaries
    for agent, result in zip(
        [ticker_agent, narrative_agent, causal_agent],
        [ticker_result, narrative_result, causal_result]
    ):
        state.update(result)
        summaries.append(agent.summary)

    # Step 4: Forecast scenarios
    scenario_agent = ScenarioForecasterAgent()
    state = await scenario_agent.run(state)
    summaries.append(scenario_agent.summary)

    # Step 5: Generate final report
    report_agent = ReportComposerAgent()
    state = await report_agent.run(state)
    summaries.append(report_agent.summary)

    # Step 6: Evaluate analysis quality
    evaluator = MetaEvaluatorAgent()
    state = await evaluator.run(state)

    # Save updated state (versioned)
    save_state(state)
    logging.info("Session complete. Belief state updated.")

    # ✅ Print user-friendly highlights only
    print("\n📋 Agent Run Summary:")
    for summary in summaries:
        print("-", summary)

    print("\n🧠 Key Narratives:")
    for n in state.get("active_narratives", []):
        print(f"- [{n['status'].upper()}] {n['narrative']} (strength={n['strength']})")

    print("\n🔮 Scenario Forecasts:")
    for s in state.get("scenarios", []):
        print(f"- {s['label'].title()}: {s['summary']} ({int(s['probability'] * 100)}%)")

    print("\n📝 Final Report Summary:")
    print(state.get("report", "No report generated.").split("\n\n")[0])

    return state
