"""
Middleware d'authentification et d'autorisation
Gère la vérification des tokens JWT et le contrôle d'accès basé sur les rôles
"""

import os
import jwt
from typing import List, Optional, Callable
from functools import wraps
from fastapi import HTTPException, Security, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials


# Configuration JWT
SECRET_KEY = os.getenv("JWT_SECRET_KEY", "your-secret-key-change-in-production")
ALGORITHM = "HS256"

# Security scheme pour FastAPI
security = HTTPBearer()


def verify_token(credentials: HTTPAuthorizationCredentials = Security(security)) -> dict:
    """
    Vérifie et décode un token JWT
    
    Args:
        credentials: Credentials HTTP contenant le token Bearer
        
    Returns:
        Payload du token décodé (contient user_id, email, role, etc.)
        
    Raises:
        HTTPException: Si le token est invalide ou expiré
    """
    token = credentials.credentials
    
    try:
        # Décoder le token JWT
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        
        # Vérifier que le payload contient les champs requis
        if "user_id" not in payload:
            raise HTTPException(
                status_code=401,
                detail="Token invalide: user_id manquant"
            )
        
        return payload
        
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=401,
            detail="Token expiré"
        )
    except jwt.InvalidTokenError:
        raise HTTPException(
            status_code=401,
            detail="Token invalide"
        )
    except Exception as e:
        raise HTTPException(
            status_code=401,
            detail=f"Erreur de validation du token: {str(e)}"
        )


def require_role(*allowed_roles: str) -> Callable:
    """
    Décorateur pour restreindre l'accès aux endpoints selon le rôle utilisateur
    
    Args:
        *allowed_roles: Rôles autorisés (admin, merchant, influencer, etc.)
        
    Returns:
        Décorateur de fonction
        
    Exemple:
        @router.get("/admin/stats")
        @require_role("admin")
        async def admin_stats(user: dict = Depends(verify_token)):
            ...
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Récupérer le token user depuis les kwargs (injecté par Depends)
            user = kwargs.get('user') or kwargs.get('current_user')
            
            if not user:
                raise HTTPException(
                    status_code=401,
                    detail="Authentification requise"
                )
            
            user_role = user.get('role')
            
            # Vérifier si le rôle de l'utilisateur est autorisé
            if user_role not in allowed_roles:
                raise HTTPException(
                    status_code=403,
                    detail=f"Accès interdit. Rôles autorisés: {', '.join(allowed_roles)}"
                )
            
            return await func(*args, **kwargs)
        
        return wrapper
    return decorator


def get_current_user(token_data: dict = Depends(verify_token)) -> dict:
    """
    Dependency pour récupérer l'utilisateur courant depuis le token
    
    Args:
        token_data: Données du token décodé (auto-injecté par Depends)
        
    Returns:
        Dictionnaire contenant les informations de l'utilisateur
        
    Exemple:
        @router.get("/profile")
        async def get_profile(user: dict = Depends(get_current_user)):
            return {"user_id": user["user_id"], "email": user["email"]}
    """
    return token_data


def get_optional_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(lambda: None)
) -> Optional[dict]:
    """
    Dependency pour récupérer l'utilisateur si authentifié, None sinon
    Utile pour les endpoints publics avec contenu personnalisé pour utilisateurs connectés
    
    Args:
        credentials: Credentials HTTP (optionnel)
        
    Returns:
        Données utilisateur ou None
    """
    if credentials is None:
        return None
    
    try:
        return verify_token(credentials)
    except HTTPException:
        return None
