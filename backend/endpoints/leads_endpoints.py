"""
Endpoints API pour le système de génération de LEADS
Marketplace services: génération leads, dépôts, validation, statistiques
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from typing import Optional, List
from decimal import Decimal
from pydantic import BaseModel, Field
from datetime import datetime

from backend.utils.supabase_client import get_supabase_client
from backend.middleware.auth import verify_token, require_role
from backend.services.lead_service import LeadService
from backend.services.deposit_service import DepositService


# ============================================
# MODELS PYDANTIC
# ============================================

class CreateLeadRequest(BaseModel):
    campaign_id: str
    influencer_id: Optional[str] = None
    commercial_id: Optional[str] = None
    estimated_value: float = Field(..., ge=50, description="Valeur estimée minimum 50 dhs")
    customer_name: Optional[str] = None
    customer_email: Optional[str] = None
    customer_phone: Optional[str] = None
    customer_company: Optional[str] = None
    customer_notes: Optional[str] = None
    source: str = 'direct'
    product_id: Optional[str] = None


class ValidateLeadRequest(BaseModel):
    status: str = Field(..., description="validated, rejected, converted, lost")
    quality_score: Optional[int] = Field(None, ge=1, le=10)
    feedback: Optional[str] = None
    rejection_reason: Optional[str] = None


class CreateDepositRequest(BaseModel):
    initial_amount: float = Field(..., ge=2000, description="Minimum 2000 dhs")
    campaign_id: Optional[str] = None
    alert_threshold: Optional[float] = Field(500, ge=0)
    auto_recharge: bool = False
    auto_recharge_amount: Optional[float] = Field(None, ge=1000)
    payment_method: str = 'manual'
    payment_reference: Optional[str] = None


class RechargeDepositRequest(BaseModel):
    amount: float = Field(..., ge=100, description="Minimum 100 dhs")
    payment_method: str = 'manual'
    payment_reference: Optional[str] = None


class CreateAgreementRequest(BaseModel):
    influencer_id: Optional[str] = None
    commercial_id: Optional[str] = None
    campaign_id: Optional[str] = None
    commission_percentage: float = Field(..., ge=0, le=100)
    minimum_deposit: float = Field(2000, ge=2000)
    quality_threshold: int = Field(7, ge=1, le=10)
    requires_validation: bool = True
    auto_payment: bool = False
    payment_delay_days: int = Field(14, ge=0)


# ============================================
# ROUTER
# ============================================

router = APIRouter(prefix="/api/leads", tags=["Leads System"])


# ============================================
# ENDPOINTS LEADS
# ============================================

@router.post("/create")
async def create_lead(
    request: CreateLeadRequest,
    current_user: dict = Depends(verify_token)
):
    """
    Créer un nouveau lead
    Accessible: influenceurs, commerciaux
    """
    try:
        supabase = get_supabase_client()
        lead_service = LeadService(supabase)
        
        user_id = current_user.get("user_id")
        role = current_user.get("role")
        
        # Récupérer merchant_id depuis la campagne
        campaign = supabase.table('campaigns').select('merchant_id').eq('id', request.campaign_id).single().execute()
        
        if not campaign.data:
            raise HTTPException(status_code=404, detail="Campagne non trouvée")
        
        merchant_id = campaign.data['merchant_id']
        
        # Déterminer influencer_id ou commercial_id
        influencer_id = None
        commercial_id = None
        
        if role == 'influencer':
            # Récupérer influencer_id depuis user_id
            influencer = supabase.table('influencers').select('id').eq('user_id', user_id).single().execute()
            if influencer.data:
                influencer_id = influencer.data['id']
        elif role == 'commercial' or role == 'admin':
            commercial_id = user_id
        else:
            raise HTTPException(status_code=403, detail="Rôle non autorisé")
        
        # Créer le lead
        lead = lead_service.create_lead(
            campaign_id=request.campaign_id,
            merchant_id=merchant_id,
            influencer_id=influencer_id or request.influencer_id,
            commercial_id=commercial_id or request.commercial_id,
            estimated_value=Decimal(str(request.estimated_value)),
            customer_data={
                'customer_name': request.customer_name,
                'customer_email': request.customer_email,
                'customer_phone': request.customer_phone,
                'customer_company': request.customer_company,
                'customer_notes': request.customer_notes,
                'product_id': request.product_id
            },
            source=request.source
        )
        
        return {
            "success": True,
            "lead": lead,
            "message": "Lead créé avec succès"
        }
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        print(f"Erreur create_lead: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{lead_id}")
async def get_lead(
    lead_id: str,
    current_user: dict = Depends(verify_token)
):
    """Récupérer un lead par ID"""
    try:
        supabase = get_supabase_client()
        user_id = current_user.get("user_id")
        role = current_user.get("role")
        
        query = supabase.table('leads').select('*, campaigns(name), merchants(company_name), influencers(user_id)').eq('id', lead_id)
        
        # Filtrer selon le rôle
        if role == 'merchant':
            merchant = supabase.table('merchants').select('id').eq('user_id', user_id).single().execute()
            if merchant.data:
                query = query.eq('merchant_id', merchant.data['id'])
        elif role == 'influencer':
            influencer = supabase.table('influencers').select('id').eq('user_id', user_id).single().execute()
            if influencer.data:
                query = query.eq('influencer_id', influencer.data['id'])
        
        result = query.single().execute()
        
        if not result.data:
            raise HTTPException(status_code=404, detail="Lead non trouvé")
        
        return result.data
        
    except Exception as e:
        print(f"Erreur get_lead: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/campaign/{campaign_id}")
async def get_campaign_leads(
    campaign_id: str,
    status: Optional[str] = None,
    limit: int = Query(100, le=500),
    current_user: dict = Depends(verify_token)
):
    """Récupérer les leads d'une campagne"""
    try:
        supabase = get_supabase_client()
        lead_service = LeadService(supabase)
        
        user_id = current_user.get("user_id")
        role = current_user.get("role")
        
        merchant_id = None
        if role == 'merchant':
            merchant = supabase.table('merchants').select('id').eq('user_id', user_id).single().execute()
            if merchant.data:
                merchant_id = merchant.data['id']
        
        leads = lead_service.get_leads_by_campaign(
            campaign_id,
            merchant_id,
            status,
            limit
        )
        
        return {
            "leads": leads,
            "total": len(leads)
        }
        
    except Exception as e:
        print(f"Erreur get_campaign_leads: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/influencer/my-leads")
async def get_my_leads(
    status: Optional[str] = None,
    limit: int = Query(100, le=500),
    current_user: dict = Depends(verify_token)
):
    """Récupérer les leads d'un influenceur/commercial"""
    try:
        supabase = get_supabase_client()
        lead_service = LeadService(supabase)
        
        user_id = current_user.get("user_id")
        role = current_user.get("role")
        
        if role == 'influencer':
            influencer = supabase.table('influencers').select('id').eq('user_id', user_id).single().execute()
            if not influencer.data:
                raise HTTPException(status_code=404, detail="Profil influenceur non trouvé")
            
            leads = lead_service.get_leads_by_influencer(
                influencer.data['id'],
                status,
                limit
            )
        elif role == 'commercial':
            query = supabase.table('leads').select('*, campaigns(name), merchants(company_name)').eq('commercial_id', user_id)
            if status:
                query = query.eq('status', status)
            result = query.order('created_at', desc=True).limit(limit).execute()
            leads = result.data or []
        else:
            raise HTTPException(status_code=403, detail="Rôle non autorisé")
        
        return {
            "leads": leads,
            "total": len(leads)
        }
        
    except Exception as e:
        print(f"Erreur get_my_leads: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/{lead_id}/validate")
async def validate_lead(
    lead_id: str,
    request: ValidateLeadRequest,
    current_user: dict = Depends(verify_token)
):
    """
    Valider ou rejeter un lead
    Accessible: merchants uniquement
    """
    try:
        require_role(['merchant', 'admin'], current_user)
        
        supabase = get_supabase_client()
        lead_service = LeadService(supabase)
        
        user_id = current_user.get("user_id")
        
        # Récupérer merchant_id
        if current_user.get("role") == 'merchant':
            merchant = supabase.table('merchants').select('id').eq('user_id', user_id).single().execute()
            if not merchant.data:
                raise HTTPException(status_code=404, detail="Profil merchant non trouvé")
            merchant_id = merchant.data['id']
        else:
            # Admin: récupérer merchant_id depuis le lead
            lead = supabase.table('leads').select('merchant_id').eq('id', lead_id).single().execute()
            if not lead.data:
                raise HTTPException(status_code=404, detail="Lead non trouvé")
            merchant_id = lead.data['merchant_id']
        
        # Valider le lead
        updated_lead = lead_service.validate_lead(
            lead_id,
            merchant_id,
            user_id,
            request.status,
            request.quality_score,
            request.feedback,
            request.rejection_reason
        )
        
        return {
            "success": True,
            "lead": updated_lead,
            "message": f"Lead {request.status}"
        }
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        print(f"Erreur validate_lead: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stats/campaign/{campaign_id}")
async def get_campaign_lead_stats(
    campaign_id: str,
    current_user: dict = Depends(verify_token)
):
    """Statistiques des leads d'une campagne"""
    try:
        supabase = get_supabase_client()
        lead_service = LeadService(supabase)
        
        stats = lead_service.get_lead_stats(campaign_id=campaign_id)
        
        return stats
        
    except Exception as e:
        print(f"Erreur get_campaign_lead_stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stats/influencer/my-stats")
async def get_my_influencer_stats(
    current_user: dict = Depends(verify_token)
):
    """Statistiques d'un influenceur/commercial"""
    try:
        require_role(['influencer', 'commercial'], current_user)
        
        supabase = get_supabase_client()
        lead_service = LeadService(supabase)
        
        user_id = current_user.get("user_id")
        role = current_user.get("role")
        
        if role == 'influencer':
            influencer = supabase.table('influencers').select('id').eq('user_id', user_id).single().execute()
            if not influencer.data:
                return {"error": "Profil influenceur non trouvé"}
            
            stats = lead_service.get_lead_stats(influencer_id=influencer.data['id'])
        else:
            # Commercial: filtrer par commercial_id
            stats = lead_service.get_lead_stats()  # À adapter
        
        return stats
        
    except Exception as e:
        print(f"Erreur get_my_influencer_stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================
# ENDPOINTS DEPOSITS
# ============================================

@router.post("/deposits/create")
async def create_deposit(
    request: CreateDepositRequest,
    current_user: dict = Depends(verify_token)
):
    """
    Créer un dépôt prépayé
    Accessible: merchants uniquement
    """
    try:
        require_role(['merchant', 'admin'], current_user)
        
        supabase = get_supabase_client()
        deposit_service = DepositService(supabase)
        
        user_id = current_user.get("user_id")
        
        # Récupérer merchant_id
        merchant = supabase.table('merchants').select('id').eq('user_id', user_id).single().execute()
        if not merchant.data:
            raise HTTPException(status_code=404, detail="Profil merchant non trouvé")
        
        merchant_id = merchant.data['id']
        
        # Créer le dépôt
        deposit = deposit_service.create_deposit(
            merchant_id=merchant_id,
            initial_amount=Decimal(str(request.initial_amount)),
            campaign_id=request.campaign_id,
            alert_threshold=Decimal(str(request.alert_threshold)) if request.alert_threshold else None,
            auto_recharge=request.auto_recharge,
            auto_recharge_amount=Decimal(str(request.auto_recharge_amount)) if request.auto_recharge_amount else None,
            payment_method=request.payment_method,
            payment_reference=request.payment_reference
        )
        
        return {
            "success": True,
            "deposit": deposit,
            "message": "Dépôt créé avec succès"
        }
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        print(f"Erreur create_deposit: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/deposits/{deposit_id}/recharge")
async def recharge_deposit(
    deposit_id: str,
    request: RechargeDepositRequest,
    current_user: dict = Depends(verify_token)
):
    """Recharger un dépôt"""
    try:
        require_role(['merchant', 'admin'], current_user)
        
        supabase = get_supabase_client()
        deposit_service = DepositService(supabase)
        
        user_id = current_user.get("user_id")
        
        merchant = supabase.table('merchants').select('id').eq('user_id', user_id).single().execute()
        if not merchant.data:
            raise HTTPException(status_code=404, detail="Profil merchant non trouvé")
        
        merchant_id = merchant.data['id']
        
        # Recharger
        deposit = deposit_service.recharge_deposit(
            deposit_id,
            merchant_id,
            Decimal(str(request.amount)),
            request.payment_method,
            request.payment_reference,
            user_id
        )
        
        return {
            "success": True,
            "deposit": deposit,
            "message": f"Dépôt rechargé de {request.amount} dhs"
        }
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        print(f"Erreur recharge_deposit: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/deposits/balance")
async def get_my_deposit_balance(
    campaign_id: Optional[str] = None,
    current_user: dict = Depends(verify_token)
):
    """Récupérer le solde du dépôt"""
    try:
        require_role(['merchant', 'admin'], current_user)
        
        supabase = get_supabase_client()
        deposit_service = DepositService(supabase)
        
        user_id = current_user.get("user_id")
        
        merchant = supabase.table('merchants').select('id').eq('user_id', user_id).single().execute()
        if not merchant.data:
            raise HTTPException(status_code=404, detail="Profil merchant non trouvé")
        
        merchant_id = merchant.data['id']
        
        balance = deposit_service.get_deposit_balance(merchant_id, campaign_id)
        
        return balance
        
    except Exception as e:
        print(f"Erreur get_my_deposit_balance: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/deposits/history")
async def get_deposit_history(
    deposit_id: Optional[str] = None,
    transaction_type: Optional[str] = None,
    limit: int = Query(100, le=500),
    current_user: dict = Depends(verify_token)
):
    """Historique des transactions"""
    try:
        require_role(['merchant', 'admin'], current_user)
        
        supabase = get_supabase_client()
        deposit_service = DepositService(supabase)
        
        user_id = current_user.get("user_id")
        
        merchant = supabase.table('merchants').select('id').eq('user_id', user_id).single().execute()
        if not merchant.data:
            raise HTTPException(status_code=404, detail="Profil merchant non trouvé")
        
        merchant_id = merchant.data['id']
        
        history = deposit_service.get_deposit_history(
            merchant_id,
            deposit_id,
            transaction_type,
            limit
        )
        
        return {
            "transactions": history,
            "total": len(history)
        }
        
    except Exception as e:
        print(f"Erreur get_deposit_history: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/deposits/all")
async def get_all_my_deposits(
    status: Optional[str] = None,
    current_user: dict = Depends(verify_token)
):
    """Tous les dépôts d'un merchant"""
    try:
        require_role(['merchant', 'admin'], current_user)
        
        supabase = get_supabase_client()
        deposit_service = DepositService(supabase)
        
        user_id = current_user.get("user_id")
        
        merchant = supabase.table('merchants').select('id').eq('user_id', user_id).single().execute()
        if not merchant.data:
            raise HTTPException(status_code=404, detail="Profil merchant non trouvé")
        
        merchant_id = merchant.data['id']
        
        deposits = deposit_service.get_all_deposits(merchant_id, status)
        
        return {
            "deposits": deposits,
            "total": len(deposits)
        }
        
    except Exception as e:
        print(f"Erreur get_all_my_deposits: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/deposits/stats")
async def get_deposit_stats(
    current_user: dict = Depends(verify_token)
):
    """Statistiques des dépôts"""
    try:
        require_role(['merchant', 'admin'], current_user)
        
        supabase = get_supabase_client()
        deposit_service = DepositService(supabase)
        
        user_id = current_user.get("user_id")
        
        merchant = supabase.table('merchants').select('id').eq('user_id', user_id).single().execute()
        if not merchant.data:
            raise HTTPException(status_code=404, detail="Profil merchant non trouvé")
        
        merchant_id = merchant.data['id']
        
        stats = deposit_service.get_deposit_stats(merchant_id)
        
        return stats
        
    except Exception as e:
        print(f"Erreur get_deposit_stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================
# ENDPOINTS AGREEMENTS
# ============================================

@router.post("/agreements/create")
async def create_agreement(
    request: CreateAgreementRequest,
    current_user: dict = Depends(verify_token)
):
    """Créer un accord influenceur/merchant"""
    try:
        require_role(['merchant', 'admin'], current_user)
        
        supabase = get_supabase_client()
        user_id = current_user.get("user_id")
        
        merchant = supabase.table('merchants').select('id').eq('user_id', user_id).single().execute()
        if not merchant.data:
            raise HTTPException(status_code=404, detail="Profil merchant non trouvé")
        
        merchant_id = merchant.data['id']
        
        if not request.influencer_id and not request.commercial_id:
            raise HTTPException(status_code=400, detail="Influenceur ou commercial requis")
        
        agreement_data = {
            'merchant_id': merchant_id,
            'influencer_id': request.influencer_id,
            'commercial_id': request.commercial_id,
            'campaign_id': request.campaign_id,
            'commission_percentage': request.commission_percentage,
            'minimum_deposit': request.minimum_deposit,
            'quality_threshold': request.quality_threshold,
            'requires_validation': request.requires_validation,
            'auto_payment': request.auto_payment,
            'payment_delay_days': request.payment_delay_days,
            'status': 'pending',
            'signed_by_merchant': True
        }
        
        result = supabase.table('influencer_agreements').insert(agreement_data).execute()
        
        if not result.data:
            raise HTTPException(status_code=500, detail="Erreur création accord")
        
        return {
            "success": True,
            "agreement": result.data[0],
            "message": "Accord créé avec succès"
        }
        
    except Exception as e:
        print(f"Erreur create_agreement: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/agreements/my-agreements")
async def get_my_agreements(
    status: Optional[str] = None,
    current_user: dict = Depends(verify_token)
):
    """Récupérer les accords d'un utilisateur"""
    try:
        supabase = get_supabase_client()
        user_id = current_user.get("user_id")
        role = current_user.get("role")
        
        if role == 'merchant':
            merchant = supabase.table('merchants').select('id').eq('user_id', user_id).single().execute()
            if not merchant.data:
                return {"agreements": [], "total": 0}
            
            query = supabase.table('influencer_agreements').select('*, influencers(user_id), campaigns(name)').eq('merchant_id', merchant.data['id'])
        elif role == 'influencer':
            influencer = supabase.table('influencers').select('id').eq('user_id', user_id).single().execute()
            if not influencer.data:
                return {"agreements": [], "total": 0}
            
            query = supabase.table('influencer_agreements').select('*, merchants(company_name), campaigns(name)').eq('influencer_id', influencer.data['id'])
        else:
            raise HTTPException(status_code=403, detail="Rôle non autorisé")
        
        if status:
            query = query.eq('status', status)
        
        result = query.order('created_at', desc=True).execute()
        agreements = result.data or []
        
        return {
            "agreements": agreements,
            "total": len(agreements)
        }
        
    except Exception as e:
        print(f"Erreur get_my_agreements: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================
# EXPORTER LE ROUTER
# ============================================

def add_leads_endpoints(app, verify_token_func):
    """Ajouter tous les endpoints LEADS à l'application"""
    app.include_router(router)
    print("✅ Endpoints LEADS système intégrés")
