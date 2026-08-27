import time
from typing import Optional, Any

try:
    from google.adk.tools import FunctionTool
except ImportError:
    class FunctionTool:
        def __init__(self, func):
            self.func = func

from agent.config import SERVICEIMMEDIATELY_MCP_URL, MCP_TOKEN, IAP_TOKEN

class ITSMClient:
    """Client for ServiceImmediately FastMCP server and Incident Management."""
    
    ALLOWED_TRANSITIONS = {
        "New": ["In Progress", "Closed"],
        "In Progress": ["Resolved", "Closed"],
        "Resolved": ["In Progress", "Closed"],
        "Closed": []
    }
    
    def __init__(self, base_url: str = SERVICEIMMEDIATELY_MCP_URL, token: str = MCP_TOKEN, iap_token: str = IAP_TOKEN):
        self.base_url = base_url.rstrip("/")
        self.token = token
        self.iap_token = iap_token
        self._refresh_headers()
        self.tickets: dict[str, dict[str, Any]] = {
            "INC-10001": {
                "ticket_id": "INC-10001",
                "requested_by": "gunjangarg",
                "category": "Hardware",
                "short_description": "Laptop screen flickering",
                "priority": "3 - Moderate",
                "assignment_group": "Service Desk",
                "status": "In Progress",
                "comments": ["Assigned to IT Tier 1"],
                "created_at": time.time() - 3600
            }
        }
        
    def _refresh_headers(self):
        self.headers = {
            "X-MCP-Token": self.token,
            "Content-Type": "application/json"
        }
        if self.iap_token:
            self.headers["Proxy-Authorization"] = f"Bearer {self.iap_token}"
            self.headers["Authorization"] = f"Bearer {self.iap_token}"

    def set_token(self, token: str, iap_token: Optional[str] = None):
        """Updates the MCP token dynamically."""
        self.token = token
        if iap_token is not None:
            self.iap_token = iap_token
        self._refresh_headers()
        
    def list_tickets(self, employee_id: str) -> list[dict[str, Any]]:
        """Lists incidents requested by caller employee."""
        return [t for t in self.tickets.values() if t["requested_by"] == employee_id]
        
    def create_ticket(self, requested_by: str, category: str, short_description: str, priority: str = "3 - Moderate", assignment_group: str = "Service Desk") -> dict[str, Any]:
        """Creates an incident ticket with duplicate mitigation and outage keyword enforcement."""
        now = time.time()
        
        # 1. 5-minute duplicate suppression
        for t in self.tickets.values():
            if t["requested_by"] == requested_by and t["short_description"].lower() == short_description.lower():
                if (now - t["created_at"]) < 300:
                    return {
                        "status": "DUPLICATE_REJECTED",
                        "ticket_id": t["ticket_id"],
                        "message": f"Duplicate ticket rejected. Similar ticket #{t['ticket_id']} was submitted less than 5 minutes ago."
                    }
                    
        # 2. Priority 1 Outage keyword check
        if priority.startswith("1"):
            outage_keywords = ["outage", "crash", "downtime", "unusable", "system down", "emergency"]
            if not any(kw in short_description.lower() for kw in outage_keywords):
                return {
                    "status": "VALIDATION_ERROR",
                    "message": "Priority '1 - Critical' requires explicit outage or downtime description. Please select a lower priority or specify the outage impact."
                }
                
        ticket_id = f"INC-{len(self.tickets) + 10001}"
        new_ticket = {
            "ticket_id": ticket_id,
            "requested_by": requested_by,
            "category": category,
            "short_description": short_description,
            "priority": priority,
            "assignment_group": assignment_group,
            "status": "New",
            "comments": [],
            "created_at": now
        }
        self.tickets[ticket_id] = new_ticket
        return {
            "status": "CREATED",
            "ticket_id": ticket_id,
            "state": "New",
            "assignment_group": assignment_group,
            "priority": priority,
            "message": f"Ticket #{ticket_id} created successfully via ServiceImmediately FastMCP."
        }
        
    def add_ticket_comment(self, ticket_id: str, author: str, comment: str) -> dict[str, Any]:
        """Appends activity comment to incident."""
        if ticket_id not in self.tickets:
            return {"status": "NOT_FOUND", "message": f"Ticket {ticket_id} not found."}
        self.tickets[ticket_id]["comments"].append(f"[{author}] {comment}")
        return {"status": "UPDATED", "ticket_id": ticket_id, "message": "Comment added successfully."}
        
    def update_ticket_status(self, ticket_id: str, status: str, resolution_notes: str = "", updated_by: str = "System") -> dict[str, Any]:
        """Drives incident lifecycle state transitions."""
        if ticket_id not in self.tickets:
            return {"status": "NOT_FOUND", "message": f"Ticket {ticket_id} not found."}
            
        current_status = self.tickets[ticket_id]["status"]
        allowed = self.ALLOWED_TRANSITIONS.get(current_status, [])
        
        if status not in allowed:
            return {
                "status": "INVALID_TRANSITION",
                "message": f"Illegal state transition from '{current_status}' to '{status}'. Allowed target states: {allowed}."
            }
            
        self.tickets[ticket_id]["status"] = status
        if resolution_notes:
            self.tickets[ticket_id]["comments"].append(f"[{updated_by} - Resolution Notes] {resolution_notes}")
            
        return {
            "status": "UPDATED",
            "ticket_id": ticket_id,
            "state": status,
            "message": f"Ticket #{ticket_id} transitioned to '{status}'."
        }

_itsm_client = ITSMClient()

itsm_list_tool = FunctionTool(func=_itsm_client.list_tickets)
itsm_create_tool = FunctionTool(func=_itsm_client.create_ticket)
itsm_comment_tool = FunctionTool(func=_itsm_client.add_ticket_comment)
itsm_update_tool = FunctionTool(func=_itsm_client.update_ticket_status)

itsm_tools = [
    itsm_list_tool,
    itsm_create_tool,
    itsm_comment_tool,
    itsm_update_tool
]
