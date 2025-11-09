"""
Package utilitaires pour l'application backend
"""

from .supabase_client import get_supabase_client, init_supabase, set_supabase_client

__all__ = [
    'get_supabase_client',
    'init_supabase',
    'set_supabase_client',
]
