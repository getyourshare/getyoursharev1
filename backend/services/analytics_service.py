"""
Service Analytics pour système LEADS
KPIs, métriques et statistiques avancées
"""

from decimal import Decimal
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from supabase import Client


class AnalyticsService:
    """Service d'analytics pour le système LEADS"""
    
    def __init__(self, supabase_client: Client):
        self.supabase = supabase_client
    
    def get_merchant_kpis(self, merchant_id: str, period_days: int = 30) -> Dict:
        """
        KPIs complets pour un merchant
        
        Retourne:
        - Total leads reçus
        - Taux de validation
        - Taux de conversion
        - Dépenses totales
        - ROI estimé
        - Qualité moyenne des leads
        """
        start_date = (datetime.now() - timedelta(days=period_days)).isoformat()
        
        # Récupérer tous les leads
        leads_response = self.supabase.table('leads')\
            .select('*')\
            .eq('merchant_id', merchant_id)\
            .gte('created_at', start_date)\
            .execute()
        
        leads = leads_response.data if leads_response.data else []
        
        if not leads:
            return {
                'total_leads': 0,
                'validated_leads': 0,
                'rejected_leads': 0,
                'converted_leads': 0,
                'pending_leads': 0,
                'validation_rate': 0,
                'conversion_rate': 0,
                'total_spent': 0,
                'avg_quality_score': 0,
                'avg_lead_value': 0,
                'period_days': period_days
            }
        
        # Calculer les métriques
        total_leads = len(leads)
        validated = [l for l in leads if l['status'] == 'validated']
        rejected = [l for l in leads if l['status'] == 'rejected']
        converted = [l for l in leads if l['status'] == 'converted']
        pending = [l for l in leads if l['status'] == 'pending']
        
        validation_rate = (len(validated) / total_leads * 100) if total_leads > 0 else 0
        conversion_rate = (len(converted) / len(validated) * 100) if len(validated) > 0 else 0
        
        total_spent = sum(float(l['commission_amount']) for l in validated)
        avg_quality = sum(l.get('quality_score', 0) for l in validated) / len(validated) if validated else 0
        avg_value = sum(float(l['estimated_value']) for l in leads) / total_leads if total_leads > 0 else 0
        
        return {
            'total_leads': total_leads,
            'validated_leads': len(validated),
            'rejected_leads': len(rejected),
            'converted_leads': len(converted),
            'pending_leads': len(pending),
            'validation_rate': round(validation_rate, 2),
            'conversion_rate': round(conversion_rate, 2),
            'total_spent': round(total_spent, 2),
            'avg_quality_score': round(avg_quality, 2),
            'avg_lead_value': round(avg_value, 2),
            'period_days': period_days
        }
    
    def get_influencer_kpis(self, influencer_id: str, period_days: int = 30) -> Dict:
        """
        KPIs complets pour un influenceur
        
        Retourne:
        - Total leads générés
        - Taux de validation
        - Commissions gagnées
        - Commissions en attente
        - Meilleure campagne
        - Qualité moyenne
        """
        start_date = (datetime.now() - timedelta(days=period_days)).isoformat()
        
        # Récupérer tous les leads
        leads_response = self.supabase.table('leads')\
            .select('*, campaigns(name)')\
            .eq('influencer_id', influencer_id)\
            .gte('created_at', start_date)\
            .execute()
        
        leads = leads_response.data if leads_response.data else []
        
        if not leads:
            return {
                'total_leads': 0,
                'validated_leads': 0,
                'rejected_leads': 0,
                'pending_leads': 0,
                'validation_rate': 0,
                'total_earned': 0,
                'pending_earnings': 0,
                'avg_quality_score': 0,
                'best_campaign': None,
                'period_days': period_days
            }
        
        total_leads = len(leads)
        validated = [l for l in leads if l['status'] == 'validated']
        rejected = [l for l in leads if l['status'] == 'rejected']
        pending = [l for l in leads if l['status'] == 'pending']
        
        validation_rate = (len(validated) / total_leads * 100) if total_leads > 0 else 0
        
        total_earned = sum(float(l.get('influencer_commission', 0)) for l in validated)
        pending_earnings = sum(float(l.get('influencer_commission', 0)) for l in pending)
        
        avg_quality = sum(l.get('quality_score', 0) for l in validated) / len(validated) if validated else 0
        
        # Meilleure campagne
        campaigns_performance = {}
        for lead in validated:
            campaign_id = lead['campaign_id']
            commission = float(lead.get('influencer_commission', 0))
            
            if campaign_id not in campaigns_performance:
                campaigns_performance[campaign_id] = {
                    'name': lead.get('campaigns', {}).get('name', 'N/A'),
                    'total_commission': 0,
                    'count': 0
                }
            
            campaigns_performance[campaign_id]['total_commission'] += commission
            campaigns_performance[campaign_id]['count'] += 1
        
        best_campaign = None
        if campaigns_performance:
            best_campaign = max(campaigns_performance.values(), key=lambda x: x['total_commission'])
        
        return {
            'total_leads': total_leads,
            'validated_leads': len(validated),
            'rejected_leads': len(rejected),
            'pending_leads': len(pending),
            'validation_rate': round(validation_rate, 2),
            'total_earned': round(total_earned, 2),
            'pending_earnings': round(pending_earnings, 2),
            'avg_quality_score': round(avg_quality, 2),
            'best_campaign': best_campaign,
            'period_days': period_days
        }
    
    def get_campaign_performance(self, campaign_id: str) -> Dict:
        """
        Performance détaillée d'une campagne
        
        Retourne:
        - Nombre de leads
        - Taux de validation
        - Coût total
        - Top influenceurs
        - Timeline
        """
        # Récupérer tous les leads de la campagne
        leads_response = self.supabase.table('leads')\
            .select('*, influencers(user_id), users(email)')\
            .eq('campaign_id', campaign_id)\
            .execute()
        
        leads = leads_response.data if leads_response.data else []
        
        if not leads:
            return {
                'total_leads': 0,
                'validated_leads': 0,
                'total_cost': 0,
                'avg_quality': 0,
                'top_influencers': [],
                'daily_breakdown': []
            }
        
        validated = [l for l in leads if l['status'] == 'validated']
        total_cost = sum(float(l['commission_amount']) for l in validated)
        avg_quality = sum(l.get('quality_score', 0) for l in validated) / len(validated) if validated else 0
        
        # Top influenceurs
        influencer_performance = {}
        for lead in validated:
            inf_id = lead.get('influencer_id')
            if not inf_id:
                continue
            
            if inf_id not in influencer_performance:
                influencer_performance[inf_id] = {
                    'email': lead.get('users', {}).get('email', 'N/A'),
                    'leads_count': 0,
                    'total_commission': 0
                }
            
            influencer_performance[inf_id]['leads_count'] += 1
            influencer_performance[inf_id]['total_commission'] += float(lead.get('influencer_commission', 0))
        
        top_influencers = sorted(
            influencer_performance.values(), 
            key=lambda x: x['leads_count'], 
            reverse=True
        )[:5]
        
        # Timeline (7 derniers jours)
        daily_breakdown = []
        for i in range(7):
            date = (datetime.now() - timedelta(days=i)).date()
            date_str = date.isoformat()
            
            day_leads = [l for l in leads if l['created_at'][:10] == date_str]
            day_validated = [l for l in day_leads if l['status'] == 'validated']
            
            daily_breakdown.append({
                'date': date_str,
                'total_leads': len(day_leads),
                'validated_leads': len(day_validated)
            })
        
        return {
            'total_leads': len(leads),
            'validated_leads': len(validated),
            'total_cost': round(total_cost, 2),
            'avg_quality': round(avg_quality, 2),
            'top_influencers': top_influencers,
            'daily_breakdown': daily_breakdown[::-1]  # Ordre chronologique
        }
    
    def get_platform_overview(self) -> Dict:
        """
        Vue d'ensemble de la plateforme (Admin)
        
        Retourne:
        - Total leads générés
        - Total commissions payées
        - Dépôts actifs vs épuisés
        - Top merchants
        - Top influenceurs
        """
        # Total leads
        total_leads_response = self.supabase.table('leads')\
            .select('*', count='exact')\
            .execute()
        
        total_leads = total_leads_response.count if hasattr(total_leads_response, 'count') else 0
        
        # Leads validés
        validated_response = self.supabase.table('leads')\
            .select('commission_amount', count='exact')\
            .eq('status', 'validated')\
            .execute()
        
        validated_count = validated_response.count if hasattr(validated_response, 'count') else 0
        total_commissions = sum(float(l['commission_amount']) for l in (validated_response.data or []))
        
        # Dépôts
        deposits_response = self.supabase.table('company_deposits')\
            .select('*')\
            .execute()
        
        deposits = deposits_response.data if deposits_response.data else []
        active_deposits = len([d for d in deposits if d['status'] == 'active'])
        depleted_deposits = len([d for d in deposits if d['status'] == 'depleted'])
        total_deposited = sum(float(d['initial_amount']) for d in deposits)
        total_remaining = sum(float(d['current_balance']) for d in deposits if d['status'] == 'active')
        
        return {
            'total_leads': total_leads,
            'validated_leads': validated_count,
            'total_commissions_paid': round(total_commissions, 2),
            'active_deposits': active_deposits,
            'depleted_deposits': depleted_deposits,
            'total_deposited': round(total_deposited, 2),
            'total_remaining': round(total_remaining, 2),
            'platform_revenue': round(total_commissions * 0.1, 2)  # 10% platform fee (exemple)
        }
    
    def get_deposit_forecast(self, deposit_id: str) -> Dict:
        """
        Prévision d'épuisement d'un dépôt
        
        Analyse les 7 derniers jours pour estimer:
        - Dépense quotidienne moyenne
        - Jours restants avant épuisement
        - Date estimée d'épuisement
        """
        # Récupérer le dépôt
        deposit_response = self.supabase.table('company_deposits')\
            .select('*')\
            .eq('id', deposit_id)\
            .execute()
        
        if not deposit_response.data:
            return None
        
        deposit = deposit_response.data[0]
        current_balance = float(deposit['current_balance'])
        
        # Récupérer les transactions des 7 derniers jours
        seven_days_ago = (datetime.now() - timedelta(days=7)).isoformat()
        
        transactions_response = self.supabase.table('deposit_transactions')\
            .select('*')\
            .eq('deposit_id', deposit_id)\
            .eq('transaction_type', 'deduction')\
            .gte('created_at', seven_days_ago)\
            .execute()
        
        transactions = transactions_response.data if transactions_response.data else []
        
        if not transactions:
            return {
                'current_balance': current_balance,
                'avg_daily_spend': 0,
                'days_remaining': 'N/A',
                'estimated_depletion_date': None,
                'warning': 'Pas assez de données pour prévoir'
            }
        
        # Calculer la dépense moyenne quotidienne
        total_spent = sum(abs(float(t['amount'])) for t in transactions)
        avg_daily_spend = total_spent / 7
        
        # Calculer les jours restants
        days_remaining = (current_balance / avg_daily_spend) if avg_daily_spend > 0 else float('inf')
        
        # Date estimée d'épuisement
        if days_remaining != float('inf'):
            depletion_date = datetime.now() + timedelta(days=days_remaining)
            depletion_date_str = depletion_date.strftime('%Y-%m-%d')
        else:
            depletion_date_str = None
        
        return {
            'current_balance': round(current_balance, 2),
            'avg_daily_spend': round(avg_daily_spend, 2),
            'days_remaining': round(days_remaining, 1) if days_remaining != float('inf') else 'Illimité',
            'estimated_depletion_date': depletion_date_str,
            'recommended_recharge': round(avg_daily_spend * 30, 2)  # 30 jours de buffer
        }
