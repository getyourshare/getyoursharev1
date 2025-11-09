from typing import Optional, List, Dict, Any
from .base_repository import BaseRepository


class TrackingRepository(BaseRepository):
    def __init__(self, supabase_client):
        super().__init__(supabase_client)
        self.table_name = "tracking_events"
    
    def find_by_link(self, link_id: str) -> List[Dict[str, Any]]:
        result = self._execute_query(
            self.supabase.table(self.table_name).select("*").eq("link_id", link_id).order("created_at", desc=True)
        )
        return result["data"] if result["success"] else []
