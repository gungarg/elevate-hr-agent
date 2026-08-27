from typing import Optional, Literal, Any

try:
    from pydantic import BaseModel, Field
except ImportError:
    class BaseModel:
        def __init__(self, **kwargs):
            for k, v in kwargs.items():
                setattr(self, k, v)
    def Field(**kwargs):
        return kwargs.get("default", None)

class EmployeeProfile(BaseModel):
    employee_id: str
    name: Optional[str] = None
    email: Optional[str] = None
    department: Optional[str] = None
    role: Optional[str] = None
    work_mode: Optional[str] = "Remote"
    address: Optional[str] = None
    phone: Optional[str] = None
    manager_id: Optional[str] = None

class LeaveBalance(BaseModel):
    leave_type: str
    accrued: float
    used: float
    remaining: float

class WorkWeekTaskOutput(BaseModel):
    status: Literal["SUCCESS", "INSUFFICIENT_BALANCE", "VALIDATION_ERROR", "NOT_FOUND", "ERROR"]
    employee_id: str
    action: str = Field(description="Action executed e.g. GET_PROFILE, GET_BALANCES, BOOK_LEAVE, CANCEL_LEAVE")
    data: Optional[dict[str, Any]] = Field(default_factory=dict, description="Payload data resulting from operation")
    message: str = Field(description="Human-readable explanation of result")

class ITSMTaskOutput(BaseModel):
    status: Literal["CREATED", "UPDATED", "DUPLICATE_REJECTED", "INVALID_TRANSITION", "NOT_FOUND", "ERROR"]
    ticket_id: Optional[str] = None
    state: Optional[str] = None
    assignment_group: Optional[str] = None
    priority: Optional[str] = None
    message: str = Field(description="Human-readable explanation of result")
