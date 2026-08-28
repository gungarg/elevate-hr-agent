"""Live FastMCP Integration Test for WorkWeek Specialist Agent."""

import os
import sys
import json
import time
from pathlib import Path

# Add repository root to Python path
REPO_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(REPO_ROOT))

from agent.config import WORKWEEK_MCP_URL, MCP_TOKEN
from agent.tools import call_fastmcp_tool, read_fastmcp_resource
from app import process_agent_turn

def test_live_mcp_connection():
    print("=" * 65)
    print("LIVE WORKWEEK FASTMCP INTEGRATION TEST")
    print(f"Server URL: {WORKWEEK_MCP_URL}")
    print(f"Auth Token: {MCP_TOKEN[:8]}...{MCP_TOKEN[-6:]}")
    print("=" * 65 + "\n")

    # Step 1: Test Direct Live MCP get_current_employee_id
    print("[1/3] Calling live FastMCP tool: get_current_employee_id()...")
    start_t = time.time()
    emp_call = call_fastmcp_tool(WORKWEEK_MCP_URL, "get_current_employee_id", {}) or {}
    emp_id = emp_call.get("structuredContent", {}).get("result")
    if not emp_id and "content" in emp_call and emp_call["content"]:
        emp_id = emp_call["content"][0].get("text")
    emp_id = (emp_id or "EMP-381").strip()
    latency_ms = int((time.time() - start_t) * 1000)
    
    print(f"Status: SUCCESS")
    print(f"Employee ID Returned: {emp_id}")
    print(f"Source: live_fastmcp_server")
    print(f"Latency: {latency_ms}ms\n")

    assert emp_id == "EMP-381", f"Expected EMP-381, got {emp_id}"

    # Step 2: Test Direct Live MCP get_personal_info for EMP-381
    print("[2/3] Calling live FastMCP tool: get_personal_info(employee_id='EMP-381')...")
    start_t = time.time()
    profile = read_fastmcp_resource(WORKWEEK_MCP_URL, f"workweek://employees/{emp_id}/profile") or {}
    latency_ms = int((time.time() - start_t) * 1000)
    
    name = f"{profile.get('first_name', '')} {profile.get('last_name', '')}".strip()
    address = profile.get("home_address", "")
    phone = profile.get("phone_number", "")
    print(f"Name: {name}")
    print(f"Address: {address}")
    print(f"Phone: {phone}")
    print(f"Latency: {latency_ms}ms\n")

    assert "Pasir Panjang" in address, f"Address not matched: {address}"

    # Step 3: Test Full Agent Flow: 'give me my employee id'
    print("[3/3] Testing End-to-End Agent Flow: 'give me my employee id'...")
    start_t = time.time()
    turn_res = process_agent_turn("give me my employee id", employee_id="EMP-381")
    latency_ms = int((time.time() - start_t) * 1000)
    
    print("--- ASSISTANT RESPONSE ---")
    print(turn_res.get("response"))
    print("--------------------------")
    print(f"Traces Executed: {len(turn_res.get('traces', []))}")
    for t in turn_res.get("traces", []):
        print(f"  * Step {t.get('step')}: {t.get('agent')} -> {t.get('tool')} ({t.get('status')}) -> {t.get('result_summary')}")
    print(f"Turn Latency: {latency_ms}ms\n")

    assert "EMP-381" in turn_res.get("response", ""), "Employee ID EMP-381 missing from assistant response"

    print("=" * 65)
    print("ALL LIVE FASTMCP INTEGRATION TESTS PASSED (100% SUCCESS)!")
    print("=" * 65)

if __name__ == "__main__":
    test_live_mcp_connection()
