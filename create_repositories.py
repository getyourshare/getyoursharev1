"""Script pour créer les fichiers repository"""
import os

base_dir = r"c:\Users\samye\OneDrive\Desktop\getyourshar v1\Getyourshare1\backend\repositories"

# Créer __init__.py
init_content = """from .base_repository import BaseRepository
from .user_repository import UserRepository
from .product_repository import ProductRepository
from .sale_repository import SaleRepository
from .tracking_repository import TrackingRepository
from .lead_repositories import (
    LeadRepository,
    DepositRepository,
    DepositTransactionRepository,
    LeadValidationRepository,
    InfluencerAgreementRepository,
    CampaignSettingsRepository
)

__all__ = [
    'BaseRepository',
    'UserRepository',
    'ProductRepository',
    'SaleRepository',
    'TrackingRepository',
    'LeadRepository',
    'DepositRepository',
    'DepositTransactionRepository',
    'LeadValidationRepository',
    'InfluencerAgreementRepository',
    'CampaignSettingsRepository',
]
"""

with open(os.path.join(base_dir, "__init__.py"), "w", encoding="utf-8") as f:
    f.write(init_content)

# Créer base_repository.py
base_repo_content = """from typing import Optional, List, Dict, Any
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
"""

with open(os.path.join(base_dir, "base_repository.py"), "w", encoding="utf-8") as f:
    f.write(base_repo_content)

# Créer user_repository.py
user_repo_content = """from typing import Optional, List, Dict, Any
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
"""

with open(os.path.join(base_dir, "user_repository.py"), "w", encoding="utf-8") as f:
    f.write(user_repo_content)

# Créer product_repository.py
product_repo_content = """from typing import Optional, List, Dict, Any
from .base_repository import BaseRepository


class ProductRepository(BaseRepository):
    def __init__(self, supabase_client):
        super().__init__(supabase_client)
        self.table_name = "products"
    
    def find_by_merchant(self, merchant_id: str) -> List[Dict[str, Any]]:
        result = self._execute_query(
            self.supabase.table(self.table_name).select("*").eq("merchant_id", merchant_id)
        )
        return result["data"] if result["success"] else []
"""

with open(os.path.join(base_dir, "product_repository.py"), "w", encoding="utf-8") as f:
    f.write(product_repo_content)

# Créer sale_repository.py
sale_repo_content = """from typing import Optional, List, Dict, Any
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
"""

with open(os.path.join(base_dir, "sale_repository.py"), "w", encoding="utf-8") as f:
    f.write(sale_repo_content)

# Créer tracking_repository.py
tracking_repo_content = """from typing import Optional, List, Dict, Any
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
"""

with open(os.path.join(base_dir, "tracking_repository.py"), "w", encoding="utf-8") as f:
    f.write(tracking_repo_content)

print("✅ Tous les fichiers repository ont été créés avec succès!")
