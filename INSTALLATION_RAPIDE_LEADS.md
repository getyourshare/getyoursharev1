# 🚀 INSTALLATION RAPIDE - SYSTÈME LEADS

## ⚡ Démarrage en 5 minutes

### 1️⃣ Installation des dépendances

```bash
cd backend
pip install apscheduler stripe reportlab
```

### 2️⃣ Exécuter migrations SQL

1. Ouvrir **Supabase Dashboard** → **SQL Editor**
2. Copier le contenu de `database/migrations/leads_system.sql`
3. Exécuter
4. Vérifier: "Success. No rows returned"

### 3️⃣ Configurer variables d'environnement

Ajouter dans `backend/.env`:

```env
# Stripe (optionnel pour tests)
STRIPE_SECRET_KEY=sk_test_xxx
STRIPE_WEBHOOK_SECRET=whsec_xxx

# Frontend URL (pour redirections paiement)
FRONTEND_URL=http://localhost:3000
```

### 4️⃣ Démarrer le serveur

```bash
cd backend
python server.py
```

Vérifier le démarrage:
```
✅ Scheduler LEADS démarré avec succès!
   🔄 Vérification dépôts: Toutes les heures
   🧹 Nettoyage leads expirés: 23:00 quotidien
   📊 Rapport quotidien: 09:00 quotidien
```

### 5️⃣ Installer composants frontend

```bash
cd frontend

# Si Ant Design n'est pas installé
npm install antd axios moment
```

Ajouter les imports dans vos pages:

```javascript
// Dans MerchantDashboard.js
import DepositBalanceCard from '../components/leads/DepositBalanceCard';
import PendingLeadsTable from '../components/leads/PendingLeadsTable';

// Dans InfluencerDashboard.js
import CreateLeadForm from '../components/leads/CreateLeadForm';
```

---

## 🧪 TESTER LE SYSTÈME

### Test 1: Créer un dépôt

```bash
curl -X POST http://localhost:8001/api/leads/deposits/create \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "merchant_id": "your-merchant-uuid",
    "initial_amount": 5000.00
  }'
```

### Test 2: Créer un lead

```bash
curl -X POST http://localhost:8001/api/leads/create \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "campaign_id": "your-campaign-uuid",
    "customer_name": "Ahmed Test",
    "customer_email": "ahmed@test.com",
    "customer_phone": "+212 6 12 34 56 78",
    "estimated_value": 1500.00,
    "source": "instagram"
  }'
```

### Test 3: Vérifier le solde

```bash
curl -X GET "http://localhost:8001/api/leads/deposits/balance?merchant_id=your-merchant-uuid" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

### Test 4: Tester le scheduler manuellement

```bash
cd backend
python scheduler/leads_scheduler.py
```

---

## 📊 VÉRIFIER L'INSTALLATION

### ✅ Checklist complète

- [ ] **SQL**: 6 tables créées dans Supabase
  - `leads`
  - `company_deposits`
  - `deposit_transactions`
  - `lead_validation`
  - `influencer_agreements`
  - `campaign_settings`

- [ ] **Backend**: Server démarre sans erreur
  - Message "Scheduler LEADS démarré" visible
  - Swagger docs accessible: http://localhost:8001/docs
  - Endpoints `/api/leads/*` visibles dans docs

- [ ] **Frontend**: Composants compilent
  - Pas d'erreurs npm
  - `DepositBalanceCard.js` existe
  - `PendingLeadsTable.js` existe
  - `CreateLeadForm.js` existe

- [ ] **Scheduler**: Tâches programmées
  - Vérification dépôts: Toutes les heures
  - Nettoyage leads: 23:00 quotidien
  - Rapports: 09:00 quotidien

---

## 🐛 RÉSOLUTION PROBLÈMES

### Erreur: "Import scheduler could not be resolved"
**Solution:** C'est un warning Pylance normal. Le code fonctionne.

### Erreur: "No module named 'apscheduler'"
```bash
pip install apscheduler
```

### Erreur: "No module named 'reportlab'"
```bash
pip install reportlab
```

### Erreur: "stripe.error.AuthenticationError"
**Solution:** Vérifier `STRIPE_SECRET_KEY` dans `.env`

### Scheduler ne démarre pas
**Solution:** Vérifier que le serveur est lancé avec `python server.py` (pas uvicorn directement)

### Frontend: "Cannot read property 'balance'"
**Solution:** Vérifier que le merchant a un dépôt actif

---

## 📖 DOCUMENTATION COMPLÈTE

- **Guide complet:** `SYSTEME_LEADS_FINAL_COMPLET.md`
- **Architecture avancée:** `SYSTEME_LEADS_AVANCE_COMPLET.md`
- **Guide original:** `GUIDE_COMPLET_SYSTEME_LEADS.md`

---

## 🎯 PROCHAINES ÉTAPES

1. **Intégrer dans vos dashboards:**
   - Merchant Dashboard → Ajouter `<DepositBalanceCard />` et `<PendingLeadsTable />`
   - Influencer Dashboard → Ajouter `<CreateLeadForm />`

2. **Configurer Stripe en production:**
   - Remplacer `sk_test_xxx` par `sk_live_xxx`
   - Configurer webhooks: `https://votre-domaine.com/api/webhooks/stripe`

3. **Personnaliser les alertes:**
   - Modifier les seuils dans `leads_scheduler.py`
   - Configurer SMTP pour emails
   - Ajouter Twilio pour SMS

4. **Tester en production:**
   - Créer de vrais dépôts
   - Générer des leads réels
   - Valider les alertes

---

## 💡 BESOIN D'AIDE ?

**Fichiers à consulter:**
- `SYSTEME_LEADS_FINAL_COMPLET.md` - Documentation complète (1000+ lignes)
- `backend/services/lead_service.py` - Logique métier leads
- `backend/scheduler/leads_scheduler.py` - Alertes automatiques
- `frontend/src/components/leads/` - Composants React

**Endpoints principaux:**
- POST `/api/leads/create` - Créer un lead
- PUT `/api/leads/{id}/validate` - Valider un lead
- GET `/api/leads/deposits/balance` - Consulter solde
- POST `/api/leads/deposits/recharge` - Recharger

---

**✨ Tout est prêt ! Le système est 100% fonctionnel.**

Bon développement ! 🚀
