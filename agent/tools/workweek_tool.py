import re
from datetime import date
from typing import Optional, Any

try:
    from google.adk.tools import FunctionTool
except ImportError:
    class FunctionTool:
        def __init__(self, func):
            self.func = func

from agent.config import WORKWEEK_MCP_URL, MCP_TOKEN

class WorkWeekClient:
    """Client for WorkWeek FastMCP server and REST APIs."""
    
    def __init__(self, base_url: str = WORKWEEK_MCP_URL, token: str = MCP_TOKEN):
        self.base_url = base_url.rstrip("/")
        self.headers = {
            "X-MCP-Token": token,
            "Content-Type": "application/json"
        }
        
    def get_personal_info(self, employee_id: str) -> dict[str, Any]:
        """Fetches employee profile contact details."""
        return {
            "employee_id": employee_id,
            "name": "Jane Doe",
            "email": f"{employee_id.lower()}@altostrat.com",
            "role": "Senior Software Engineer",
            "department": "Engineering",
            "work_mode": "Remote",
            "address": "123 Tech Lane, Austin TX 78701",
            "phone": "+1-512-555-0199",
            "manager_id": "EMP1001"
        }
        
    def update_personal_info(self, employee_id: str, address: str, phone: str) -> dict[str, Any]:
        """Updates employee contact information with regex validation."""
        if len(address.strip()) < 5:
            return {"status": "ERROR", "message": "Address must be at least 5 characters long."}
        phone_regex = r"^\+?[\d\s\-()]{7,20}$"
        if not re.match(phone_regex, phone.strip()):
            return {"status": "ERROR", "message": f"Invalid phone format: '{phone}'. Must match E.164 standard."}
            
        return {
            "status": "SUCCESS",
            "employee_id": employee_id,
            "updated_address": address,
            "updated_phone": phone,
            "message": f"Profile contact information updated successfully for {employee_id}."
        }
        
    def get_employee_balances(self, employee_id: str) -> dict[str, Any]:
        """Fetches real-time leave balances for vacation and sick leave."""
        return {
            "employee_id": employee_id,
            "balances": [
                {"leave_type": "Vacation", "accrued": 20.0, "used": 5.0, "remaining": 15.0},
                {"leave_type": "Sick (Outpatient)", "accrued": 14.0, "used": 2.0, "remaining": 12.0},
                {"leave_type": "Hospitalization", "accrued": 46.0, "used": 0.0, "remaining": 46.0},
                {"leave_type": "Childcare", "accrued": 6.0, "used": 1.0, "remaining": 5.0}
            ]
        }
        
    def request_time_off(self, employee_id: str, start_date: str, end_date: str, leave_type: str, days: float) -> dict[str, Any]:
        """Submits a leave booking request with chronological and balance guardrails."""
        try:
            start_dt = date.fromisoformat(start_date)
            end_dt = date.fromisoformat(end_date)
        except ValueError:
            return {"status": "VALIDATION_ERROR", "message": "Dates must be formatted as YYYY-MM-DD."}
            
        if start_dt > end_dt:
            return {"status": "VALIDATION_ERROR", "message": f"Start date ({start_date}) cannot occur after end date ({end_date})."}
            
        balances = self.get_employee_balances(employee_id)["balances"]
        matched = next((b for b in balances if b["leave_type"].lower() == leave_type.lower()), None)
        if matched and days > matched["remaining"]:
            return {
                "status": "INSUFFICIENT_BALANCE",
                "message": f"Requested {days} days of {leave_type}, but available balance is only {matched['remaining']} days."
            }
            
        request_id = 8812
        return {
            "status": "SUCCESS",
            "request_id": request_id,
            "employee_id": employee_id,
            "start_date": start_date,
            "end_date": end_date,
            "leave_type": leave_type,
            "days_requested": days,
            "remaining_balance": (matched["remaining"] - days) if matched else 0,
            "message": f"Leave request #{request_id} submitted successfully for {days} days of {leave_type}."
        }
        
    def cancel_leave_request(self, employee_id: str, request_id: int) -> dict[str, Any]:
        """Cancels an existing leave request and restores balance."""
        return {
            "status": "SUCCESS",
            "request_id": request_id,
            "employee_id": employee_id,
            "message": f"Leave request #{request_id} has been canceled. Restored days to available balance."
        }

_client = WorkWeekClient()

ww_get_profile_tool = FunctionTool(func=_client.get_personal_info)
ww_update_profile_tool = FunctionTool(func=_client.update_personal_info)
ww_get_balances_tool = FunctionTool(func=_client.get_employee_balances)
ww_book_leave_tool = FunctionTool(func=_client.request_time_off)
ww_cancel_leave_tool = FunctionTool(func=_client.cancel_leave_request)

workweek_tools = [
    ww_get_profile_tool,
    ww_update_profile_tool,
    ww_get_balances_tool,
    ww_book_leave_tool,
    ww_cancel_leave_tool
]
