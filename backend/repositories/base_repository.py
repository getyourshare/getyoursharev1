from typing import Optional, List, Dict, Any
from datetime import datetime


class BaseRepository:
    def __init__(self, supabase_client):
        self.supabase = supabase_client
        self.table_name = None
    
    def _execute_query(self, query):
        try:
            result = query.execute()
            return {"success": True, "data": result.data, "count": getattr(result, 'count', None)}
        except Exception as e:
            return {"success": False, "error": str(e), "data": None}
    
    def find_by_id(self, id: str) -> Optional[Dict[str, Any]]:
        if not self.table_name:
            raise ValueError("table_name must be defined")
        result = self._execute_query(
            self.supabase.table(self.table_name).select("*").eq("id", id).maybe_single()
        )
        return result["data"] if result["success"] else None
    
    def find_all(self, limit: int = 100, offset: int = 0) -> List[Dict[str, Any]]:
        if not self.table_name:
            raise ValueError("table_name must be defined")
        result = self._execute_query(
            self.supabase.table(self.table_name).select("*").range(offset, offset + limit - 1)
        )
        return result["data"] if result["success"] else []
    
    def create(self, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        if not self.table_name:
            raise ValueError("table_name must be defined")
        if "created_at" not in data:
            data["created_at"] = datetime.utcnow().isoformat()
        result = self._execute_query(
            self.supabase.table(self.table_name).insert(data).execute()
        )
        return result["data"][0] if result["success"] and result["data"] else None
    
    def update(self, id: str, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        if not self.table_name:
            raise ValueError("table_name must be defined")
        data["updated_at"] = datetime.utcnow().isoformat()
        result = self._execute_query(
            self.supabase.table(self.table_name).update(data).eq("id", id).execute()
        )
        return result["data"][0] if result["success"] and result["data"] else None
    
    def delete(self, id: str) -> bool:
        if not self.table_name:
            raise ValueError("table_name must be defined")
        result = self._execute_query(
            self.supabase.table(self.table_name).delete().eq("id", id).execute()
        )
        return result["success"]
