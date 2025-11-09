from typing import Optional, List, Dict, Any
from .base_repository import BaseRepository


class SaleRepository(BaseRepository):
    def __init__(self, supabase_client):
        super().__init__(supabase_client)
        self.table_name = "sales"
    
    def find_by_merchant(self, merchant_id: str) -> List[Dict[str, Any]]:
        result = self._execute_query(
            self.supabase.table(self.table_name).select("*").eq("merchant_id", merchant_id).order("created_at", desc=True)
        )
        return result["data"] if result["success"] else []
