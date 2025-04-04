import json
import logging
import asyncio
from core.state_manager import load_state, save_state
from agents.event_parser import EventParserAgent
from agents.entity_expander import EntityExpanderAgent
from agents.event_grounding import EventGroundingAgent
from agents.search_planner import SearchPlannerAgent
from agents.webcontent_analyzer import WebContentAnalyzerAgent
from agents.event_brancher import EventBrancherAgent
from agents.position_evaluator import PositionEvaluatorAgent
from agents.position_planner import PositionPlannerAgent

import time


async def run_analysis(user_input):
    logging.info("--- New Session Started ---")
    state = load_state()
    summaries = []

    # Step 1: Parse events
    start = time.time()
    event_agent = EventParserAgent()
    state = await event_agent.run(state, user_input)
    summaries.append(event_agent.summary)
    logging.info(
        "========== [Agent Completed] EventParserAgent finished in %.2f seconds ==========", (time.time()-start))

    # Step 2: Expand events
    start = time.time()
    expander_agent = EntityExpanderAgent()
    state = await expander_agent.run(state, user_input)
    summaries.append(expander_agent.summary)
    logging.info(
        "========== [Agent Completed] EntityExpanderAgent finished in %.2f seconds ==========", (time.time()-start))

    # Step 3: Ground events
    start = time.time()
    grounding_agent = EventGroundingAgent()
    state = await grounding_agent.run(state, user_input)
    summaries.append(grounding_agent.summary)
    logging.info(
        "========== [Agent Completed] EventGroundingAgent finished in %.2f seconds ==========", (time.time()-start))

    # Step 4: Branch events
    start = time.time()
    brancher_agent = EventBrancherAgent()
    state = await brancher_agent.run(state, user_input)
    summaries.append(brancher_agent.summary)
    logging.info(
        "========== [Agent Completed] EventBrancherAgent finished in %.2f seconds ==========", (time.time()-start))

    # Step 5: Questioning events
    start = time.time()
    question_agent = SearchPlannerAgent()
    state = await question_agent.run(state, user_input)
    summaries.append(question_agent.summary)
    logging.info(
        "========== [Agent Completed] SearchPlannerAgent finished in %.2f seconds ==========", (time.time()-start))

    # Step 6: Websearching events
    start = time.time()
    websearch_agent = WebContentAnalyzerAgent()
    state = await websearch_agent.run(state, user_input)
    summaries.append(websearch_agent.summary)
    logging.info(
        "========== [Agent Completed] WebContentAnalyzerAgent finished in %.2f seconds ==========", (time.time()-start))

    # # Step 7: Evaluating positions
    start = time.time()
    evaluator_agent = PositionEvaluatorAgent()
    state = await evaluator_agent.run(state, user_input)
    summaries.append(evaluator_agent.summary)
    logging.info(
        "========== [Agent Completed] PositionEvaluatorAgent finished in %.2f seconds ==========", (time.time()-start))

    # Step 8: Planning positions
    start = time.time()
    planner_agent = PositionPlannerAgent()
    state = await planner_agent.run(state, user_input)
    summaries.append(planner_agent.summary)
    logging.info(
        "========== [Agent Completed] PositionPlannerAgent finished in %.2f seconds ==========", (time.time()-start))

    # Save updated state (versioned)
    save_state(state)
    logging.info("Session complete. Belief state updated.")

    # ✅ Print user-friendly highlights only
    print("\n📋 Agent Run Summary:")
    for summary in summaries:
        print("-", summary)

    return state
