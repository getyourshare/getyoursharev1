from typing import Optional, List, Dict, Any
from .base_repository import BaseRepository


class UserRepository(BaseRepository):
    def __init__(self, supabase_client):
        super().__init__(supabase_client)
        self.table_name = "users"
    
    def find_by_email(self, email: str) -> Optional[Dict[str, Any]]:
        result = self._execute_query(
            self.supabase.table(self.table_name).select("*").eq("email", email).maybe_single()
        )
        return result["data"] if result["success"] else None
    
    def find_by_role(self, role: str) -> List[Dict[str, Any]]:
        result = self._execute_query(
            self.supabase.table(self.table_name).select("*").eq("role", role)
        )
        return result["data"] if result["success"] else []
