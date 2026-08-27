import os
import yaml
from pathlib import Path
from typing import Optional

try:
    from google.adk.tools import FunctionTool
except ImportError:
    class FunctionTool:
        def __init__(self, func):
            self.func = func

from agent.config import KNOWLEDGE_DIR, POLICY_GCS_BUCKET, KNOWLEDGE_LOCAL_FALLBACK

_CONCEPT_CACHE: dict[str, dict] = {}
_CONCEPT_LIST_CACHE: list[dict] = []

def _load_local_bundle(bundle_dir: Path):
    """Loads OKF concept files from local directory into cache."""
    global _CONCEPT_CACHE, _CONCEPT_LIST_CACHE
    temp_cache = {}
    temp_list = []
    
    for md_file in bundle_dir.glob("**/*.md"):
        if md_file.name in ["index.md", "log.md"]:
            continue
        try:
            content = md_file.read_text(encoding="utf-8")
            if content.startswith("---"):
                parts = content.split("---", 2)
                frontmatter = yaml.safe_load(parts[1]) if len(parts) >= 3 else {}
                body = parts[2].strip() if len(parts) >= 3 else content
                
                rel_id = md_file.relative_to(bundle_dir).with_suffix("").as_posix()
                concept_data = {
                    "concept_id": rel_id,
                    "title": frontmatter.get("title", rel_id),
                    "description": frontmatter.get("description", ""),
                    "tags": frontmatter.get("tags", []),
                    "sources": frontmatter.get("sources", []),
                    "verified": frontmatter.get("verified", {}),
                    "content": body,
                }
                temp_cache[rel_id] = concept_data
                temp_list.append({
                    "concept_id": rel_id,
                    "title": concept_data["title"],
                    "description": concept_data["description"],
                    "tags": concept_data["tags"],
                })
        except Exception as e:
            print(f"Error reading local concept {md_file}: {e}")
            
    _CONCEPT_CACHE = temp_cache
    _CONCEPT_LIST_CACHE = temp_list

def init_okf_engine():
    """Initializes OKF engine from GCS or falls back to local knowledge directory."""
    global _CONCEPT_CACHE, _CONCEPT_LIST_CACHE
    try:
        from google.cloud import storage
        client = storage.Client()
        bucket = client.bucket(POLICY_GCS_BUCKET)
        blobs = list(bucket.list_blobs(prefix="knowledge/"))
        if blobs:
            temp_cache = {}
            temp_list = []
            for blob in blobs:
                if blob.name.endswith(".md") and not blob.name.endswith(("index.md", "log.md")):
                    content = blob.download_as_text()
                    parts = content.split("---", 2)
                    frontmatter = yaml.safe_load(parts[1]) if len(parts) >= 3 else {}
                    body = parts[2].strip() if len(parts) >= 3 else content
                    
                    concept_id = blob.name.replace("knowledge/", "").replace(".md", "")
                    concept_data = {
                        "concept_id": concept_id,
                        "title": frontmatter.get("title", concept_id),
                        "description": frontmatter.get("description", ""),
                        "tags": frontmatter.get("tags", []),
                        "sources": frontmatter.get("sources", []),
                        "verified": frontmatter.get("verified", {}),
                        "content": body,
                    }
                    temp_cache[concept_id] = concept_data
                    temp_list.append({
                        "concept_id": concept_id,
                        "title": concept_data["title"],
                        "description": concept_data["description"],
                        "tags": concept_data["tags"],
                    })
            _CONCEPT_CACHE = temp_cache
            _CONCEPT_LIST_CACHE = temp_list
            print(f"Loaded {len(_CONCEPT_LIST_CACHE)} concepts from GCS: gs://{POLICY_GCS_BUCKET}/knowledge/")
            return
    except Exception as e:
        if not KNOWLEDGE_LOCAL_FALLBACK:
            print(f"Warning: GCS OKF load failed: {e}")

    # Fallback to local knowledge bundle
    if KNOWLEDGE_DIR.exists():
        _load_local_bundle(KNOWLEDGE_DIR)
        print(f"Loaded {len(_CONCEPT_LIST_CACHE)} concepts from local bundle: {KNOWLEDGE_DIR}")

init_okf_engine()

def list_concepts(domain: Optional[str] = None) -> list[dict]:
    """Lists available HR policy concepts with title, description, and tags from YAML frontmatter.
    
    Args:
        domain: Optional domain directory filter (e.g. '01-paid-time-off', '04-travel-expenses', '05-ethics-compliance').
    
    Returns:
        A list of concept summary objects containing concept_id, title, description, and tags.
    """
    if not _CONCEPT_LIST_CACHE:
        init_okf_engine()
    if domain:
        return [c for c in _CONCEPT_LIST_CACHE if c["concept_id"].startswith(domain)]
    return _CONCEPT_LIST_CACHE

def read_concept(concept_id: str) -> dict:
    """Reads the full markdown body, metadata, and citation sources for a specific concept.
    
    Args:
        concept_id: The relative concept path (e.g. '01-paid-time-off/1.1-outpatient-sick-hospitalization', '05-ethics-compliance/5.4-remote-work-equipment').
        
    Returns:
        A dictionary containing concept_id, title, content (markdown), sources, and verification info.
    """
    if not _CONCEPT_CACHE:
        init_okf_engine()
        
    clean_id = concept_id.replace(".md", "").strip("/")
    if clean_id in _CONCEPT_CACHE:
        return _CONCEPT_CACHE[clean_id]
        
    # Case-insensitive / partial prefix match fallback
    for k, v in _CONCEPT_CACHE.items():
        if k.endswith(clean_id) or clean_id in k:
            return v
            
    return {"error": f"Policy concept '{concept_id}' not found in knowledge catalog."}

list_concepts_tool = FunctionTool(func=list_concepts)
read_concept_tool = FunctionTool(func=read_concept)
