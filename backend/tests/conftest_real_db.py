"""
Fixtures pytest avec VRAIE base de données Supabase
AUCUN MOCK - Tous les tests utilisent des données réelles
"""

import pytest
import asyncio
from datetime import datetime, timedelta
from uuid import uuid4

# Import du setup de la vraie DB
from .test_database_setup import (
    setup_test_database,
    get_test_data,
    get_supabase_for_tests,
    test_db
)


# ============================================================================
# CONFIGURATION PYTEST
# ============================================================================

@pytest.fixture(scope="session")
def event_loop():
    """Event loop pour tests async"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session", autouse=True)
async def setup_database():
    """Setup de la base de données AVANT tous les tests"""
    print("\n" + "="*60)
    print("🚀 INITIALISATION BASE DE DONNÉES DE TEST")
    print("="*60)
    
    test_data = await setup_test_database()
    
    yield test_data
    
    # Cleanup après tous les tests
    print("\n" + "="*60)
    print("🧹 NETTOYAGE BASE DE DONNÉES DE TEST")
    print("="*60)
    await test_db.cleanup()


# ============================================================================
# FIXTURES CLIENT SUPABASE RÉEL
# ============================================================================

@pytest.fixture
def supabase_client():
    """Client Supabase RÉEL - PAS DE MOCK!"""
    return get_supabase_for_tests()


@pytest.fixture
def real_supabase():
    """Alias pour supabase_client - pour compatibilité"""
    return get_supabase_for_tests()


# ============================================================================
# FIXTURES DONNÉES DE TEST RÉELLES
# ============================================================================

@pytest.fixture
def test_data():
    """Toutes les données de test de la vraie DB"""
    return get_test_data()


@pytest.fixture
def sample_user_influencer(test_data):
    """Influenceur de test RÉEL"""
    return test_data.get("user_influencer")


@pytest.fixture
def sample_user_merchant(test_data):
    """Marchand de test RÉEL"""
    return test_data.get("user_merchant")


@pytest.fixture
def sample_user_admin(test_data):
    """Admin de test RÉEL"""
    return test_data.get("user_admin")


@pytest.fixture
def sample_user_id(sample_user_influencer):
    """ID de l'influenceur de test"""
    return sample_user_influencer.get("id") if sample_user_influencer else str(uuid4())


@pytest.fixture
def sample_influencer_id(sample_user_influencer):
    """Alias pour sample_user_id"""
    return sample_user_influencer.get("id") if sample_user_influencer else str(uuid4())


@pytest.fixture
def sample_merchant_id(sample_user_merchant):
    """ID du marchand de test"""
    return sample_user_merchant.get("id") if sample_user_merchant else str(uuid4())


@pytest.fixture
def sample_product(test_data):
    """Produit de test RÉEL"""
    return test_data.get("product_premium")


@pytest.fixture
def sample_product_id(sample_product):
    """ID du produit de test"""
    return sample_product.get("id") if sample_product else str(uuid4())


@pytest.fixture
def sample_tracking_link(test_data):
    """Lien de tracking de test RÉEL"""
    return test_data.get("tracking_link")


@pytest.fixture
def sample_tracking_link_id(sample_tracking_link):
    """ID du lien de tracking"""
    return sample_tracking_link.get("id") if sample_tracking_link else str(uuid4())


@pytest.fixture
def sample_sale(test_data):
    """Vente de test RÉELLE"""
    return test_data.get("sale_completed")


@pytest.fixture
def sample_sale_id(sample_sale):
    """ID de la vente de test"""
    return sample_sale.get("id") if sample_sale else str(uuid4())


@pytest.fixture
def sample_commission(test_data):
    """Commission de test RÉELLE"""
    return test_data.get("commission_paid")


@pytest.fixture
def sample_commission_id(sample_commission):
    """ID de la commission de test"""
    return sample_commission.get("id") if sample_commission else str(uuid4())


# ============================================================================
# FIXTURES POUR CRÉATION DE DONNÉES
# ============================================================================

@pytest.fixture
def sample_sale_request(sample_influencer_id, sample_merchant_id, sample_product_id, sample_tracking_link_id):
    """Requête de création de vente"""
    return {
        "amount": 99.99,
        "quantity": 1,
        "influencer_id": sample_influencer_id,
        "merchant_id": sample_merchant_id,
        "product_id": sample_product_id,
        "link_id": sample_tracking_link_id,
        "payment_status": "pending",
        "status": "pending",
    }


@pytest.fixture
def sample_commission_request(sample_influencer_id, sample_sale_id):
    """Requête de création de commission"""
    return {
        "amount": 14.99,
        "influencer_id": sample_influencer_id,
        "sale_id": sample_sale_id,
        "status": "pending",
    }


# ============================================================================
# FIXTURES POUR ERREURS (conservées pour compatibilité)
# ============================================================================

@pytest.fixture
def mock_postgres_error():
    """Factory pour créer des erreurs PostgreSQL mockées"""
    class PostgresError:
        def __init__(self, code: str, message: str):
            self.code = code
            self.message = message
    
    def _create_error(code: str, message: str):
        return PostgresError(code, message)
    
    return _create_error


# ============================================================================
# HELPERS
# ============================================================================

def create_test_user(supabase_client, **kwargs):
    """Helper pour créer un utilisateur de test supplémentaire"""
    user_data = {
        "id": str(uuid4()),
        "email": f"test_{uuid4().hex[:8]}@example.com",
        "username": f"test_user_{uuid4().hex[:8]}",
        "role": kwargs.get("role", "influencer"),
        "balance": kwargs.get("balance", 0.0),
        "created_at": datetime.utcnow().isoformat(),
        **kwargs
    }
    
    result = supabase_client.table("users").insert(user_data).execute()
    return result.data[0] if result.data else None


def create_test_product(supabase_client, merchant_id, **kwargs):
    """Helper pour créer un produit de test supplémentaire"""
    product_data = {
        "id": str(uuid4()),
        "name": f"TEST Product {uuid4().hex[:8]}",
        "description": "Produit de test",
        "price": kwargs.get("price", 99.99),
        "merchant_id": merchant_id,
        "commission_rate": kwargs.get("commission_rate", 10.0),
        "created_at": datetime.utcnow().isoformat(),
        **kwargs
    }
    
    result = supabase_client.table("products").insert(product_data).execute()
    return result.data[0] if result.data else None


def create_test_sale(supabase_client, **kwargs):
    """Helper pour créer une vente de test supplémentaire"""
    sale_data = {
        "id": str(uuid4()),
        "amount": kwargs.get("amount", 99.99),
        "quantity": kwargs.get("quantity", 1),
        "status": kwargs.get("status", "pending"),
        "payment_status": kwargs.get("payment_status", "pending"),
        "created_at": datetime.utcnow().isoformat(),
        **kwargs
    }
    
    result = supabase_client.table("sales").insert(sale_data).execute()
    return result.data[0] if result.data else None


def create_test_commission(supabase_client, **kwargs):
    """Helper pour créer une commission de test supplémentaire"""
    commission_data = {
        "id": str(uuid4()),
        "amount": kwargs.get("amount", 14.99),
        "status": kwargs.get("status", "pending"),
        "created_at": datetime.utcnow().isoformat(),
        **kwargs
    }
    
    result = supabase_client.table("commissions").insert(commission_data).execute()
    return result.data[0] if result.data else None


# Exporter les helpers
__all__ = [
    'supabase_client',
    'real_supabase',
    'test_data',
    'sample_user_influencer',
    'sample_user_merchant',
    'sample_user_admin',
    'sample_user_id',
    'sample_influencer_id',
    'sample_merchant_id',
    'sample_product',
    'sample_product_id',
    'sample_tracking_link',
    'sample_tracking_link_id',
    'sample_sale',
    'sample_sale_id',
    'sample_commission',
    'sample_commission_id',
    'sample_sale_request',
    'sample_commission_request',
    'mock_postgres_error',
    'create_test_user',
    'create_test_product',
    'create_test_sale',
    'create_test_commission',
]
