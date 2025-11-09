"""
Service de gestion des dépôts pour génération de leads
Dépôts prépayés, recharges, notifications, historique
"""

from typing import Optional, Dict, List, Any
from datetime import datetime, timedelta
from decimal import Decimal
from uuid import UUID
from supabase import Client


class DepositService:
    """Service pour gérer les dépôts prépayés des entreprises"""
    
    def __init__(self, supabase: Client):
        self.supabase = supabase
        
        # Montants de dépôts prédéfinis
        self.DEPOSIT_TIERS = [2000, 5000, 10000]  # en dhs
        
        # Seuils par défaut
        self.DEFAULT_ALERT_THRESHOLD = Decimal('500.00')  # 500 dhs
        self.CRITICAL_THRESHOLD = Decimal('200.00')  # 200 dhs
    
    
    def create_deposit(
        self,
        merchant_id: str,
        initial_amount: Decimal,
        campaign_id: Optional[str] = None,
        alert_threshold: Optional[Decimal] = None,
        auto_recharge: bool = False,
        auto_recharge_amount: Optional[Decimal] = None,
        payment_method: str = 'manual',
        payment_reference: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Créer un nouveau dépôt prépayé
        
        Args:
            merchant_id: ID du merchant
            initial_amount: Montant initial (minimum 2000 dhs)
            campaign_id: ID de la campagne (optionnel)
            alert_threshold: Seuil d'alerte en dhs (défaut: 500)
            auto_recharge: Activer recharge automatique
            auto_recharge_amount: Montant de la recharge auto
            payment_method: Méthode de paiement
            payment_reference: Référence du paiement
            
        Returns:
            Dépôt créé
        """
        try:
            # Validations
            if initial_amount < 2000:
                raise ValueError("Montant minimum: 2000 dhs")
            
            if initial_amount not in [Decimal(t) for t in self.DEPOSIT_TIERS] and initial_amount < 2000:
                raise ValueError(f"Montants suggérés: {', '.join(str(t) for t in self.DEPOSIT_TIERS)} dhs")
            
            # Données du dépôt
            deposit_data = {
                'merchant_id': merchant_id,
                'campaign_id': campaign_id,
                'initial_amount': float(initial_amount),
                'current_balance': float(initial_amount),
                'reserved_amount': 0.0,
                'alert_threshold': float(alert_threshold or self.DEFAULT_ALERT_THRESHOLD),
                'auto_recharge': auto_recharge,
                'auto_recharge_amount': float(auto_recharge_amount) if auto_recharge_amount else None,
                'status': 'active'
            }
            
            # Créer le dépôt
            result = self.supabase.table('company_deposits').insert(deposit_data).execute()
            
            if not result.data:
                raise Exception("Erreur création dépôt")
            
            deposit = result.data[0]
            
            # Enregistrer la transaction initiale
            self._record_transaction(
                deposit['id'],
                merchant_id,
                'initial',
                initial_amount,
                Decimal('0.00'),
                initial_amount,
                "Dépôt initial",
                payment_method,
                payment_reference
            )
            
            return deposit
            
        except Exception as e:
            print(f"Erreur create_deposit: {e}")
            raise
    
    
    def recharge_deposit(
        self,
        deposit_id: str,
        merchant_id: str,
        amount: Decimal,
        payment_method: str = 'manual',
        payment_reference: Optional[str] = None,
        created_by: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Recharger un dépôt existant
        
        Args:
            deposit_id: ID du dépôt
            merchant_id: ID du merchant
            amount: Montant de la recharge
            payment_method: Méthode de paiement (stripe, cmi, bank_transfer, etc.)
            payment_reference: Référence du paiement
            created_by: ID de l'utilisateur effectuant la recharge
            
        Returns:
            Dépôt mis à jour
        """
        try:
            # Récupérer le dépôt
            deposit = self.supabase.table('company_deposits').select('*').eq('id', deposit_id).eq('merchant_id', merchant_id).single().execute()
            
            if not deposit.data:
                raise ValueError("Dépôt non trouvé")
            
            deposit_data = deposit.data
            current_balance = Decimal(deposit_data['current_balance'])
            new_balance = current_balance + amount
            
            # Mettre à jour le dépôt
            update_data = {
                'current_balance': float(new_balance),
                'status': 'active',  # Réactiver si épuisé
                'updated_at': datetime.now().isoformat()
            }
            
            result = self.supabase.table('company_deposits').update(update_data).eq('id', deposit_id).execute()
            
            if not result.data:
                raise Exception("Erreur mise à jour dépôt")
            
            updated_deposit = result.data[0]
            
            # Enregistrer la transaction
            self._record_transaction(
                deposit_id,
                merchant_id,
                'recharge',
                amount,
                current_balance,
                new_balance,
                f"Recharge du dépôt via {payment_method}",
                payment_method,
                payment_reference,
                created_by
            )
            
            return updated_deposit
            
        except Exception as e:
            print(f"Erreur recharge_deposit: {e}")
            raise
    
    
    def get_deposit_balance(
        self,
        merchant_id: str,
        campaign_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Récupérer le solde d'un dépôt
        
        Args:
            merchant_id: ID du merchant
            campaign_id: ID de la campagne (optionnel)
            
        Returns:
            Informations sur le solde
        """
        try:
            query = self.supabase.table('company_deposits').select('*').eq('merchant_id', merchant_id).eq('status', 'active')
            
            if campaign_id:
                query = query.eq('campaign_id', campaign_id)
            
            result = query.order('created_at', desc=True).limit(1).execute()
            
            if not result.data or len(result.data) == 0:
                return {
                    'has_deposit': False,
                    'current_balance': 0.0,
                    'reserved_amount': 0.0,
                    'available_balance': 0.0,
                    'alert_threshold': float(self.DEFAULT_ALERT_THRESHOLD),
                    'is_low': False,
                    'is_critical': False,
                    'is_depleted': True
                }
            
            deposit = result.data[0]
            current_balance = Decimal(deposit['current_balance'])
            reserved = Decimal(deposit['reserved_amount'] or 0)
            available = current_balance - reserved
            alert_threshold = Decimal(deposit['alert_threshold'])
            
            return {
                'has_deposit': True,
                'deposit_id': deposit['id'],
                'initial_amount': deposit['initial_amount'],
                'current_balance': float(current_balance),
                'reserved_amount': float(reserved),
                'available_balance': float(available),
                'alert_threshold': float(alert_threshold),
                'is_low': current_balance <= alert_threshold,
                'is_critical': current_balance <= self.CRITICAL_THRESHOLD,
                'is_depleted': current_balance <= 0,
                'auto_recharge': deposit.get('auto_recharge', False),
                'status': deposit['status'],
                'created_at': deposit['created_at']
            }
            
        except Exception as e:
            print(f"Erreur get_deposit_balance: {e}")
            return {'has_deposit': False, 'error': str(e)}
    
    
    def get_deposit_history(
        self,
        merchant_id: str,
        deposit_id: Optional[str] = None,
        transaction_type: Optional[str] = None,
        limit: int = 100
    ) -> List[Dict]:
        """
        Récupérer l'historique des transactions
        
        Args:
            merchant_id: ID du merchant
            deposit_id: ID du dépôt (optionnel)
            transaction_type: Type de transaction (optionnel)
            limit: Nombre maximum de résultats
            
        Returns:
            Liste des transactions
        """
        try:
            query = self.supabase.table('deposit_transactions').select('*').eq('merchant_id', merchant_id)
            
            if deposit_id:
                query = query.eq('deposit_id', deposit_id)
            
            if transaction_type:
                query = query.eq('transaction_type', transaction_type)
            
            result = query.order('created_at', desc=True).limit(limit).execute()
            
            return result.data or []
            
        except Exception as e:
            print(f"Erreur get_deposit_history: {e}")
            return []
    
    
    def get_all_deposits(
        self,
        merchant_id: str,
        status: Optional[str] = None
    ) -> List[Dict]:
        """
        Récupérer tous les dépôts d'un merchant
        
        Args:
            merchant_id: ID du merchant
            status: Filtrer par statut (active, depleted, suspended)
            
        Returns:
            Liste des dépôts
        """
        try:
            query = self.supabase.table('company_deposits').select('*').eq('merchant_id', merchant_id)
            
            if status:
                query = query.eq('status', status)
            
            result = query.order('created_at', desc=True).execute()
            
            return result.data or []
            
        except Exception as e:
            print(f"Erreur get_all_deposits: {e}")
            return []
    
    
    def check_low_balances(self) -> List[Dict]:
        """
        Vérifier tous les dépôts avec solde bas
        Utilisé pour les notifications automatiques
        
        Returns:
            Liste des dépôts avec solde bas
        """
        try:
            # Récupérer tous les dépôts actifs
            result = self.supabase.table('company_deposits').select('*').eq('status', 'active').execute()
            
            deposits = result.data or []
            low_deposits = []
            
            for deposit in deposits:
                current_balance = Decimal(deposit['current_balance'])
                alert_threshold = Decimal(deposit['alert_threshold'])
                
                if current_balance <= alert_threshold:
                    # Vérifier si notification récente (pas plus d'une fois par 24h)
                    last_alert = deposit.get('last_alert_sent')
                    should_notify = True
                    
                    if last_alert:
                        last_alert_time = datetime.fromisoformat(last_alert.replace('Z', '+00:00'))
                        hours_since = (datetime.now() - last_alert_time.replace(tzinfo=None)).total_seconds() / 3600
                        should_notify = hours_since >= 24
                    
                    if should_notify:
                        low_deposits.append({
                            **deposit,
                            'is_critical': current_balance <= self.CRITICAL_THRESHOLD,
                            'percentage_remaining': float(current_balance / Decimal(deposit['initial_amount']) * 100)
                        })
            
            return low_deposits
            
        except Exception as e:
            print(f"Erreur check_low_balances: {e}")
            return []
    
    
    def update_alert_threshold(
        self,
        deposit_id: str,
        merchant_id: str,
        new_threshold: Decimal
    ) -> Dict[str, Any]:
        """
        Modifier le seuil d'alerte d'un dépôt
        
        Args:
            deposit_id: ID du dépôt
            merchant_id: ID du merchant
            new_threshold: Nouveau seuil en dhs
            
        Returns:
            Dépôt mis à jour
        """
        try:
            if new_threshold < 0:
                raise ValueError("Seuil doit être positif")
            
            result = self.supabase.table('company_deposits').update({
                'alert_threshold': float(new_threshold),
                'updated_at': datetime.now().isoformat()
            }).eq('id', deposit_id).eq('merchant_id', merchant_id).execute()
            
            if not result.data:
                raise Exception("Dépôt non trouvé")
            
            return result.data[0]
            
        except Exception as e:
            print(f"Erreur update_alert_threshold: {e}")
            raise
    
    
    def configure_auto_recharge(
        self,
        deposit_id: str,
        merchant_id: str,
        enabled: bool,
        recharge_amount: Optional[Decimal] = None
    ) -> Dict[str, Any]:
        """
        Configurer la recharge automatique
        
        Args:
            deposit_id: ID du dépôt
            merchant_id: ID du merchant
            enabled: Activer/désactiver
            recharge_amount: Montant de la recharge auto
            
        Returns:
            Dépôt mis à jour
        """
        try:
            update_data = {
                'auto_recharge': enabled,
                'updated_at': datetime.now().isoformat()
            }
            
            if enabled and recharge_amount:
                if recharge_amount < 1000:
                    raise ValueError("Montant minimum recharge auto: 1000 dhs")
                update_data['auto_recharge_amount'] = float(recharge_amount)
            
            result = self.supabase.table('company_deposits').update(update_data).eq('id', deposit_id).eq('merchant_id', merchant_id).execute()
            
            if not result.data:
                raise Exception("Dépôt non trouvé")
            
            return result.data[0]
            
        except Exception as e:
            print(f"Erreur configure_auto_recharge: {e}")
            raise
    
    
    def suspend_deposit(
        self,
        deposit_id: str,
        merchant_id: str,
        reason: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Suspendre un dépôt (arrêter l'utilisation sans supprimer)
        
        Args:
            deposit_id: ID du dépôt
            merchant_id: ID du merchant
            reason: Raison de la suspension
            
        Returns:
            Dépôt suspendu
        """
        try:
            result = self.supabase.table('company_deposits').update({
                'status': 'suspended',
                'updated_at': datetime.now().isoformat()
            }).eq('id', deposit_id).eq('merchant_id', merchant_id).execute()
            
            if not result.data:
                raise Exception("Dépôt non trouvé")
            
            # Enregistrer dans les transactions
            self._record_transaction(
                deposit_id,
                merchant_id,
                'adjustment',
                Decimal('0.00'),
                Decimal(result.data[0]['current_balance']),
                Decimal(result.data[0]['current_balance']),
                f"Dépôt suspendu: {reason or 'Pas de raison fournie'}"
            )
            
            return result.data[0]
            
        except Exception as e:
            print(f"Erreur suspend_deposit: {e}")
            raise
    
    
    def get_deposit_stats(
        self,
        merchant_id: str,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """
        Statistiques des dépôts d'un merchant
        
        Args:
            merchant_id: ID du merchant
            start_date: Date de début
            end_date: Date de fin
            
        Returns:
            Statistiques
        """
        try:
            # Récupérer tous les dépôts
            deposits = self.get_all_deposits(merchant_id)
            
            # Récupérer toutes les transactions
            transactions = self.get_deposit_history(merchant_id, limit=1000)
            
            # Filtrer par dates si fournies
            if start_date or end_date:
                transactions = [
                    t for t in transactions
                    if (not start_date or datetime.fromisoformat(t['created_at'].replace('Z', '+00:00')) >= start_date)
                    and (not end_date or datetime.fromisoformat(t['created_at'].replace('Z', '+00:00')) <= end_date)
                ]
            
            total_deposited = sum(Decimal(d['initial_amount']) for d in deposits)
            total_current_balance = sum(Decimal(d['current_balance']) for d in deposits if d['status'] == 'active')
            total_reserved = sum(Decimal(d['reserved_amount'] or 0) for d in deposits if d['status'] == 'active')
            
            total_spent = sum(
                abs(Decimal(t['amount']))
                for t in transactions
                if t['transaction_type'] == 'deduction'
            )
            
            total_recharged = sum(
                Decimal(t['amount'])
                for t in transactions
                if t['transaction_type'] == 'recharge'
            )
            
            active_deposits = sum(1 for d in deposits if d['status'] == 'active')
            depleted_deposits = sum(1 for d in deposits if d['status'] == 'depleted')
            
            return {
                'total_deposits': len(deposits),
                'active_deposits': active_deposits,
                'depleted_deposits': depleted_deposits,
                'total_deposited': float(total_deposited),
                'total_current_balance': float(total_current_balance),
                'total_reserved': float(total_reserved),
                'total_available': float(total_current_balance - total_reserved),
                'total_spent': float(total_spent),
                'total_recharged': float(total_recharged),
                'total_transactions': len(transactions),
                'avg_transaction': float(sum(abs(Decimal(t['amount'])) for t in transactions) / len(transactions)) if transactions else 0
            }
            
        except Exception as e:
            print(f"Erreur get_deposit_stats: {e}")
            return {}
    
    
    # ============================================
    # MÉTHODES PRIVÉES
    # ============================================
    
    def _record_transaction(
        self,
        deposit_id: str,
        merchant_id: str,
        transaction_type: str,
        amount: Decimal,
        balance_before: Decimal,
        balance_after: Decimal,
        description: Optional[str] = None,
        payment_method: Optional[str] = None,
        payment_reference: Optional[str] = None,
        created_by: Optional[str] = None
    ):
        """Enregistrer une transaction dans l'historique"""
        try:
            transaction_data = {
                'deposit_id': deposit_id,
                'merchant_id': merchant_id,
                'transaction_type': transaction_type,
                'amount': float(amount),
                'balance_before': float(balance_before),
                'balance_after': float(balance_after),
                'description': description,
                'payment_method': payment_method,
                'payment_reference': payment_reference,
                'created_by': created_by
            }
            
            self.supabase.table('deposit_transactions').insert(transaction_data).execute()
            
        except Exception as e:
            print(f"Erreur _record_transaction: {e}")
