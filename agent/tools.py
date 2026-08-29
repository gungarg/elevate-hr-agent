import os
import re
import json
import urllib.request
from typing import Optional, Any
from pathlib import Path

try:
    from google.adk.tools import VertexAiSearchTool, FunctionTool
except ImportError:
    class FunctionTool:
        def __init__(self, func, **kwargs):
            self.func = func
    class VertexAiSearchTool:
        def __init__(self, data_store_id: str, **kwargs):
            self.data_store_id = data_store_id

from agent.config import DATA_STORE_PATH, PROJECT_ID, WORKWEEK_MCP_URL, SERVICEIMMEDIATELY_MCP_URL, MCP_TOKEN

def search_hr_policies(query: str, region_filter: str = "Singapore") -> list[dict[str, Any]]:
    """
    Performs live semantic search across enterprise HR and IT policy documents in Vertex AI Search.
    Queries the live Vertex AI Search Datastore endpoint in GCP project `agenticai-gunjan`.
    """
    try:
        token = os.popen("/usr/local/google/home/gunjangarg/google-cloud-sdk/bin/gcloud auth print-access-token 2>/dev/null").read().strip()
        if token:
            url = f"https://discoveryengine.googleapis.com/v1/{DATA_STORE_PATH}/servingConfigs/default_search:search"
            payload = json.dumps({"query": query, "pageSize": 3}).encode("utf-8")
            req = urllib.request.Request(
                url,
                data=payload,
                headers={
                    "Authorization": f"Bearer {token}",
                    "X-Goog-User-Project": PROJECT_ID,
                    "Content-Type": "application/json"
                }
            )
            with urllib.request.urlopen(req) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                results = []
                for res in data.get("results", []):
                    doc = res.get("document", {})
                    struct_data = doc.get("derivedStructData", {})
                    snippets = struct_data.get("snippets", [{}])
                    extractive_answers = struct_data.get("extractive_answers", [{}])
                    content_text = ""
                    if extractive_answers and extractive_answers[0].get("content"):
                        content_text = extractive_answers[0].get("content", "")
                    elif snippets and snippets[0].get("snippet"):
                        content_text = snippets[0].get("snippet", "")

                    results.append({
                        "title": struct_data.get("title", "Singapore Employee Policy Handbook"),
                        "content": content_text or struct_data.get("link", ""),
                        "section": struct_data.get("section", "General"),
                        "source_url": struct_data.get("link", "https://docs.google.com/document/d/1omb7qXPLlY6H5PSH-dTra8pYwDX9fWG2NLqUdHFPZ3M")
                    })
                if results:
                    return results
    except Exception as e:
        print(f"[Vertex AI Search REST Warning]: {e}")

    return []

policy_search_tool = FunctionTool(func=search_hr_policies)

def call_fastmcp_tool(server_url: str, tool_name: str, arguments: dict[str, Any]) -> dict[str, Any]:
    """Helper for JSON-RPC 2.0 FastMCP tool execution over Streamable HTTP."""
    payload = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "tools/call",
        "params": {
            "name": tool_name,
            "arguments": arguments
        }
    }
    req = urllib.request.Request(
        server_url,
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Content-Type": "application/json",
            "Accept": "application/json, text/event-stream",
            "X-MCP-Token": MCP_TOKEN
        }
    )
    try:
        with urllib.request.urlopen(req) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            return data.get("result", {})
    except Exception as e:
        return {"status": "ERROR", "message": str(e)}

def read_fastmcp_resource(server_url: str, uri: str) -> dict[str, Any]:
    """Helper for reading FastMCP resources over Streamable HTTP."""
    payload = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "resources/read",
        "params": {
            "uri": uri
        }
    }
    req = urllib.request.Request(
        server_url,
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Content-Type": "application/json",
            "Accept": "application/json, text/event-stream",
            "X-MCP-Token": MCP_TOKEN
        }
    )
    try:
        with urllib.request.urlopen(req) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            contents = data.get("result", {}).get("contents", [])
            if contents:
                text = contents[0].get("text", "")
                return json.loads(text) if text.startswith("{") else {"text": text}
            return {}
    except Exception as e:
        return {"status": "ERROR", "message": str(e)}
