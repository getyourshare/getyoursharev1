# 🎯 DIFFÉRENCIATION PRODUITS vs SERVICES - MARKETPLACE

## 📊 VUE D'ENSEMBLE

Le marketplace GetYourShare utilise **DEUX systèmes de rémunération distincts** selon le type d'offre :

### 🛍️ PRODUITS → Commission en pourcentage (système actuel)
### 💼 SERVICES → Génération de LEADS avec commission mixte (nouveau système)

---

## 🛍️ SYSTÈME PRODUITS (Commission pourcentage)

### Principe
**Vente directe** de produits physiques ou digitaux avec commission sur le montant de la vente.

### Fonctionnement
```
Client achète → Vente validée → Commission calculée → Influenceur payé
```

### Tarification
- **Commission standard :** 10-25% du prix de vente
- **Variable selon :** 
  - Type de produit
  - Abonnement merchant (FREE/STARTER/PRO/ENTERPRISE)
  - Accord spécifique influenceur/merchant

### Tables utilisées
```sql
- products (type='product')
- sales
- commissions
- payments
```

### Workflow
1. Influenceur partage lien tracking produit
2. Client clique et achète
3. Vente enregistrée avec statut 'pending'
4. Validation après 14 jours
5. Commission créditée à l'influenceur
6. Paiement automatique tous les vendredis (si solde ≥ 50€)

### Exemple
```javascript
Produit: Montre connectée - 500 dhs
Commission merchant: 15%
Commission plateforme: 75 dhs

Répartition:
├── Influenceur: 60 dhs (80% de 75 dhs)
└── Plateforme: 15 dhs (20% de 75 dhs)
```

### Endpoints API actuels
```
POST /api/products (créer produit type='product')
GET /api/sales (voir ventes)
GET /api/commissions (voir commissions)
POST /api/payments/request (demander paiement)
```

---

## 💼 SYSTÈME SERVICES (Génération LEADS)

### Principe
**Génération de prospects qualifiés** pour services à forte valeur. Pas de vente directe, mais des contacts clients potentiels.

### Fonctionnement
```
Influenceur génère lead → Merchant valide qualité → Commission déduite du dépôt → Influenceur payé
```

### Tarification DOUBLE
| Valeur service | Commission | Type |
|---------------|------------|------|
| 50 - 799 dhs | **10%** | Pourcentage |
| ≥ 800 dhs | **80 dhs** | Fixe |

**Pourquoi ce modèle ?**
- Services chers se vendent moins → Commission fixe = prévisibilité
- Services abordables → 10% reste rentable
- Équilibre entre volume et rentabilité

### Dépôt prépayé OBLIGATOIRE
```
Montants disponibles:
├── 2,000 dhs (Basic)
├── 5,000 dhs (Pro)
└── 10,000 dhs (Enterprise)
```

### Tables spécifiques
```sql
- products (type='service')
- leads
- company_deposits
- deposit_transactions
- lead_validation
- influencer_agreements
- campaign_settings
```

### Workflow
1. **Merchant** crée dépôt (min 2000 dhs)
2. **Merchant** propose accord à influenceur (% commission)
3. **Influenceur** génère lead (formulaire client)
4. **Commission réservée** automatiquement dans dépôt
5. **Merchant** valide lead (score qualité 1-10)
6. **Commission déduite** du dépôt si validé
7. **Notification** solde bas si < 500 dhs
8. **Arrêt auto** campagne si dépôt épuisé

### Exemple 1: Service coaching (400 dhs)
```javascript
Service: Coaching marketing digital - 400 dhs
Commission: 40 dhs (10% car < 800 dhs)
Accord influenceur: 30%

Répartition:
├── Influenceur: 12 dhs (30% de 40 dhs)
└── Plateforme: 28 dhs

Lead généré → Réservation 40 dhs du dépôt
Lead validé → Déduction 40 dhs, balance: 4960 dhs
```

### Exemple 2: Service immobilier (3000 dhs)
```javascript
Service: Transaction immobilière - 3000 dhs
Commission: 80 dhs (FIXE car ≥ 800 dhs)
Accord influenceur: 40%

Répartition:
├── Influenceur: 32 dhs (40% de 80 dhs)
└── Plateforme: 48 dhs

Lead généré → Réservation 80 dhs du dépôt
Lead validé → Déduction 80 dhs, balance: 4920 dhs
```

### Endpoints API LEADS
```
POST /api/leads/create (générer lead)
PUT /api/leads/{id}/validate (valider/rejeter)
POST /api/leads/deposits/create (créer dépôt)
POST /api/leads/deposits/{id}/recharge (recharger)
GET /api/leads/deposits/balance (voir solde)
GET /api/leads/stats/campaign/{id} (statistiques)
```

---

## 🔀 DIFFÉRENCES CLÉS

| Critère | PRODUITS | SERVICES |
|---------|----------|----------|
| **Objectif** | Vente directe | Génération prospects |
| **Commission** | Pourcentage uniquement | Mixte (10% ou 80 dhs) |
| **Paiement** | Après validation vente | Déduit dépôt prépayé |
| **Validation** | 14 jours automatique | Manuelle par merchant |
| **Dépôt** | ❌ Non requis | ✅ Obligatoire (2000+ dhs) |
| **Notifications** | Vente validée | Solde bas, dépôt épuisé |
| **Arrêt auto** | ❌ Non | ✅ Si dépôt épuisé |
| **Qualité** | Note produit | Score lead 1-10 |
| **Tables** | sales, commissions | leads, deposits |

---

## 🎨 DÉTECTION AUTOMATIQUE

### Dans `products` table

```sql
CREATE TABLE products (
    id UUID PRIMARY KEY,
    name VARCHAR(255),
    type VARCHAR(50) NOT NULL, -- 'product' ou 'service'
    price DECIMAL(10, 2),
    commission_rate DECIMAL(5, 2), -- Pour produits
    commission_type VARCHAR(20), -- 'percentage', 'fixed', 'mixed'
    -- ...
    CHECK (type IN ('product', 'service'))
);
```

### Logique dans le code

```python
# services/commission_service.py

def calculate_commission(product_id: str, amount: Decimal):
    product = get_product(product_id)
    
    if product['type'] == 'product':
        # Système PRODUITS (pourcentage)
        commission_rate = Decimal(product['commission_rate'])
        return amount * commission_rate / 100
    
    elif product['type'] == 'service':
        # Système SERVICES (10% ou 80 dhs)
        if amount < 800:
            return amount * Decimal('10.00') / 100  # 10%
        else:
            return Decimal('80.00')  # Fixe
```

### Frontend - Création campagne

```javascript
// frontend/src/pages/campaigns/CreateCampaign.js

const [productType, setProductType] = useState('product');

<FormSelect
  label="Type d'offre"
  value={productType}
  onChange={(e) => setProductType(e.target.value)}
>
  <option value="product">🛍️ Produit (vente directe)</option>
  <option value="service">💼 Service (génération leads)</option>
</FormSelect>

{productType === 'service' && (
  <Alert variant="info">
    <strong>Dépôt requis:</strong> Minimum 2000 dhs pour campagnes services.
    Commission: 10% jusqu'à 799 dhs, puis 80 dhs fixe.
  </Alert>
)}
```

---

## 📱 EXEMPLE COMPLET D'UTILISATION

### Cas 1: E-commerce (Produits)

**Merchant:** Boutique de vêtements  
**Type:** Produits  
**Commission:** 15% sur toutes ventes

```javascript
// Créer produit
POST /api/products
{
  "name": "Robe d'été",
  "type": "product",
  "price": 350,
  "commission_rate": 15
}

// Vente
Influenceur partage lien → Client achète 350 dhs
→ Commission: 52.5 dhs (15%)
→ Influenceur reçoit: 42 dhs (80% de 52.5)
→ Validé après 14 jours
→ Paiement vendredi suivant si solde ≥ 50€
```

### Cas 2: Coaching (Services)

**Merchant:** Coach business  
**Type:** Services  
**Services:** 400 dhs - 1500 dhs  
**Dépôt initial:** 5000 dhs

```javascript
// Créer dépôt
POST /api/leads/deposits/create
{
  "initial_amount": 5000,
  "alert_threshold": 500
}

// Créer accord avec influenceur
POST /api/leads/agreements/create
{
  "influencer_id": "inf_123",
  "commission_percentage": 35
}

// Influenceur génère leads
Lead 1: Service 400 dhs → Commission 40 dhs (10%)
  → Influenceur: 14 dhs (35%)
  → Dépôt: 4960 dhs

Lead 2: Service 1200 dhs → Commission 80 dhs (fixe)
  → Influenceur: 28 dhs (35%)
  → Dépôt: 4880 dhs

...après 60 leads...

Dépôt: 450 dhs → ⚠️ Notification solde bas
Merchant recharge: +3000 dhs → Solde: 3450 dhs
Campagne continue...
```

---

## 🔧 CONFIGURATION PAR CAMPAGNE

### Table `campaign_settings`

```sql
INSERT INTO campaign_settings (
    campaign_id,
    merchant_id,
    campaign_type, -- 'service_leads' ou 'product_sales'
    lead_generation_enabled,
    auto_stop_on_depletion,
    percentage_commission_rate,
    fixed_commission_amount,
    commission_threshold
) VALUES (
    'campaign_services_123',
    'merchant_abc',
    'service_leads', -- ✅ SERVICES
    true,
    true, -- Arrêt auto si dépôt épuisé
    10.00, -- 10%
    80.00, -- 80 dhs
    800.00 -- Seuil
);

INSERT INTO campaign_settings (
    campaign_id,
    merchant_id,
    campaign_type
) VALUES (
    'campaign_products_456',
    'merchant_abc',
    'product_sales' -- ✅ PRODUITS
);
```

---

## 📊 DASHBOARDS DIFFÉRENCIÉS

### Dashboard Merchant - Produits
```
📦 MES PRODUITS
├── 45 produits actifs
├── 128 ventes ce mois
├── 6,420 dhs de commissions
└── Taux conversion: 3.2%

💰 PROCHAINS PAIEMENTS
└── 890 dhs validés (paiement vendredi)
```

### Dashboard Merchant - Services
```
💼 MES SERVICES
├── 8 services actifs
├── 67 leads générés ce mois
├── 42 leads validés (62%)
└── Score qualité moyen: 7.8/10

💳 DÉPÔTS
├── Solde actuel: 2,340 dhs
├── Réservé: 240 dhs
├── Disponible: 2,100 dhs
└── ⚠️ Rechargez bientôt (seuil: 500 dhs)
```

### Dashboard Influenceur - Mixte
```
🎯 MES PERFORMANCES

PRODUITS (15 actifs)
├── 23 ventes validées
└── 680 dhs gagnés

SERVICES (5 campagnes)
├── 34 leads générés
├── 28 validés (82%)
├── Score qualité: 8.2/10
└── 420 dhs gagnés

TOTAL: 1,100 dhs disponibles
```

---

## ✅ CHECKLIST IMPLÉMENTATION

### Produits (Existant)
- [x] Table `products` avec type='product'
- [x] Table `sales`
- [x] Table `commissions`
- [x] Commission pourcentage
- [x] Validation 14 jours
- [x] Paiement automatique vendredi

### Services (Nouveau - LEADS)
- [x] Table `products` avec type='service'
- [x] Table `leads`
- [x] Table `company_deposits`
- [x] Table `deposit_transactions`
- [x] Table `lead_validation`
- [x] Table `influencer_agreements`
- [x] Table `campaign_settings`
- [x] LeadService (commission 10% vs 80 dhs)
- [x] DepositService (dépôts, recharges)
- [x] NotificationService (alertes)
- [x] 15+ endpoints API
- [x] Repositories

### Frontend à créer
- [ ] Page création produit/service (sélecteur type)
- [ ] Page gestion dépôts (merchants services)
- [ ] Page validation leads (merchants services)
- [ ] Page mes leads (influenceurs services)
- [ ] Dashboard différencié produits/services
- [ ] Notifications temps réel
- [ ] Composant alerte solde bas

---

## 🎯 RÉSUMÉ FINAL

| Aspect | PRODUITS | SERVICES |
|--------|----------|----------|
| **Icône** | 🛍️ | 💼 |
| **But** | Vendre | Générer prospects |
| **Commission** | % variable | 10% ou 80 dhs |
| **Dépôt** | Non | Oui (2000+ dhs) |
| **Validation** | Auto 14j | Manuelle + score |
| **Paiement** | Vendredi auto | Déduit dépôt |
| **Système** | `sales` | `leads` |
| **Arrêt** | Jamais | Si dépôt épuisé |

**Les deux systèmes coexistent dans la même plateforme mais utilisent des tables et workflows différents.**

---

📚 **Voir aussi:**
- `GUIDE_COMPLET_SYSTEME_LEADS.md` - Documentation complète LEADS
- `SYSTEME_REMUNERATION_MARKETPLACE.md` - Commission produits
- `database/migrations/leads_system.sql` - Tables LEADS
- `backend/services/lead_service.py` - Service LEADS
