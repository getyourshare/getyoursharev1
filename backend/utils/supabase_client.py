"""
Utilitaire pour accéder au client Supabase
Fournit une instance globale du client Supabase pour toute l'application
"""

import os
from typing import Optional
from supabase import create_client, Client

# Instance globale du client Supabase
_supabase_client: Optional[Client] = None


def init_supabase() -> Optional[Client]:
    """
    Initialise le client Supabase avec les variables d'environnement
    
    Returns:
        Client Supabase ou None si les variables ne sont pas configurées
    """
    global _supabase_client
    
    if _supabase_client is not None:
        return _supabase_client
    
    supabase_url = os.getenv("SUPABASE_URL")
    supabase_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY") or os.getenv("SUPABASE_KEY")
    
    if not supabase_url or not supabase_key:
        print("⚠️ SUPABASE_URL ou SUPABASE_KEY non configurés")
        return None
    
    try:
        _supabase_client = create_client(supabase_url, supabase_key)
        print("✅ Client Supabase initialisé")
        return _supabase_client
    except Exception as e:
        print(f"❌ Erreur initialisation Supabase: {e}")
        return None


def get_supabase_client() -> Client:
    """
    Récupère l'instance du client Supabase
    
    Returns:
        Client Supabase
        
    Raises:
        RuntimeError: Si le client n'est pas initialisé
    """
    global _supabase_client
    
    if _supabase_client is None:
        _supabase_client = init_supabase()
    
    if _supabase_client is None:
        raise RuntimeError(
            "Client Supabase non initialisé. "
            "Vérifiez les variables d'environnement SUPABASE_URL et SUPABASE_KEY"
        )
    
    return _supabase_client


def set_supabase_client(client: Client) -> None:
    """
    Définit manuellement le client Supabase
    Utile pour les tests ou l'injection de dépendances
    
    Args:
        client: Instance du client Supabase
    """
    global _supabase_client
    _supabase_client = client
