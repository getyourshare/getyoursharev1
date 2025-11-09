# 💰 SYSTÈME DE RÉMUNÉRATION - MARKETPLACE GETYOURSHARE

**Date:** 8 novembre 2025  
**Version:** 2.0

---

## 🎯 VUE D'ENSEMBLE

Le système de rémunération de la marketplace GetYourShare fonctionne selon un **modèle à 3 parties** :

1. **Client** → Achète un produit
2. **Marchand** → Vend le produit et paie une commission à la plateforme
3. **Influenceur** → Génère la vente et reçoit une commission du marchand

---

## 💸 FLUX DE L'ARGENT

```
┌─────────────────────────────────────────────────────────────────┐
│                        CLIENT ACHÈTE                             │
│                  100€ pour un produit                            │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│                     MARCHAND REÇOIT                              │
│                         100€                                     │
│                                                                  │
│  Le marchand doit payer 2 commissions :                         │
│  ├─ Commission Influenceur : 10-25% (selon négociation)         │
│  └─ Commission Plateforme : 5% (selon abonnement)               │
└────────────────────┬────────────────┬───────────────────────────┘
                     │                │
                     ▼                ▼
         ┌───────────────┐  ┌──────────────────┐
         │  INFLUENCEUR  │  │   PLATEFORME     │
         │   Reçoit      │  │    Reçoit        │
         │   15€ (15%)   │  │    5€ (5%)       │
         └───────────────┘  └──────────────────┘
```

---

## 📊 DÉTAIL DES COMMISSIONS

### 1️⃣ **Commission de l'Influenceur**

**Qui paie ?** Le **Marchand**  
**Taux ?** Entre **10% et 25%** du montant de la vente  
**Négociable ?** ✅ Oui, défini lors de la création de la campagne

#### Exemple :
- Vente : **100€**
- Commission influenceur : **15%**
- Influenceur reçoit : **15€**

#### Stockage dans la base de données :
```sql
-- Table: sales
{
  "id": "sale_123",
  "product_id": "prod_456",
  "merchant_id": "merchant_789",
  "influencer_id": "inf_101",
  "sale_amount": 100.00,
  "commission_rate": 15.00,        -- Taux négocié
  "commission_amount": 15.00,      -- Calculé automatiquement
  "status": "completed"
}
```

---

### 2️⃣ **Commission de la Plateforme**

**Qui paie ?** Le **Marchand**  
**Taux ?** Entre **1% et 5%** selon l'abonnement du marchand  
**Négociable ?** ❌ Non, défini par le plan d'abonnement

#### Barème selon l'abonnement :

| Plan Marchand | Commission Plateforme | Frais Mensuels |
|---------------|----------------------|----------------|
| **FREE** | 5% | 0€ |
| **STARTER** | 3% | 29€/mois |
| **PRO** | 2% | 99€/mois |
| **ENTERPRISE** | 1% | Sur devis |

#### Exemple avec un marchand PRO :
- Vente : **100€**
- Commission plateforme : **2%**
- Plateforme reçoit : **2€**

#### Stockage dans la base de données :
```sql
-- Table: merchants
{
  "id": "merchant_789",
  "company_name": "ElectroMaroc",
  "subscription_plan": "pro",
  "commission_rate": 2.00,         -- Frais plateforme selon le plan
  "total_commission_paid": 450.00  -- Historique cumulé
}
```

---

### 3️⃣ **Récapitulatif d'une Vente**

Pour une vente de **100€** avec un marchand **PRO** et commission influenceur **15%** :

| Partie | Montant | Calcul |
|--------|---------|--------|
| **Client paie** | 100€ | Prix du produit |
| **Marchand reçoit brut** | 100€ | Paiement client |
| **Commission influenceur** | -15€ | 100€ × 15% |
| **Commission plateforme** | -2€ | 100€ × 2% |
| **Marchand garde net** | **83€** | 100€ - 15€ - 2€ |
| **Influenceur reçoit** | **15€** | Sa commission |
| **Plateforme reçoit** | **2€** | Frais de service |

---

## 🔄 PROCESSUS DE PAIEMENT

### Étape 1 : Vente Réalisée

```javascript
// Le webhook du marchand signale une vente
POST /api/webhook/shopify/{merchant_id}
{
  "order_id": "12345",
  "total": 100.00,
  "customer_email": "client@example.com",
  "items": [...]
}
```

### Étape 2 : Attribution & Calcul

```python
# Le système attribue la vente à l'influenceur
# via le cookie de tracking (30 jours)

sale_data = {
    "merchant_id": merchant_id,
    "influencer_id": influencer_id,  # Trouvé via le tracking
    "product_id": product_id,
    "sale_amount": 100.00,
    "commission_rate": 15.00,        # Taux de la campagne
    "commission_amount": 15.00,      # 100 * 0.15
    "platform_fee": 2.00,            # 100 * 0.02 (plan PRO)
    "status": "pending"              # En attente de validation
}
```

### Étape 3 : Validation (14 jours)

```python
# Après 14 jours sans retour, la vente est validée
auto_payment_service.validate_pending_sales()

# Status passe de "pending" à "completed"
# Le solde de l'influenceur est crédité
```

### Étape 4 : Paiement Influenceur

```python
# L'influenceur peut demander un retrait
# Montant minimum : 50€ (configurable)

payout_request = {
    "influencer_id": influencer_id,
    "amount": 150.00,              # Solde disponible
    "payment_method": "paypal",    # ou "bank_transfer", "mobile_money"
    "status": "pending"
}

# Le paiement est traité automatiquement chaque vendredi
auto_payment_service.process_automatic_payouts()
```

---

## 💳 MÉTHODES DE PAIEMENT DISPONIBLES

### Pour les Influenceurs (Recevoir l'argent)

#### 1. **PayPal**
```json
{
  "method": "paypal",
  "details": {
    "email": "influencer@example.com"
  }
}
```

#### 2. **Virement Bancaire (SEPA)**
```json
{
  "method": "bank_transfer",
  "details": {
    "iban": "FR7630006000011234567890189",
    "account_name": "Hassan Oudrhiri",
    "bank_name": "Banque Populaire"
  }
}
```

#### 3. **Mobile Money Maroc** 🇲🇦
```json
{
  "method": "mobile_money",
  "details": {
    "provider": "orange_money",  // ou "inwi_money", "cash_plus"
    "phone_number": "+212698765432"
  }
}
```

---

### Pour les Marchands (Payer la Plateforme)

#### 1. **Carte Bancaire (Stripe)**
- Paiement automatique mensuel
- Prélèvement des commissions

#### 2. **Virement Bancaire Manuel**
- Facture générée automatiquement
- Paiement sous 30 jours

#### 3. **CMI / PayZen / SG Maroc** 🇲🇦
- Paiements locaux marocains
- Intégration directe avec les banques

---

## 📈 SYSTÈME DE FACTURATION

### Facturation Plateforme → Marchand

**Fréquence :** Mensuelle  
**Contenu :** Commission sur les ventes du mois

#### Structure de la Facture :

```
═══════════════════════════════════════════════════════════
                    FACTURE #INV-2025-11-0001
═══════════════════════════════════════════════════════════

Marchand : ElectroMaroc
Période  : 1-30 novembre 2025
Plan     : PRO (2% commission)

───────────────────────────────────────────────────────────
DÉTAIL DES VENTES
───────────────────────────────────────────────────────────
Date        Produit              Montant    Commission 2%
───────────────────────────────────────────────────────────
2025-11-05  iPhone 15           899.00€    17.98€
2025-11-12  MacBook Pro         2,499.00€  49.98€
2025-11-20  AirPods Pro         279.00€    5.58€
───────────────────────────────────────────────────────────

TOTAL VENTES                    3,677.00€
COMMISSION PLATEFORME (2%)        73.54€
TVA (20%)                         14.71€
───────────────────────────────────────────────────────────
MONTANT TOTAL DÛ                  88.25€

Échéance : 30 décembre 2025
═══════════════════════════════════════════════════════════
```

#### Base de Données :

```sql
-- Table: platform_invoices
{
  "id": "inv_123",
  "merchant_id": "merchant_789",
  "invoice_number": "INV-2025-11-0001",
  "period_start": "2025-11-01",
  "period_end": "2025-11-30",
  "total_sales_amount": 3677.00,
  "platform_commission": 73.54,
  "tax_amount": 14.71,
  "total_amount": 88.25,
  "status": "pending",
  "due_date": "2025-12-30"
}

-- Table: invoice_line_items (détail des ventes)
[
  {
    "invoice_id": "inv_123",
    "sale_id": "sale_456",
    "description": "iPhone 15",
    "sale_amount": 899.00,
    "commission_rate": 2.00,
    "commission_amount": 17.98
  },
  ...
]
```

---

## 🤖 AUTOMATISATION DES PAIEMENTS

### 1. Validation Automatique des Ventes

**Quand ?** Tous les jours à **2h00 du matin**

```python
# Valide les ventes de plus de 14 jours
@scheduler.scheduled_job('cron', hour=2, minute=0)
def validate_sales():
    auto_payment_service.validate_pending_sales()
```

**Résultat :**
- Ventes passent de `pending` → `completed`
- Solde de l'influenceur crédité
- Notification envoyée

---

### 2. Paiements Automatiques Hebdomadaires

**Quand ?** Tous les **vendredis à 10h00**

```python
# Traite tous les paiements en attente
@scheduler.scheduled_job('cron', day_of_week='fri', hour=10, minute=0)
def process_payouts():
    auto_payment_service.process_automatic_payouts()
```

**Conditions :**
- Solde ≥ 50€ (montant minimum)
- Méthode de paiement configurée
- Influenceur actif

**Actions :**
1. Crée un payout dans la base
2. Transfère l'argent (PayPal, virement, mobile money)
3. Déduit du solde de l'influenceur
4. Envoie une notification

---

### 3. Rappels de Paiement (Marchands)

**Quand ?** Tous les **lundis à 9h00**

```python
# Rappelle les factures impayées
@scheduler.scheduled_job('cron', day_of_week='mon', hour=9, minute=0)
def send_payment_reminders():
    # Factures en retard > 7 jours
    overdue_invoices = get_overdue_invoices()
    for invoice in overdue_invoices:
        send_email_reminder(invoice)
```

---

## 📊 TRACKING DES COMMISSIONS

### Interface Influenceur

```javascript
// Dashboard influenceur
GET /api/influencer/earnings

Response:
{
  "total_earnings": 1250.50,      // Total des commissions
  "available_balance": 450.00,    // Disponible pour retrait
  "pending_balance": 800.50,      // En attente de validation
  "total_withdrawn": 2000.00,     // Déjà retiré
  "this_month": 320.00,           // Ce mois
  "commission_rate": 3.00,        // Taux selon plan (PRO = 3%)
  "next_payout_date": "2025-11-15"
}
```

### Interface Marchand

```javascript
// Dashboard marchand
GET /api/merchant/commissions

Response:
{
  "total_sales": 15430.00,         // Total ventes
  "platform_commission": 308.60,   // Commission plateforme (2%)
  "influencer_commission": 2314.50, // Commission influenceurs (15% avg)
  "net_revenue": 12806.90,         // Revenu net
  "pending_invoices": [
    {
      "invoice_number": "INV-2025-11-0001",
      "amount": 88.25,
      "due_date": "2025-12-30",
      "status": "pending"
    }
  ]
}
```

---

## 💡 AVANTAGES DU SYSTÈME

### Pour les Influenceurs ✨

✅ **Commissions attractives** : 10-25% par vente  
✅ **Paiements automatiques** : Chaque vendredi  
✅ **Plusieurs méthodes** : PayPal, virement, mobile money  
✅ **Tracking en temps réel** : Dashboard complet  
✅ **Montant minimum faible** : 50€  
✅ **Délai court** : 14 jours de validation  

### Pour les Marchands 📈

✅ **Pas de frais fixes élevés** : Plans à partir de 0€  
✅ **Commission variable** : 1-5% selon abonnement  
✅ **Facturation claire** : Factures mensuelles détaillées  
✅ **Plusieurs gateways** : Stripe, CMI, PayZen, SG Maroc  
✅ **Automatisation complète** : Calcul et facturation auto  

### Pour la Plateforme 🚀

✅ **Revenus récurrents** : Abonnements + commissions  
✅ **Scalable** : Système automatisé  
✅ **Transparent** : Tracking complet  
✅ **Flexible** : S'adapte aux besoins locaux (Maroc)  

---

## 🔧 CONFIGURATION

### Paramètres de la Plateforme

```sql
-- Table: settings
INSERT INTO settings (key, value, description) VALUES
('min_payout_amount', '50', 'Montant minimum pour un paiement (€)'),
('validation_delay_days', '14', 'Délai de validation des ventes (jours)'),
('payout_day', 'friday', 'Jour des paiements automatiques'),
('default_commission_rate', '15', 'Taux de commission par défaut (%)'),
('platform_currency', 'EUR', 'Devise de la plateforme');
```

### Frais par Méthode de Paiement

```python
# Mobile Money Maroc
MOBILE_PAYMENT_FEES = {
    "orange_money": 2.0,   # 2%
    "inwi_money": 2.5,     # 2.5%
    "cash_plus": 1.5       # 1.5%
}

# Calcul du net
amount = 100.00
fee = amount * 0.02  # 2€
net_amount = amount - fee  # 98€
```

---

## 📝 RÉSUMÉ

**Le système fonctionne ainsi :**

1. **Client achète** → Marchand reçoit le paiement complet
2. **Commission influenceur** → 10-25% du montant (payé par marchand)
3. **Commission plateforme** → 1-5% du montant (payé par marchand)
4. **Validation** → Automatique après 14 jours
5. **Paiement influenceurs** → Automatique chaque vendredi
6. **Facturation marchands** → Mensuelle avec détail des ventes

**Exemple concret :**
```
Vente de 100€
├─ Client paie : 100€
├─ Marchand reçoit : 100€
│  ├─ Paie influenceur : -15€ (15%)
│  ├─ Paie plateforme : -2€ (2%)
│  └─ Garde : 83€
├─ Influenceur reçoit : 15€
└─ Plateforme reçoit : 2€
```

---

**Pour plus d'informations :**
- Configuration technique : `backend/payment_service.py`
- Facturation : `backend/invoicing_service.py`
- Paiements automatiques : `backend/auto_payment_service.py`
- Paiements mobiles Maroc : `backend/mobile_payment_service.py`

**Date de mise à jour :** 8 novembre 2025
