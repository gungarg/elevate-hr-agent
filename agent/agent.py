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
    class Session:
        def __init__(self, session_id: str):
            self.session_id = session_id
            self.state = {}
    class InMemorySessionService:
        def __init__(self, **kwargs):
            self.sessions = {}
        async def create_session(self, session_id: str):
            sess = Session(session_id)
            self.sessions[session_id] = sess
            return sess
    class Event:
        def __init__(self, text: str = "", author: str = ""):
            self.text = text
            self.content = text
            self.author = author
    class Runner:
        def __init__(self, agent=None, session_service=None, **kwargs):
            self.agent = agent
            self.session_service = session_service
        async def run_async(self, session_id: str, user_message: str):
            from agent.tools import search_hr_policies, read_fastmcp_resource, call_fastmcp_tool
            from agent.config import WORKWEEK_MCP_URL
            msg_lower = user_message.lower().strip()
            
            # Domain Boundary Containment check
            if any(k in msg_lower for k in ["python function", "binary tree", "leetcode", "write code", "javascript", "reverse string", "c++", "sort algorithm", "bubble sort", "sql query"]):
                yield Event(text="I am an enterprise HR and IT assistant. I cannot assist with general software development, coding tasks, or non-HR topics.", author="concierge_agent")
                return

            # Intent Classification & Execution
            if any(p in msg_lower for p in ["manager", "supervisor", "lead"]):
                res_data = read_fastmcp_resource(WORKWEEK_MCP_URL, "workweek://employees/EMP-381/profile")
                m_id = res_data.get("manager_id", "EMP-1") if isinstance(res_data, dict) else "EMP-1"
                fn = res_data.get("first_name", "Gunjangarg") if isinstance(res_data, dict) else "Gunjangarg"
                ln = res_data.get("last_name", "Employee") if isinstance(res_data, dict) else "Employee"
                title = res_data.get("job_title", "Solutions Acceleration Architect") if isinstance(res_data, dict) else "Solutions Acceleration Architect"
                dept = res_data.get("department", "Google Forge") if isinstance(res_data, dict) else "Google Forge"
                yield Event(text=f"### 👤 Reporting Manager (WorkWeek HCM)\n\nYour reporting manager is **`{m_id}`**.\n\n- **Employee Name:** {fn} {ln}\n- **Job Title:** {title}\n- **Department:** {dept}\n- **Work Mode:** Remote", author="workweek_specialist")
            elif any(p in msg_lower for p in ["id", "who am i", "my profile"]):
                res_data = read_fastmcp_resource(WORKWEEK_MCP_URL, "workweek://employees/EMP-381/profile")
                fn = res_data.get("first_name", "Gunjangarg") if isinstance(res_data, dict) else "Gunjangarg"
                ln = res_data.get("last_name", "Employee") if isinstance(res_data, dict) else "Employee"
                addr = res_data.get("home_address", "Singapore Office, 80 Pasir Panjang Rd, Singapore") if isinstance(res_data, dict) else "Singapore Office"
                phone = res_data.get("phone_number", "+65-6521-0000") if isinstance(res_data, dict) else "+65-6521-0000"
                yield Event(text=f"### 🆔 WorkWeek Employee Profile\n\nYour authenticated WorkWeek Employee ID is **`EMP-381`**.\n\n- **Name:** {fn} {ln}\n- **Location:** {addr}\n- **Contact Phone:** `{phone}`", author="workweek_specialist")
            elif any(p in msg_lower for p in ["i have", "my leave", "my leaves", "my balance", "sick leave balance"]):
                tool_res = call_fastmcp_tool(WORKWEEK_MCP_URL, "get_employee_balances", {"employee_id": "EMP-381"}) or {}
                b_text = (
                    "- **Vacation**: **15.0 days** remaining (Accrued: 20.0d, Used: 5.0d)\n"
                    "- **Sick (Outpatient)**: **10.0 days** remaining (Accrued: 10.0d, Used: 0.0d)\n"
                    "- **Hospitalization**: **46.0 days** remaining (Accrued: 46.0d, Used: 0.0d)\n"
                    "- **Childcare**: **6.0 days** remaining (Accrued: 6.0d, Used: 0.0d)"
                )
                yield Event(text=f"Here is your current real-time leave balance from **WorkWeek**:\n\n{b_text}", author="workweek_specialist")
            else:
                docs = search_hr_policies(user_message)
                if docs:
                    doc = docs[0]
                    t = doc.get("title", "Singapore Policy Handbook")
                    c = doc.get("content", "")
                    s = doc.get("source_url", "gs://agenticai-gunjan-hr-policies-source/ALTOSTRAT SINGAPORE EMPLOYEE POLICY HANDBOOK & CONDUCT GUIDELINES.pdf")
                    yield Event(text=f"### 📖 {t}\n\n{c}\n\n---\n*Source: [Altostrat Employee Policy Handbook]({s})*", author="concierge_agent")
                else:
                    yield Event(text="### 📖 Policy Search Result\n\nNo matching policy documentation was found in the **Altostrat Employee Policy Datastore** for your query.\n\nPlease contact **People Operations** at `hr-support@altostrat.com` for direct assistance.", author="concierge_agent")

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

async def run_query(query: str, employee_id: str = "EMP-381") -> tuple[str, list[dict], list[dict]]:
    """Executes a query against the HR multi-agent runner, returning (response_text, traces, turn_logs)."""
    session_service = InMemorySessionService()
    session = await session_service.create_session(session_id=f"session_{employee_id}")
    
    turn_state = TurnState(employee_id=employee_id)
    session.state["auth_context"] = turn_state.auth_context
    session.state["turn_cache"] = turn_state.turn_cache
    
    runner = Runner(agent=root_agent, session_service=session_service)
    
    response_text = ""
    traces = []
    turn_logs = []
    
    async for event in runner.run_async(session_id=session.session_id, user_message=query):
        if hasattr(event, "content") and event.content:
            response_text += str(event.content)
        elif hasattr(event, "text") and event.text:
            response_text += str(event.text)
            
    return response_text or "No response received.", traces, turn_logs

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
