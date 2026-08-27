from typing import Any, Optional
import time

class TurnState:
    """Manages immutable identity anchors and ephemeral turn-scoped memoization."""
    
    def __init__(self, employee_id: str = "EMP1024", email: str = "employee@altostrat.com"):
        self.auth_context = {
            "employee_id": employee_id,
            "email": email,
            "roles": ["employee"],
            "authenticated_at": time.time()
        }
        self.turn_cache: dict[str, Any] = {}
        
    def get_authenticated_employee_id(self) -> str:
        return self.auth_context["employee_id"]
        
    def get_memoized(self, key: str) -> Optional[Any]:
        return self.turn_cache.get(key)
        
    def set_memoized(self, key: str, value: Any):
        self.turn_cache[key] = value
        
    def clear_turn_cache(self):
        self.turn_cache.clear()
