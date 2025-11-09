# 🚀 SYSTÈME ULTRA-AVANCÉ DE GESTION DES LEADS ET PAIEMENTS

## 📊 ARCHITECTURE COMPLÈTE DU SYSTÈME

### 🎯 Principe de fonctionnement

```
MERCHANT (Entreprise)
    ↓ Dépose 5000 dhs
    ↓
COMPTE DÉPÔT (Prépayé)
    ├── Solde: 5000 dhs
    ├── Réservé: 0 dhs
    └── Disponible: 5000 dhs
    
INFLUENCEUR génère LEAD
    ↓ Service 600 dhs → Commission 60 dhs (10%)
    ↓
SYSTÈME RÉSERVE commission
    ├── Solde: 5000 dhs
    ├── Réservé: 60 dhs (pending)
    └── Disponible: 4940 dhs
    
MERCHANT VALIDE lead
    ↓ Approuve qualité 8/10
    ↓
SYSTÈME DÉDUIT du dépôt
    ├── Solde: 4940 dhs (60 dhs déduits)
    ├── Réservé: 0 dhs
    └── Disponible: 4940 dhs
    
INFLUENCEUR reçoit commission
    └── Balance influenceur: +18 dhs (30% de 60 dhs)
```

---

## 🔔 SYSTÈME D'ALERTES MULTI-NIVEAU

### Niveaux d'alerte selon solde

| Seuil | État | Actions automatiques | Notifications |
|-------|------|---------------------|---------------|
| **100% - 51%** | ✅ Sain | Aucune | - |
| **50% - 21%** | 🟡 Attention | Notification info dashboard | Badge jaune |
| **20% - 11%** | 🟠 Critique | Email + Notification push | Badge orange + Email |
| **10% - 1%** | 🔴 Urgence | Email urgent + SMS + Notification | Badge rouge + Email + SMS |
| **0%** | 🚫 Bloqué | **STOP génération leads** + Email + SMS | Campagne PAUSE + Alerte |

### Calcul dynamique des alertes

```python
# backend/services/advanced_alert_service.py

class AdvancedAlertService:
    """Service d'alertes avancé avec niveaux multiples"""
    
    ALERT_LEVELS = {
        'HEALTHY': {'threshold': 0.51, 'color': 'green', 'priority': 0},
        'ATTENTION': {'threshold': 0.50, 'color': 'yellow', 'priority': 1},
        'WARNING': {'threshold': 0.20, 'color': 'orange', 'priority': 2},
        'CRITICAL': {'threshold': 0.10, 'color': 'red', 'priority': 3},
        'DEPLETED': {'threshold': 0.00, 'color': 'black', 'priority': 4}
    }
    
    def get_alert_level(self, current_balance, initial_amount):
        """Déterminer le niveau d'alerte"""
        percentage = current_balance / initial_amount if initial_amount > 0 else 0
        
        if percentage > 0.50:
            return 'HEALTHY'
        elif percentage > 0.20:
            return 'ATTENTION'
        elif percentage > 0.10:
            return 'WARNING'
        elif percentage > 0:
            return 'CRITICAL'
        else:
            return 'DEPLETED'
    
    def should_send_alert(self, deposit, alert_level):
        """Vérifier si alerte doit être envoyée"""
        last_alert = deposit.get('last_alert_level')
        current_level = self.ALERT_LEVELS[alert_level]['priority']
        last_level = self.ALERT_LEVELS.get(last_alert, {}).get('priority', -1)
        
        # Envoyer alerte si niveau aggravé
        return current_level > last_level
    
    def send_multilevel_alert(self, merchant_id, deposit, alert_level):
        """Envoyer alertes selon niveau"""
        
        if alert_level == 'ATTENTION':
            # Notification dashboard uniquement
            self._send_dashboard_notification(
                merchant_id,
                "⚠️ Attention: Solde à 50%",
                f"Votre solde est à {deposit['current_balance']} dhs (50%). Pensez à recharger."
            )
        
        elif alert_level == 'WARNING':
            # Email + Notification
            self._send_email(
                merchant_id,
                "🟠 ALERTE: Solde critique (20%)",
                f"Votre solde est critique: {deposit['current_balance']} dhs. Rechargez rapidement."
            )
            self._send_dashboard_notification(
                merchant_id,
                "🟠 CRITIQUE: Solde à 20%",
                "Action requise: Rechargez votre compte immédiatement"
            )
        
        elif alert_level == 'CRITICAL':
            # Email + SMS + Notification + WhatsApp
            self._send_urgent_email(
                merchant_id,
                "🔴 URGENT: Solde très bas (10%)",
                f"URGENT: Solde restant {deposit['current_balance']} dhs. Génération leads bientôt bloquée!"
            )
            self._send_sms(
                merchant_id,
                f"TRACKNOW ALERTE: Solde {deposit['current_balance']} dhs. Rechargez URGENT!"
            )
            self._send_whatsapp(
                merchant_id,
                f"🚨 Votre solde est critique: {deposit['current_balance']} dhs. Rechargez maintenant!"
            )
        
        elif alert_level == 'DEPLETED':
            # Tout + Blocage système
            self._block_lead_generation(deposit['campaign_id'])
            self._send_critical_email(
                merchant_id,
                "🚫 BLOQUÉ: Solde épuisé",
                "Votre compte est épuisé. Génération de leads ARRÊTÉE. Rechargez immédiatement."
            )
            self._send_sms(
                merchant_id,
                "TRACKNOW: Compte épuisé. Leads BLOQUÉS. Rechargez!"
            )
            self._notify_influencers_pause(deposit['campaign_id'])
```

---

## 💳 SYSTÈME DE PAIEMENT AUTOMATISÉ

### Workflow paiement complet

```
1. MERCHANT clique "Recharger"
    ↓
2. Choix montant: [2000 dhs] [5000 dhs] [10000 dhs] [Personnalisé]
    ↓
3. Choix méthode: [Stripe] [CMI] [Virement] [Crypto]
    ↓
4. Redirection gateway paiement
    ↓
5. Paiement confirmé
    ↓
6. Webhook reçu par système
    ↓
7. AUTOMATIQUE:
    ├── Crédit compte merchant
    ├── Email confirmation + Reçu PDF
    ├── Notification "Compte rechargé"
    ├── Réactivation campagnes si pausées
    └── Enregistrement transaction
```

### Code paiement automatisé

```python
# backend/services/payment_automation_service.py

class PaymentAutomationService:
    """Service de paiement automatisé pour recharges"""
    
    def __init__(self, supabase, stripe_key, cmi_config):
        self.supabase = supabase
        self.stripe = stripe
        self.stripe.api_key = stripe_key
        self.cmi_config = cmi_config
    
    def create_deposit_payment(
        self,
        merchant_id: str,
        amount: Decimal,
        payment_method: str,
        campaign_id: str = None
    ):
        """Créer une intention de paiement"""
        
        if payment_method == 'stripe':
            return self._create_stripe_intent(merchant_id, amount)
        elif payment_method == 'cmi':
            return self._create_cmi_session(merchant_id, amount)
        elif payment_method == 'bank_transfer':
            return self._create_bank_reference(merchant_id, amount)
    
    def _create_stripe_intent(self, merchant_id, amount):
        """Créer PaymentIntent Stripe"""
        intent = self.stripe.PaymentIntent.create(
            amount=int(amount * 100),  # Convertir en centimes
            currency='mad',  # Dirham marocain
            metadata={
                'merchant_id': merchant_id,
                'type': 'deposit_recharge',
                'platform': 'tracknow'
            },
            description=f"Recharge dépôt LEADS - {amount} dhs"
        )
        
        # Enregistrer dans pending_transactions
        self.supabase.table('pending_transactions').insert({
            'merchant_id': merchant_id,
            'payment_intent_id': intent.id,
            'amount': float(amount),
            'payment_method': 'stripe',
            'status': 'pending'
        }).execute()
        
        return intent
    
    def handle_payment_webhook(self, webhook_data):
        """Gérer webhooks de paiement"""
        
        event_type = webhook_data['type']
        
        if event_type == 'payment_intent.succeeded':
            payment_intent = webhook_data['data']['object']
            self._process_successful_payment(payment_intent)
        
        elif event_type == 'payment_intent.payment_failed':
            payment_intent = webhook_data['data']['object']
            self._process_failed_payment(payment_intent)
    
    def _process_successful_payment(self, payment_intent):
        """Traiter paiement réussi"""
        
        merchant_id = payment_intent['metadata']['merchant_id']
        amount = Decimal(payment_intent['amount']) / 100
        
        # 1. Récupérer dépôt actif
        deposit = self._get_active_deposit(merchant_id)
        
        if not deposit:
            # Créer nouveau dépôt si aucun actif
            deposit_service = DepositService(self.supabase)
            deposit = deposit_service.create_deposit(
                merchant_id,
                amount,
                payment_method='stripe',
                payment_reference=payment_intent['id']
            )
        else:
            # Recharger dépôt existant
            deposit_service = DepositService(self.supabase)
            deposit = deposit_service.recharge_deposit(
                deposit['id'],
                merchant_id,
                amount,
                payment_method='stripe',
                payment_reference=payment_intent['id']
            )
        
        # 2. Réactiver campagnes si pausées
        self._reactivate_paused_campaigns(merchant_id)
        
        # 3. Envoyer confirmation
        self._send_payment_confirmation(
            merchant_id,
            amount,
            deposit['current_balance'],
            payment_intent['id']
        )
        
        # 4. Générer reçu PDF
        self._generate_receipt_pdf(
            merchant_id,
            amount,
            payment_intent['id']
        )
        
        # 5. Notification
        notification_service = NotificationService(self.supabase)
        notification_service.send_notification(
            merchant_id,
            "✅ Recharge effectuée",
            f"Votre compte a été crédité de {amount} dhs. Nouveau solde: {deposit['current_balance']} dhs",
            type='payment_success',
            level='success'
        )
    
    def _generate_receipt_pdf(self, merchant_id, amount, reference):
        """Générer reçu PDF automatiquement"""
        from reportlab.lib.pagesizes import letter
        from reportlab.pdfgen import canvas
        
        filename = f"receipt_{reference}.pdf"
        pdf = canvas.Canvas(f"receipts/{filename}", pagesize=letter)
        
        # Header
        pdf.drawString(100, 750, "TRACKNOW.IO - REÇU DE PAIEMENT")
        pdf.drawString(100, 730, f"Référence: {reference}")
        
        # Détails
        pdf.drawString(100, 700, f"Montant: {amount} dhs")
        pdf.drawString(100, 680, f"Date: {datetime.now().strftime('%d/%m/%Y %H:%M')}")
        pdf.drawString(100, 660, f"Méthode: Carte bancaire")
        
        # Merchant
        merchant = self.supabase.table('merchants').select('company_name').eq('id', merchant_id).single().execute()
        pdf.drawString(100, 630, f"Entreprise: {merchant.data['company_name']}")
        
        pdf.save()
        
        # Upload sur S3/Supabase Storage
        self._upload_receipt(filename, merchant_id)
        
        return filename
```

---

## 📊 DASHBOARDS DÉTAILLÉS PAR RÔLE

### 1. DASHBOARD MERCHANT (Entreprise)

#### Widget Solde Dépôt (Card principale)

```jsx
// frontend/src/components/leads/DepositBalanceCard.js

import React, { useEffect, useState } from 'react';
import { CircularProgressbar, buildStyles } from 'react-circular-progressbar';
import 'react-circular-progressbar/dist/styles.css';

const DepositBalanceCard = ({ merchantId }) => {
  const [balance, setBalance] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchBalance();
    // WebSocket pour updates temps réel
    const ws = new WebSocket(`ws://api/deposits/${merchantId}/balance`);
    ws.onmessage = (event) => {
      setBalance(JSON.parse(event.data));
    };
    return () => ws.close();
  }, [merchantId]);

  const fetchBalance = async () => {
    const response = await api.get('/api/leads/deposits/balance');
    setBalance(response.data);
    setLoading(false);
  };

  if (loading) return <div>Chargement...</div>;

  const percentage = (balance.current_balance / balance.initial_amount) * 100;
  const alertLevel = getAlertLevel(percentage);

  return (
    <div className={`card deposit-card alert-${alertLevel.color}`}>
      {/* Header */}
      <div className="card-header">
        <h3>💰 Solde Dépôt</h3>
        <span className={`badge badge-${alertLevel.color}`}>
          {alertLevel.label}
        </span>
      </div>

      {/* Progression circulaire */}
      <div className="balance-visual">
        <CircularProgressbar
          value={percentage}
          text={`${percentage.toFixed(0)}%`}
          styles={buildStyles({
            pathColor: alertLevel.colorHex,
            textColor: alertLevel.colorHex,
            trailColor: '#d6d6d6'
          })}
        />
      </div>

      {/* Montants */}
      <div className="balance-amounts">
        <div className="amount-item">
          <span className="label">Solde actuel</span>
          <span className="value primary">{balance.current_balance} dhs</span>
        </div>
        <div className="amount-item">
          <span className="label">Réservé (leads pending)</span>
          <span className="value secondary">{balance.reserved_amount} dhs</span>
        </div>
        <div className="amount-item">
          <span className="label">Disponible</span>
          <span className="value success">{balance.available_balance} dhs</span>
        </div>
      </div>

      {/* Estimations */}
      <div className="estimates">
        <div className="estimate-item">
          <span>Leads restants estimés</span>
          <span className="value">
            ~{Math.floor(balance.available_balance / 60)} leads
          </span>
        </div>
        <div className="estimate-item">
          <span>Jours restants estimés</span>
          <span className="value">~{estimateDaysRemaining(balance)} jours</span>
        </div>
      </div>

      {/* Alerte si critique */}
      {alertLevel.priority >= 2 && (
        <div className={`alert alert-${alertLevel.color}`}>
          <strong>{alertLevel.icon} {alertLevel.message}</strong>
          <p>{alertLevel.action}</p>
        </div>
      )}

      {/* Actions */}
      <div className="card-actions">
        <button 
          className="btn btn-primary btn-lg"
          onClick={() => openRechargeModal()}
        >
          💳 Recharger maintenant
        </button>
        <button 
          className="btn btn-outline"
          onClick={() => viewHistory()}
        >
          📊 Historique
        </button>
      </div>
    </div>
  );
};

function getAlertLevel(percentage) {
  if (percentage > 50) {
    return {
      color: 'green',
      label: 'Sain',
      priority: 0,
      icon: '✅',
      message: '',
      colorHex: '#10b981'
    };
  } else if (percentage > 20) {
    return {
      color: 'yellow',
      label: 'Attention',
      priority: 1,
      icon: '⚠️',
      message: 'Solde en dessous de 50%',
      action: 'Planifiez une recharge bientôt',
      colorHex: '#f59e0b'
    };
  } else if (percentage > 10) {
    return {
      color: 'orange',
      label: 'Critique',
      priority: 2,
      icon: '🟠',
      message: 'Solde critique!',
      action: 'Rechargez rapidement pour éviter l\'interruption',
      colorHex: '#f97316'
    };
  } else if (percentage > 0) {
    return {
      color: 'red',
      label: 'Urgence',
      priority: 3,
      icon: '🔴',
      message: 'URGENT: Solde très bas!',
      action: 'Rechargez IMMÉDIATEMENT - Génération leads bientôt bloquée',
      colorHex: '#ef4444'
    };
  } else {
    return {
      color: 'black',
      label: 'Épuisé',
      priority: 4,
      icon: '🚫',
      message: 'BLOQUÉ: Solde épuisé',
      action: 'Génération de leads ARRÊTÉE. Rechargez pour réactiver',
      colorHex: '#000000'
    };
  }
}

export default DepositBalanceCard;
```

#### Table Leads en attente de validation

```jsx
// frontend/src/components/leads/PendingLeadsTable.js

const PendingLeadsTable = ({ merchantId }) => {
  const [leads, setLeads] = useState([]);
  const [selectedLead, setSelectedLead] = useState(null);

  return (
    <div className="card">
      <div className="card-header">
        <h3>📋 Leads en attente de validation</h3>
        <span className="badge badge-warning">
          {leads.filter(l => l.status === 'pending').length} à traiter
        </span>
      </div>

      <table className="table">
        <thead>
          <tr>
            <th>Date</th>
            <th>Client</th>
            <th>Contact</th>
            <th>Service</th>
            <th>Valeur estimée</th>
            <th>Commission</th>
            <th>Influenceur</th>
            <th>Source</th>
            <th>Actions</th>
          </tr>
        </thead>
        <tbody>
          {leads.map(lead => (
            <tr key={lead.id} className={`lead-row priority-${getLeadPriority(lead)}`}>
              <td>{formatDate(lead.created_at)}</td>
              <td>
                <strong>{lead.customer_name}</strong>
                {lead.customer_company && (
                  <div className="text-sm text-gray-500">{lead.customer_company}</div>
                )}
              </td>
              <td>
                <div>{lead.customer_email}</div>
                <div className="text-sm">{lead.customer_phone}</div>
              </td>
              <td>{lead.product?.name || 'N/A'}</td>
              <td className="font-bold">{lead.estimated_value} dhs</td>
              <td>
                <span className={`badge badge-${lead.commission_type}`}>
                  {lead.commission_amount} dhs
                  {lead.commission_type === 'percentage' && ' (10%)'}
                  {lead.commission_type === 'fixed' && ' (fixe)'}
                </span>
              </td>
              <td>{lead.influencer?.email}</td>
              <td>
                <span className={`badge badge-source-${lead.source}`}>
                  {lead.source}
                </span>
              </td>
              <td>
                <div className="btn-group">
                  <button
                    className="btn btn-sm btn-success"
                    onClick={() => validateLead(lead.id, 'validated')}
                  >
                    ✅ Valider
                  </button>
                  <button
                    className="btn btn-sm btn-danger"
                    onClick={() => openRejectModal(lead)}
                  >
                    ❌ Rejeter
                  </button>
                  <button
                    className="btn btn-sm btn-info"
                    onClick={() => viewLeadDetails(lead)}
                  >
                    👁️ Détails
                  </button>
                </div>
              </td>
            </tr>
          ))}
        </tbody>
      </table>

      {/* Modal validation détaillée */}
      {selectedLead && (
        <LeadValidationModal
          lead={selectedLead}
          onValidate={handleValidation}
          onClose={() => setSelectedLead(null)}
        />
      )}
    </div>
  );
};
```

---

### 2. DASHBOARD INFLUENCEUR

#### Formulaire génération lead

```jsx
// frontend/src/components/leads/CreateLeadForm.js

const CreateLeadForm = ({ campaignId, influencerId }) => {
  const [formData, setFormData] = useState({
    customer_name: '',
    customer_email: '',
    customer_phone: '',
    customer_company: '',
    estimated_value: '',
    customer_notes: '',
    source: 'instagram'
  });
  const [preview, setPreview] = useState(null);

  // Calcul preview commission en temps réel
  useEffect(() => {
    if (formData.estimated_value) {
      calculateCommissionPreview(formData.estimated_value);
    }
  }, [formData.estimated_value]);

  const calculateCommissionPreview = async (value) => {
    const response = await api.post('/api/leads/preview-commission', {
      estimated_value: value
    });
    setPreview(response.data);
  };

  return (
    <form className="create-lead-form" onSubmit={handleSubmit}>
      <h2>🎯 Générer un nouveau lead</h2>

      {/* Informations client */}
      <div className="form-section">
        <h3>👤 Informations du client</h3>
        
        <div className="form-group">
          <label>Nom complet *</label>
          <input
            type="text"
            value={formData.customer_name}
            onChange={(e) => setFormData({...formData, customer_name: e.target.value})}
            required
            placeholder="Mohamed Bennani"
          />
        </div>

        <div className="form-row">
          <div className="form-group">
            <label>Email *</label>
            <input
              type="email"
              value={formData.customer_email}
              onChange={(e) => setFormData({...formData, customer_email: e.target.value})}
              required
              placeholder="mohamed@example.com"
            />
          </div>
          <div className="form-group">
            <label>Téléphone *</label>
            <input
              type="tel"
              value={formData.customer_phone}
              onChange={(e) => setFormData({...formData, customer_phone: e.target.value})}
              required
              placeholder="+212 6 12 34 56 78"
            />
          </div>
        </div>

        <div className="form-group">
          <label>Entreprise (optionnel)</label>
          <input
            type="text"
            value={formData.customer_company}
            onChange={(e) => setFormData({...formData, customer_company: e.target.value})}
            placeholder="StartupXYZ"
          />
        </div>
      </div>

      {/* Détails service */}
      <div className="form-section">
        <h3>💼 Détails du service</h3>
        
        <div className="form-group">
          <label>Valeur estimée du service (dhs) *</label>
          <input
            type="number"
            min="50"
            value={formData.estimated_value}
            onChange={(e) => setFormData({...formData, estimated_value: e.target.value})}
            required
            placeholder="600"
          />
          <span className="hint">Minimum 50 dhs</span>
        </div>

        {/* Preview commission en temps réel */}
        {preview && (
          <div className="commission-preview">
            <div className="preview-card">
              <h4>💰 Preview commission</h4>
              <div className="preview-details">
                <div className="preview-item">
                  <span>Type:</span>
                  <span className="value">
                    {preview.commission_type === 'percentage' ? '10% (Pourcentage)' : '80 dhs (Fixe)'}
                  </span>
                </div>
                <div className="preview-item">
                  <span>Commission totale:</span>
                  <span className="value primary">{preview.commission_amount} dhs</span>
                </div>
                <div className="preview-item highlight">
                  <span>Votre part (30%):</span>
                  <span className="value success">
                    {(preview.commission_amount * 0.3).toFixed(2)} dhs
                  </span>
                </div>
              </div>
            </div>
          </div>
        )}

        <div className="form-group">
          <label>Source du lead *</label>
          <select
            value={formData.source}
            onChange={(e) => setFormData({...formData, source: e.target.value})}
          >
            <option value="instagram">📷 Instagram</option>
            <option value="tiktok">🎵 TikTok</option>
            <option value="whatsapp">💬 WhatsApp</option>
            <option value="facebook">👍 Facebook</option>
            <option value="direct">📞 Contact direct</option>
            <option value="other">🔗 Autre</option>
          </select>
        </div>

        <div className="form-group">
          <label>Notes complémentaires</label>
          <textarea
            value={formData.customer_notes}
            onChange={(e) => setFormData({...formData, customer_notes: e.target.value})}
            rows="4"
            placeholder="Informations supplémentaires sur le prospect..."
          />
        </div>
      </div>

      {/* Actions */}
      <div className="form-actions">
        <button type="submit" className="btn btn-primary btn-lg">
          🚀 Générer le lead
        </button>
        <button type="button" className="btn btn-outline" onClick={onCancel}>
          Annuler
        </button>
      </div>
    </form>
  );
};
```

---

## 🤖 AUTOMATISATION COMPLÈTE

### Tâches Cron quotidiennes

```python
# backend/scheduler/daily_tasks.py

from apscheduler.schedulers.background import BackgroundScheduler
from services.deposit_service import DepositService
from services.notification_service import NotificationService
from services.lead_service import LeadService

scheduler = BackgroundScheduler()

# Toutes les heures: Vérifier soldes
@scheduler.scheduled_job('interval', hours=1)
def check_deposit_balances():
    """Vérifier tous les soldes et envoyer alertes"""
    deposit_service = DepositService(supabase)
    notification_service = NotificationService(supabase)
    
    low_deposits = deposit_service.check_low_balances()
    
    for deposit in low_deposits:
        alert_level = get_alert_level(deposit)
        
        if alert_level >= 2:  # WARNING ou supérieur
            notification_service.send_multilevel_alert(
                deposit['merchant_id'],
                deposit,
                alert_level
            )

# Tous les jours à 9h: Rapport quotidien
@scheduler.scheduled_job('cron', hour=9)
def send_daily_reports():
    """Envoyer rapports quotidiens aux merchants"""
    merchants = supabase.table('merchants').select('*').execute()
    
    for merchant in merchants.data:
        report = generate_daily_report(merchant['id'])
        send_email_report(merchant['user_id'], report)

# Tous les jours à 23h: Nettoyer leads expirés
@scheduler.scheduled_job('cron', hour=23)
def cleanup_expired_leads():
    """Auto-rejeter leads > 72h sans validation"""
    lead_service = LeadService(supabase)
    expired_leads = lead_service.get_expired_pending_leads()
    
    for lead in expired_leads:
        lead_service.auto_reject_expired(lead['id'])

scheduler.start()
```

---

## 📈 KPIs ET MÉTRIQUES

### Tableau de bord analytique

```python
# backend/services/analytics_service.py

class LeadAnalyticsService:
    """Service d'analytics avancé pour leads"""
    
    def get_merchant_dashboard_metrics(self, merchant_id):
        """Métriques complètes dashboard merchant"""
        
        return {
            'deposits': {
                'current_balance': self._get_current_balance(merchant_id),
                'total_deposited': self._get_total_deposited(merchant_id),
                'total_spent': self._get_total_spent(merchant_id),
                'alert_status': self._get_alert_status(merchant_id),
                'days_remaining_estimate': self._estimate_days_remaining(merchant_id)
            },
            'leads': {
                'total_generated': self._count_leads(merchant_id),
                'pending_validation': self._count_leads(merchant_id, status='pending'),
                'validated': self._count_leads(merchant_id, status='validated'),
                'rejected': self._count_leads(merchant_id, status='rejected'),
                'converted': self._count_leads(merchant_id, status='converted'),
                'validation_rate': self._calc_validation_rate(merchant_id),
                'conversion_rate': self._calc_conversion_rate(merchant_id),
                'avg_quality_score': self._calc_avg_quality(merchant_id),
                'avg_value': self._calc_avg_value(merchant_id)
            },
            'financials': {
                'total_commission_paid': self._calc_total_commissions(merchant_id),
                'avg_commission_per_lead': self._calc_avg_commission(merchant_id),
                'cost_per_acquisition': self._calc_cpa(merchant_id),
                'roi_estimate': self._estimate_roi(merchant_id)
            },
            'trends': {
                'leads_per_day_last_7d': self._get_leads_trend(merchant_id, days=7),
                'validation_rate_trend': self._get_validation_trend(merchant_id),
                'top_influencers': self._get_top_influencers(merchant_id),
                'top_sources': self._get_top_sources(merchant_id)
            }
        }
```

---

**🎯 SYSTÈME COMPLET PRÊT POUR IMPLÉMENTATION !**

Voulez-vous que je commence à implémenter ces dashboards et fonctionnalités ?
