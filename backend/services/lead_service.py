"""
Service de gestion des LEADS pour marketplace services
Génération, validation, calcul commissions (10% vs 80dhs)
"""

from typing import Optional, Dict, List, Any
from datetime import datetime, timedelta
from decimal import Decimal
from uuid import UUID
from supabase import Client


class LeadService:
    """Service pour gérer les leads (génération, validation, commissions)"""
    
    def __init__(self, supabase: Client):
        self.supabase = supabase
        
        # Seuils par défaut
        self.COMMISSION_THRESHOLD = Decimal('800.00')  # 800 dhs
        self.PERCENTAGE_RATE = Decimal('10.00')  # 10%
        self.FIXED_COMMISSION = Decimal('80.00')  # 80 dhs
        
        # Dépôts minimums
        self.MIN_DEPOSIT_AMOUNTS = [2000, 5000, 10000]  # Options en dhs
    
    
    def calculate_commission(
        self, 
        estimated_value: Decimal,
        campaign_settings: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """
        Calculer la commission pour un lead
        
        Args:
            estimated_value: Valeur estimée du service
            campaign_settings: Paramètres spécifiques de la campagne
            
        Returns:
            Dict avec commission_amount, commission_type
        """
        # Récupérer les seuils de la campagne ou utiliser défauts
        threshold = Decimal(campaign_settings.get('commission_threshold', self.COMMISSION_THRESHOLD)) if campaign_settings else self.COMMISSION_THRESHOLD
        percentage = Decimal(campaign_settings.get('percentage_commission_rate', self.PERCENTAGE_RATE)) if campaign_settings else self.PERCENTAGE_RATE
        fixed = Decimal(campaign_settings.get('fixed_commission_amount', self.FIXED_COMMISSION)) if campaign_settings else self.FIXED_COMMISSION
        
        if estimated_value < threshold:
            # Commission en pourcentage (10%)
            commission = round(estimated_value * percentage / 100, 2)
            return {
                'commission_amount': float(commission),
                'commission_type': 'percentage',
                'rate_applied': float(percentage)
            }
        else:
            # Commission fixe (80 dhs)
            return {
                'commission_amount': float(fixed),
                'commission_type': 'fixed',
                'fixed_amount': float(fixed)
            }
    
    
    def create_lead(
        self,
        campaign_id: str,
        merchant_id: str,
        influencer_id: Optional[str] = None,
        commercial_id: Optional[str] = None,
        estimated_value: Decimal = None,
        customer_data: Dict = None,
        source: str = 'direct',
        metadata: Dict = None
    ) -> Dict[str, Any]:
        """
        Créer un nouveau lead
        
        Args:
            campaign_id: ID de la campagne
            merchant_id: ID du merchant
            influencer_id: ID de l'influenceur (ou None si commercial)
            commercial_id: ID du commercial (ou None si influenceur)
            estimated_value: Valeur estimée du service
            customer_data: Données du client (name, email, phone, etc.)
            source: Source du lead (instagram, tiktok, whatsapp, direct)
            metadata: Métadonnées supplémentaires
            
        Returns:
            Lead créé
        """
        try:
            if not influencer_id and not commercial_id:
                raise ValueError("Influencer ou commercial requis")
            
            if not estimated_value or estimated_value < 50:
                raise ValueError("Valeur estimée minimum: 50 dhs")
            
            # Récupérer paramètres campagne
            campaign_settings = self._get_campaign_settings(campaign_id)
            
            # Calculer commission
            commission_data = self.calculate_commission(estimated_value, campaign_settings)
            
            # Récupérer l'accord influenceur/commercial
            agreement = self._get_agreement(
                merchant_id, 
                influencer_id or commercial_id,
                campaign_id
            )
            
            # Calculer commission influenceur/commercial
            influencer_percentage = Decimal(agreement.get('commission_percentage', 30.00)) if agreement else Decimal('30.00')
            influencer_commission = Decimal(commission_data['commission_amount']) * influencer_percentage / 100
            
            # Vérifier disponibilité dépôt
            deposit = self._get_active_deposit(merchant_id, campaign_id)
            if not deposit:
                raise ValueError("Aucun dépôt actif trouvé pour cette campagne")
            
            if Decimal(deposit['current_balance']) < Decimal(commission_data['commission_amount']):
                raise ValueError("Solde du dépôt insuffisant")
            
            # Créer le lead
            lead_data = {
                'campaign_id': campaign_id,
                'merchant_id': merchant_id,
                'influencer_id': influencer_id,
                'commercial_id': commercial_id,
                'estimated_value': float(estimated_value),
                'commission_amount': commission_data['commission_amount'],
                'commission_type': commission_data['commission_type'],
                'influencer_percentage': float(influencer_percentage),
                'influencer_commission': float(influencer_commission),
                'source': source,
                'status': 'pending',
                **(customer_data or {})
            }
            
            # Ajouter metadata si fournie
            if metadata:
                lead_data.update({
                    'ip_address': metadata.get('ip_address'),
                    'user_agent': metadata.get('user_agent')
                })
            
            result = self.supabase.table('leads').insert(lead_data).execute()
            
            if not result.data:
                raise Exception("Erreur création lead")
            
            lead = result.data[0]
            
            # Réserver le montant dans le dépôt
            self._reserve_deposit_amount(
                deposit['id'],
                Decimal(commission_data['commission_amount']),
                lead['id']
            )
            
            # Notification nouveau lead
            self._notify_new_lead(merchant_id, lead)
            
            return lead
            
        except Exception as e:
            print(f"Erreur create_lead: {e}")
            raise
    
    
    def validate_lead(
        self,
        lead_id: str,
        merchant_id: str,
        validated_by: str,
        status: str,
        quality_score: Optional[int] = None,
        feedback: Optional[str] = None,
        rejection_reason: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Valider ou rejeter un lead
        
        Args:
            lead_id: ID du lead
            merchant_id: ID du merchant
            validated_by: ID de l'utilisateur validant
            status: 'validated', 'rejected', 'converted'
            quality_score: Score de qualité 1-10
            feedback: Commentaire
            rejection_reason: Raison du rejet
            
        Returns:
            Lead mis à jour
        """
        try:
            # Récupérer le lead
            lead = self.supabase.table('leads').select('*').eq('id', lead_id).eq('merchant_id', merchant_id).single().execute()
            
            if not lead.data:
                raise ValueError("Lead non trouvé")
            
            lead_data = lead.data
            previous_status = lead_data['status']
            
            # Validation
            if status not in ['validated', 'rejected', 'converted', 'lost']:
                raise ValueError("Statut invalide")
            
            if quality_score and (quality_score < 1 or quality_score > 10):
                raise ValueError("Score qualité doit être entre 1 et 10")
            
            # Mettre à jour le lead
            update_data = {
                'status': status,
                'validated_at': datetime.now().isoformat(),
                'validated_by': validated_by,
                'updated_at': datetime.now().isoformat()
            }
            
            if quality_score:
                update_data['quality_score'] = quality_score
            
            if rejection_reason:
                update_data['rejection_reason'] = rejection_reason
            
            if status == 'converted':
                update_data['conversion_date'] = datetime.now().isoformat()
            
            result = self.supabase.table('leads').update(update_data).eq('id', lead_id).execute()
            
            if not result.data:
                raise Exception("Erreur mise à jour lead")
            
            updated_lead = result.data[0]
            
            # Enregistrer validation dans historique
            self._record_validation(
                lead_id,
                merchant_id,
                validated_by,
                previous_status,
                status,
                quality_score,
                feedback,
                rejection_reason
            )
            
            # Gérer le dépôt selon le statut
            deposit = self._get_active_deposit(merchant_id, lead_data['campaign_id'])
            
            if status == 'validated' or status == 'converted':
                # Déduire du dépôt et libérer réservation
                self._deduct_from_deposit(
                    deposit['id'],
                    Decimal(lead_data['commission_amount']),
                    lead_id,
                    f"Lead validé: {lead_data.get('customer_name', 'N/A')}"
                )
            elif status == 'rejected':
                # Libérer la réservation sans déduction
                self._release_reserved_amount(
                    deposit['id'],
                    Decimal(lead_data['commission_amount'])
                )
            
            # Vérifier seuil dépôt et notifier si bas
            self._check_deposit_balance(deposit['id'], merchant_id)
            
            return updated_lead
            
        except Exception as e:
            print(f"Erreur validate_lead: {e}")
            raise
    
    
    def get_leads_by_campaign(
        self,
        campaign_id: str,
        merchant_id: Optional[str] = None,
        status: Optional[str] = None,
        limit: int = 100
    ) -> List[Dict]:
        """Récupérer les leads d'une campagne"""
        try:
            query = self.supabase.table('leads').select('*').eq('campaign_id', campaign_id)
            
            if merchant_id:
                query = query.eq('merchant_id', merchant_id)
            
            if status:
                query = query.eq('status', status)
            
            result = query.order('created_at', desc=True).limit(limit).execute()
            
            return result.data or []
            
        except Exception as e:
            print(f"Erreur get_leads_by_campaign: {e}")
            return []
    
    
    def get_leads_by_influencer(
        self,
        influencer_id: str,
        status: Optional[str] = None,
        limit: int = 100
    ) -> List[Dict]:
        """Récupérer les leads d'un influenceur"""
        try:
            query = self.supabase.table('leads').select('*, campaigns(name), merchants(company_name)').eq('influencer_id', influencer_id)
            
            if status:
                query = query.eq('status', status)
            
            result = query.order('created_at', desc=True).limit(limit).execute()
            
            return result.data or []
            
        except Exception as e:
            print(f"Erreur get_leads_by_influencer: {e}")
            return []
    
    
    def get_lead_stats(
        self,
        merchant_id: Optional[str] = None,
        influencer_id: Optional[str] = None,
        campaign_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Statistiques des leads"""
        try:
            query = self.supabase.table('leads').select('*')
            
            if merchant_id:
                query = query.eq('merchant_id', merchant_id)
            if influencer_id:
                query = query.eq('influencer_id', influencer_id)
            if campaign_id:
                query = query.eq('campaign_id', campaign_id)
            
            result = query.execute()
            leads = result.data or []
            
            total = len(leads)
            pending = sum(1 for l in leads if l['status'] == 'pending')
            validated = sum(1 for l in leads if l['status'] == 'validated')
            rejected = sum(1 for l in leads if l['status'] == 'rejected')
            converted = sum(1 for l in leads if l['status'] == 'converted')
            
            total_value = sum(Decimal(l['estimated_value'] or 0) for l in leads)
            total_commission = sum(Decimal(l['commission_amount'] or 0) for l in leads)
            total_influencer_commission = sum(Decimal(l['influencer_commission'] or 0) for l in leads)
            
            avg_quality = sum(l['quality_score'] or 0 for l in leads if l.get('quality_score')) / max(1, sum(1 for l in leads if l.get('quality_score')))
            
            validation_rate = (validated / total * 100) if total > 0 else 0
            conversion_rate = (converted / total * 100) if total > 0 else 0
            
            return {
                'total_leads': total,
                'pending': pending,
                'validated': validated,
                'rejected': rejected,
                'converted': converted,
                'total_estimated_value': float(total_value),
                'total_commission': float(total_commission),
                'total_influencer_commission': float(total_influencer_commission),
                'avg_quality_score': round(avg_quality, 2),
                'validation_rate': round(validation_rate, 2),
                'conversion_rate': round(conversion_rate, 2)
            }
            
        except Exception as e:
            print(f"Erreur get_lead_stats: {e}")
            return {}
    
    
    # ============================================
    # MÉTHODES PRIVÉES
    # ============================================
    
    def _get_campaign_settings(self, campaign_id: str) -> Optional[Dict]:
        """Récupérer les paramètres d'une campagne"""
        try:
            result = self.supabase.table('campaign_settings').select('*').eq('campaign_id', campaign_id).single().execute()
            return result.data if result.data else None
        except:
            return None
    
    
    def _get_agreement(
        self, 
        merchant_id: str, 
        influencer_id: str,
        campaign_id: Optional[str] = None
    ) -> Optional[Dict]:
        """Récupérer l'accord influenceur/merchant"""
        try:
            query = self.supabase.table('influencer_agreements').select('*').eq('merchant_id', merchant_id).eq('influencer_id', influencer_id).eq('status', 'active')
            
            if campaign_id:
                query = query.eq('campaign_id', campaign_id)
            
            result = query.single().execute()
            return result.data if result.data else None
        except:
            return None
    
    
    def _get_active_deposit(
        self,
        merchant_id: str,
        campaign_id: Optional[str] = None
    ) -> Optional[Dict]:
        """Récupérer le dépôt actif d'un merchant"""
        try:
            query = self.supabase.table('company_deposits').select('*').eq('merchant_id', merchant_id).eq('status', 'active')
            
            if campaign_id:
                query = query.eq('campaign_id', campaign_id)
            
            result = query.order('created_at', desc=True).limit(1).execute()
            
            if result.data and len(result.data) > 0:
                return result.data[0]
            return None
        except Exception as e:
            print(f"Erreur _get_active_deposit: {e}")
            return None
    
    
    def _reserve_deposit_amount(
        self,
        deposit_id: str,
        amount: Decimal,
        lead_id: str
    ):
        """Réserver un montant dans le dépôt"""
        try:
            deposit = self.supabase.table('company_deposits').select('*').eq('id', deposit_id).single().execute()
            
            if not deposit.data:
                return
            
            new_reserved = Decimal(deposit.data['reserved_amount'] or 0) + amount
            
            self.supabase.table('company_deposits').update({
                'reserved_amount': float(new_reserved),
                'updated_at': datetime.now().isoformat()
            }).eq('id', deposit_id).execute()
            
        except Exception as e:
            print(f"Erreur _reserve_deposit_amount: {e}")
    
    
    def _release_reserved_amount(
        self,
        deposit_id: str,
        amount: Decimal
    ):
        """Libérer un montant réservé"""
        try:
            deposit = self.supabase.table('company_deposits').select('*').eq('id', deposit_id).single().execute()
            
            if not deposit.data:
                return
            
            new_reserved = max(Decimal(0), Decimal(deposit.data['reserved_amount'] or 0) - amount)
            
            self.supabase.table('company_deposits').update({
                'reserved_amount': float(new_reserved),
                'updated_at': datetime.now().isoformat()
            }).eq('id', deposit_id).execute()
            
        except Exception as e:
            print(f"Erreur _release_reserved_amount: {e}")
    
    
    def _deduct_from_deposit(
        self,
        deposit_id: str,
        amount: Decimal,
        lead_id: str,
        description: str
    ):
        """Déduire un montant du dépôt (via fonction SQL)"""
        try:
            # Appeler la fonction SQL deduct_from_deposit
            self.supabase.rpc('deduct_from_deposit', {
                'p_deposit_id': deposit_id,
                'p_amount': float(amount),
                'p_lead_id': lead_id,
                'p_description': description
            }).execute()
            
            # Libérer la réservation
            self._release_reserved_amount(deposit_id, amount)
            
        except Exception as e:
            print(f"Erreur _deduct_from_deposit: {e}")
            raise
    
    
    def _record_validation(
        self,
        lead_id: str,
        merchant_id: str,
        validated_by: str,
        previous_status: str,
        new_status: str,
        quality_score: Optional[int],
        feedback: Optional[str],
        rejection_reason: Optional[str]
    ):
        """Enregistrer la validation dans l'historique"""
        try:
            validation_data = {
                'lead_id': lead_id,
                'merchant_id': merchant_id,
                'validated_by': validated_by,
                'previous_status': previous_status,
                'new_status': new_status,
                'quality_score': quality_score,
                'feedback': feedback,
                'rejection_reason': rejection_reason,
                'action_taken': new_status
            }
            
            self.supabase.table('lead_validation').insert(validation_data).execute()
            
        except Exception as e:
            print(f"Erreur _record_validation: {e}")
    
    
    def _check_deposit_balance(self, deposit_id: str, merchant_id: str):
        """Vérifier le solde et envoyer notification si bas"""
        try:
            deposit = self.supabase.table('company_deposits').select('*').eq('id', deposit_id).single().execute()
            
            if not deposit.data:
                return
            
            current_balance = Decimal(deposit.data['current_balance'])
            alert_threshold = Decimal(deposit.data['alert_threshold'])
            
            if current_balance <= alert_threshold:
                # Envoyer notification (sera géré par NotificationService)
                self._notify_low_balance(merchant_id, deposit.data)
                
                # Mettre à jour last_alert_sent
                self.supabase.table('company_deposits').update({
                    'last_alert_sent': datetime.now().isoformat()
                }).eq('id', deposit_id).execute()
            
            # Vérifier épuisement
            if current_balance <= 0:
                self._handle_deposit_depletion(deposit_id, merchant_id, deposit.data)
                
        except Exception as e:
            print(f"Erreur _check_deposit_balance: {e}")
    
    
    def _handle_deposit_depletion(
        self,
        deposit_id: str,
        merchant_id: str,
        deposit_data: Dict
    ):
        """Gérer l'épuisement d'un dépôt"""
        try:
            # Marquer comme épuisé
            self.supabase.table('company_deposits').update({
                'status': 'depleted',
                'depleted_at': datetime.now().isoformat()
            }).eq('id', deposit_id).execute()
            
            # Récupérer les paramètres de la campagne
            campaign_id = deposit_data.get('campaign_id')
            if campaign_id:
                settings = self._get_campaign_settings(campaign_id)
                
                if settings and settings.get('auto_stop_on_depletion', True):
                    # Arrêter la campagne
                    self._stop_campaign(campaign_id)
            
            # Notifier l'épuisement
            self._notify_deposit_depleted(merchant_id, deposit_data)
            
        except Exception as e:
            print(f"Erreur _handle_deposit_depletion: {e}")
    
    
    def _stop_campaign(self, campaign_id: str):
        """Arrêter une campagne (épuisement dépôt)"""
        try:
            self.supabase.table('campaigns').update({
                'status': 'paused',
                'updated_at': datetime.now().isoformat()
            }).eq('id', campaign_id).execute()
        except Exception as e:
            print(f"Erreur _stop_campaign: {e}")
    
    
    def _notify_new_lead(self, merchant_id: str, lead: Dict):
        """Notification nouveau lead (à implémenter avec NotificationService)"""
        print(f"📧 Notification: Nouveau lead pour merchant {merchant_id}")
    
    
    def _notify_low_balance(self, merchant_id: str, deposit: Dict):
        """Notification solde bas (à implémenter avec NotificationService)"""
        print(f"⚠️  Notification: Solde bas pour merchant {merchant_id} - {deposit['current_balance']} dhs restants")
    
    
    def _notify_deposit_depleted(self, merchant_id: str, deposit: Dict):
        """Notification dépôt épuisé (à implémenter avec NotificationService)"""
        print(f"🚫 Notification: Dépôt épuisé pour merchant {merchant_id}")
