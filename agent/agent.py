import sys
import asyncio

try:
    from google.adk.agents import Agent
    from google.adk.runners import Runner
    from google.adk.sessions import InMemorySessionService
    from google.adk.tools.mcp_tool import McpToolset
    from google.adk.tools.mcp_tool.mcp_session_manager import StreamableHTTPConnectionParams
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
    class McpToolset:
        def __init__(self, connection_params=None, **kwargs):
            self.connection_params = connection_params
    class StreamableHTTPConnectionParams:
        def __init__(self, url=None, headers=None):
            self.url = url
            self.headers = headers or {}

from agent.config import (
    MODEL_NAME,
    WORKWEEK_MCP_URL,
    SERVICEIMMEDIATELY_MCP_URL,
    MCP_TOKEN,
)
from agent.prompt import (
    CONCIERGE_INSTRUCTION,
    WORKWEEK_SPECIALIST_INSTRUCTION,
    ITSM_SPECIALIST_INSTRUCTION,
)
from agent.tools import policy_search_tool
from agent.state import TurnState

# 1. Native FastMCP Toolsets (Streamable HTTP with X-MCP-Token)
workweek_mcp = McpToolset(
    connection_params=StreamableHTTPConnectionParams(
        url=WORKWEEK_MCP_URL,
        headers={"X-MCP-Token": MCP_TOKEN}
    )
)

serviceimmediately_mcp = McpToolset(
    connection_params=StreamableHTTPConnectionParams(
        url=SERVICEIMMEDIATELY_MCP_URL,
        headers={"X-MCP-Token": MCP_TOKEN}
    )
)

# 2. Specialist: WorkWeek Agent (Option 2: Autonomous Tool Access for Policy Validation + FastMCP)
workweek_specialist = Agent(
    name="workweek_specialist",
    model=MODEL_NAME,
    description="Specialist handling WorkWeek HCM operations: employee profile lookups, contact updates, leave balances, policy validation for time off, and leave bookings.",
    instruction=WORKWEEK_SPECIALIST_INSTRUCTION,
    tools=[workweek_mcp, policy_search_tool],
)

# 3. Specialist: ITSM Agent (Standard Conversational Sub-Agent)
itsm_specialist = Agent(
    name="itsm_specialist",
    model=MODEL_NAME,
    description="Specialist handling ServiceImmediately ITSM operations: ticket queries, incident creation, comments, and status transitions.",
    instruction=ITSM_SPECIALIST_INSTRUCTION,
    tools=[serviceimmediately_mcp],
)

# 4. Root Orchestrator: Main Concierge Agent
concierge_agent = Agent(
    name="concierge_agent",
    model=MODEL_NAME,
    description="Primary Enterprise HR & IT Concierge Assistant orchestrating policy Q&A, WorkWeek HCM operations, and ITSM service desk tickets.",
    instruction=CONCIERGE_INSTRUCTION,
    tools=[policy_search_tool],
    sub_agents=[workweek_specialist, itsm_specialist],
)

root_agent = concierge_agent

async def run_query(query: str, employee_id: str = "gunjangarg") -> str:
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
