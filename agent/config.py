import os
from pathlib import Path

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

BASE_DIR = Path(__file__).parent.parent

# Google Cloud Project & Model Configuration
PROJECT_ID = os.getenv("GOOGLE_CLOUD_PROJECT", "agenticai-gunjan")
LOCATION = os.getenv("GOOGLE_CLOUD_LOCATION", "us-central1")
MODEL_NAME = os.getenv("GEMINI_MODEL", "gemini-3.5-flash")

# Vertex AI Search (Enterprise Datastore)
DATA_STORE_ID = os.getenv("DATA_STORE_ID", "hr-policy-datastore")
DATA_STORE_PATH = os.getenv(
    "DATA_STORE_PATH",
    f"projects/{PROJECT_ID}/locations/global/collections/default_collection/dataStores/{DATA_STORE_ID}"
)
POLICY_GCS_BUCKET = os.getenv("POLICY_GCS_BUCKET", f"{PROJECT_ID}-hr-policies")

# FastMCP Remote Endpoints (Streamable HTTP)
WORKWEEK_MCP_URL = os.getenv(
    "WORKWEEK_MCP_URL",
    "https://mock-saas.aishprabhat.demo.altostrat.com/work-week/mcp/"
)
SERVICEIMMEDIATELY_MCP_URL = os.getenv(
    "SERVICEIMMEDIATELY_MCP_URL",
    "https://mock-saas.aishprabhat.demo.altostrat.com/service-immediately/mcp/"
)

# Active FastMCP Authentication Token
MCP_TOKEN = os.getenv("MCP_TOKEN", "mcp_zYnFTkwwEfKkx6qaHgW2XTiTRzREoiHjwDZR3I64XdA")
IAP_TOKEN = os.getenv("IAP_TOKEN", "")

# Google Cloud Model Armor GenAI Security
ENABLE_MODEL_ARMOR = os.getenv("ENABLE_MODEL_ARMOR", "true").lower() == "true"
