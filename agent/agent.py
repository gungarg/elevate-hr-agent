import sys
import asyncio

try:
    from google.adk.agents import Agent
    from google.adk.runners import Runner
    from google.adk.sessions import InMemorySessionService
except ImportError:
    class Agent:
        def __init__(self, **kwargs):
            for k, v in kwargs.items():
                setattr(self, k, v)
    class Runner:
        def __init__(self, **kwargs):
            pass
    class InMemorySessionService:
        def __init__(self, **kwargs):
            pass

from agent.config import MODEL_NAME
from agent.prompt import (
    CONCIERGE_INSTRUCTION,
    WORKWEEK_SPECIALIST_INSTRUCTION,
    ITSM_SPECIALIST_INSTRUCTION,
)
from agent.schemas import WorkWeekTaskOutput, ITSMTaskOutput
from agent.tools.okf_tool import list_concepts_tool, read_concept_tool
from agent.tools.workweek_tool import workweek_tools
from agent.tools.itsm_tool import itsm_tools
from agent.state import TurnState

# 1. Specialist: WorkWeek Agent (mode='task')
workweek_specialist = Agent(
    name="workweek_specialist",
    model=MODEL_NAME,
    mode="task",
    output_schema=WorkWeekTaskOutput,
    description="Handles WorkWeek HCM operations: employee profile lookups, contact updates, leave balances, booking and canceling leave.",
    instruction=WORKWEEK_SPECIALIST_INSTRUCTION,
    tools=workweek_tools + [list_concepts_tool, read_concept_tool],
)

# 2. Specialist: ITSM Agent (mode='task')
itsm_specialist = Agent(
    name="itsm_specialist",
    model=MODEL_NAME,
    mode="task",
    output_schema=ITSMTaskOutput,
    description="Handles ServiceImmediately ITSM operations: ticket queries, incident creation, comments, and lifecycle status updates.",
    instruction=ITSM_SPECIALIST_INSTRUCTION,
    tools=itsm_tools,
)

# 3. Root Orchestrator: Concierge Agent
concierge_agent = Agent(
    name="concierge_agent",
    model=MODEL_NAME,
    description="Primary Enterprise HR & IT Concierge Assistant orchestrating policy Q&A, WorkWeek HCM operations, and ITSM service desk tickets.",
    instruction=CONCIERGE_INSTRUCTION,
    tools=[list_concepts_tool, read_concept_tool],
    sub_agents=[workweek_specialist, itsm_specialist],
)

root_agent = concierge_agent

async def run_query(query: str, employee_id: str = "EMP1024") -> str:
    """Executes a query against the HR multi-agent runner."""
    session_service = InMemorySessionService()
    session = await session_service.create_session(session_id=f"session_{employee_id}")
    
    turn_state = TurnState(employee_id=employee_id)
    session.state["auth_context"] = turn_state.auth_context
    session.state["turn_cache"] = turn_state.turn_cache
    
    runner = Runner(agent=root_agent, session_service=session_service)
    
    response_text = ""
    async for event in runner.run_async(session_id=session.session_id, user_message=query):
        if hasattr(event, "content") and event.content:
            response_text += event.content
        elif hasattr(event, "text") and event.text:
            response_text += event.text
            
    return response_text or "No response received."

def main():
    if len(sys.argv) > 1:
        query = " ".join(sys.argv[1:])
        print(f"\n[USER QUERY]: {query}")
        result = asyncio.run(run_query(query))
        print(f"\n[ASSISTANT RESPONSE]:\n{result}")
    else:
        print("Altostrat HR Multi-Agent Assistant CLI (ADK 2.0)")
        print("Type 'exit' or 'quit' to end session.\n")
        while True:
            try:
                user_input = input("You > ").strip()
                if user_input.lower() in ["exit", "quit"]:
                    break
                if not user_input:
                    continue
                result = asyncio.run(run_query(user_input))
                print(f"\nAssistant >\n{result}\n")
            except (KeyboardInterrupt, EOFError):
                break

if __name__ == "__main__":
    main()
