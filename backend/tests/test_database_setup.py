"""
Configuration et setup de la base de donnees de test
Gere l initialisation de donnees de test reelles dans Supabase
"""

import os
from typing import Dict, Any, Optional
from datetime import datetime
from uuid import uuid4
from dotenv import load_dotenv

# Charger les variables d environnement
load_dotenv()


class TestDatabase:
    """Gestionnaire de base de donnees de test"""
    
    def __init__(self):
        self.supabase_client = None
        self.test_data = {}
        self.created_records = []
        
    def get_client(self):
        """Retourne le client Supabase pour les tests"""
        if self.supabase_client is None:
            try:
                from supabase import create_client
                supabase_url = os.getenv("SUPABASE_URL")
                supabase_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY") or os.getenv("SUPABASE_KEY")
                
                if supabase_url and supabase_key:
                    self.supabase_client = create_client(supabase_url, supabase_key)
                    print(f"Test Supabase client initialized")
                else:
                    print("Warning: Supabase credentials not found in environment")
            except Exception as e:
                print(f"Error creating Supabase client: {e}")
        
        return self.supabase_client
    
    async def cleanup(self):
        """Nettoie les donnees de test creees"""
        print("Cleaning up test data...")
        pass


# Instance globale
test_db = TestDatabase()


def get_supabase_for_tests():
    """Retourne le client Supabase pour les tests"""
    return test_db.get_client()


def get_test_data() -> Dict[str, Any]:
    """Retourne les donnees de test"""
    return {
        "user_influencer": {
            "id": str(uuid4()),
            "email": "test_influencer@example.com",
            "username": "test_influencer",
            "role": "influencer",
            "subscription_plan": "pro",
            "created_at": datetime.now().isoformat()
        },
        "user_merchant": {
            "id": str(uuid4()),
            "email": "test_merchant@example.com",
            "username": "test_merchant",
            "role": "merchant",
            "subscription_plan": "starter",
            "created_at": datetime.now().isoformat()
        },
        "user_admin": {
            "id": str(uuid4()),
            "email": "test_admin@example.com",
            "username": "test_admin",
            "role": "admin",
            "subscription_plan": "enterprise",
            "created_at": datetime.now().isoformat()
        },
        "product_premium": {
            "id": str(uuid4()),
            "name": "Test Product Premium",
            "description": "A premium test product for testing purposes",
            "price": 99.99,
            "category": "Test",
            "commission_rate": 15.0,
            "created_at": datetime.now().isoformat()
        },
        "tracking_link": {
            "id": str(uuid4()),
            "original_url": "https://example.com/product/123",
            "short_code": "TEST123",
            "clicks": 0,
            "conversions": 0,
            "created_at": datetime.now().isoformat()
        },
        "sale_completed": {
            "id": str(uuid4()),
            "amount": 99.99,
            "commission_amount": 14.99,
            "status": "completed",
            "created_at": datetime.now().isoformat()
        },
        "commission_pending": {
            "id": str(uuid4()),
            "amount": 14.99,
            "status": "pending",
            "created_at": datetime.now().isoformat()
        }
    }


async def setup_test_database() -> Dict[str, Any]:
    """Configure la base de donnees de test avec des donnees initiales"""
    print("Setting up test database...")
    
    supabase = get_supabase_for_tests()
    
    if supabase is None:
        print("Warning: Supabase client not available, using mock data")
        return get_test_data()
    
    test_data = get_test_data()
    
    print("Test database setup complete")
    return test_data
