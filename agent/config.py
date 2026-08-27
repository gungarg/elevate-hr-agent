import os
from pathlib import Path

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

BASE_DIR = Path(__file__).parent.parent
KNOWLEDGE_DIR = BASE_DIR / "knowledge"

PROJECT_ID = os.getenv("GOOGLE_CLOUD_PROJECT", "elevate-hr-demo")
LOCATION = os.getenv("GOOGLE_CLOUD_LOCATION", "us-central1")
MODEL_NAME = os.getenv("GEMINI_MODEL", "gemini-3.5-flash")

POLICY_GCS_BUCKET = os.getenv("POLICY_GCS_BUCKET", "elevate-hr-policies-prod")
KNOWLEDGE_LOCAL_FALLBACK = os.getenv("KNOWLEDGE_LOCAL_FALLBACK", "true").lower() == "true"

WORKWEEK_MCP_URL = os.getenv("WORKWEEK_MCP_URL", "https://mock-saas.aishprabhat.demo.altostrat.com/work-week/mcp/")
SERVICEIMMEDIATELY_MCP_URL = os.getenv("SERVICEIMMEDIATELY_MCP_URL", "https://mock-saas.aishprabhat.demo.altostrat.com/service-immediately/mcp/")
MCP_TOKEN = os.getenv("MCP_TOKEN", "mcp_your_token_here")

ENABLE_MODEL_ARMOR = os.getenv("ENABLE_MODEL_ARMOR", "false").lower() == "true"
