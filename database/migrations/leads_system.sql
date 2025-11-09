-- ============================================
-- SYSTÈME COMPLET DE GÉNÉRATION DE LEADS
-- Pour services marketplace (génération de leads vs ventes directes)
-- ============================================

-- ============================================
-- 1. TABLE LEADS - Leads générés par influenceurs/commerciaux
-- ============================================
CREATE TABLE IF NOT EXISTS leads (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    
    -- Relations
    campaign_id UUID NOT NULL REFERENCES campaigns(id) ON DELETE CASCADE,
    influencer_id UUID REFERENCES influencers(id) ON DELETE SET NULL,
    commercial_id UUID REFERENCES users(id) ON DELETE SET NULL, -- Si commercial
    merchant_id UUID NOT NULL REFERENCES merchants(id) ON DELETE CASCADE,
    product_id UUID REFERENCES products(id) ON DELETE SET NULL,
    
    -- Informations du lead
    customer_name VARCHAR(255),
    customer_email VARCHAR(255),
    customer_phone VARCHAR(50),
    customer_company VARCHAR(255),
    customer_notes TEXT,
    
    -- Tracking
    source VARCHAR(50), -- 'instagram', 'tiktok', 'whatsapp', 'direct'
    ip_address VARCHAR(100),
    user_agent TEXT,
    
    -- Montant et commission
    estimated_value DECIMAL(10, 2) NOT NULL, -- Valeur estimée du service
    commission_amount DECIMAL(10, 2) NOT NULL, -- Commission calculée (10% ou 80dhs)
    commission_type VARCHAR(20) NOT NULL DEFAULT 'percentage', -- 'percentage' ou 'fixed'
    influencer_percentage DECIMAL(5, 2), -- % accordé à l'influenceur/commercial
    influencer_commission DECIMAL(10, 2), -- Commission de l'influenceur
    
    -- Validation et qualité
    status VARCHAR(50) NOT NULL DEFAULT 'pending', -- 'pending', 'validated', 'rejected', 'converted', 'lost'
    quality_score INTEGER CHECK (quality_score BETWEEN 1 AND 10), -- Score qualité 1-10
    rejection_reason TEXT,
    
    -- Validation par merchant
    validated_at TIMESTAMP,
    validated_by UUID REFERENCES users(id),
    conversion_date TIMESTAMP, -- Date de conversion en client
    
    -- Timestamps
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    
    -- Contraintes
    CHECK (influencer_id IS NOT NULL OR commercial_id IS NOT NULL),
    CHECK (estimated_value >= 50), -- Minimum 50 dhs
    CHECK (commission_type IN ('percentage', 'fixed'))
);

-- Index pour performance
CREATE INDEX idx_leads_campaign ON leads(campaign_id);
CREATE INDEX idx_leads_influencer ON leads(influencer_id);
CREATE INDEX idx_leads_merchant ON leads(merchant_id);
CREATE INDEX idx_leads_status ON leads(status);
CREATE INDEX idx_leads_created_at ON leads(created_at);


-- ============================================
-- 2. TABLE COMPANY_DEPOSITS - Dépôts prépayés des entreprises
-- ============================================
CREATE TABLE IF NOT EXISTS company_deposits (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    
    -- Relations
    merchant_id UUID NOT NULL REFERENCES merchants(id) ON DELETE CASCADE,
    campaign_id UUID REFERENCES campaigns(id) ON DELETE SET NULL,
    
    -- Montants
    initial_amount DECIMAL(10, 2) NOT NULL, -- Montant initial du dépôt
    current_balance DECIMAL(10, 2) NOT NULL, -- Solde actuel
    reserved_amount DECIMAL(10, 2) DEFAULT 0, -- Montant réservé pour leads en attente
    
    -- Seuils et alertes
    alert_threshold DECIMAL(10, 2) NOT NULL DEFAULT 500, -- Seuil d'alerte (500 dhs par défaut)
    auto_recharge BOOLEAN DEFAULT FALSE,
    auto_recharge_amount DECIMAL(10, 2),
    
    -- Statut
    status VARCHAR(50) NOT NULL DEFAULT 'active', -- 'active', 'depleted', 'suspended'
    depleted_at TIMESTAMP, -- Date d'épuisement
    last_alert_sent TIMESTAMP, -- Dernière alerte envoyée
    
    -- Timestamps
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    
    -- Contraintes
    CHECK (initial_amount >= 2000), -- Minimum 2000 dhs
    CHECK (current_balance >= 0),
    CHECK (current_balance <= initial_amount),
    CHECK (alert_threshold > 0),
    CHECK (status IN ('active', 'depleted', 'suspended'))
);

-- Index
CREATE INDEX idx_deposits_merchant ON company_deposits(merchant_id);
CREATE INDEX idx_deposits_campaign ON company_deposits(campaign_id);
CREATE INDEX idx_deposits_status ON company_deposits(status);


-- ============================================
-- 3. TABLE DEPOSIT_TRANSACTIONS - Historique des transactions
-- ============================================
CREATE TABLE IF NOT EXISTS deposit_transactions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    
    -- Relations
    deposit_id UUID NOT NULL REFERENCES company_deposits(id) ON DELETE CASCADE,
    merchant_id UUID NOT NULL REFERENCES merchants(id) ON DELETE CASCADE,
    lead_id UUID REFERENCES leads(id) ON DELETE SET NULL,
    
    -- Transaction
    transaction_type VARCHAR(50) NOT NULL, -- 'initial', 'recharge', 'deduction', 'refund', 'adjustment'
    amount DECIMAL(10, 2) NOT NULL,
    balance_before DECIMAL(10, 2) NOT NULL,
    balance_after DECIMAL(10, 2) NOT NULL,
    
    -- Détails
    description TEXT,
    payment_method VARCHAR(50), -- Pour recharges: 'stripe', 'cmi', 'bank_transfer'
    payment_reference VARCHAR(255), -- Référence paiement
    
    -- Metadata
    metadata JSONB, -- Informations supplémentaires
    created_by UUID REFERENCES users(id),
    created_at TIMESTAMP DEFAULT NOW(),
    
    -- Contraintes
    CHECK (transaction_type IN ('initial', 'recharge', 'deduction', 'refund', 'adjustment')),
    CHECK (amount != 0)
);

-- Index
CREATE INDEX idx_transactions_deposit ON deposit_transactions(deposit_id);
CREATE INDEX idx_transactions_merchant ON deposit_transactions(merchant_id);
CREATE INDEX idx_transactions_type ON deposit_transactions(transaction_type);
CREATE INDEX idx_transactions_created ON deposit_transactions(created_at);


-- ============================================
-- 4. TABLE LEAD_VALIDATION - Historique validation/qualité
-- ============================================
CREATE TABLE IF NOT EXISTS lead_validation (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    
    -- Relations
    lead_id UUID NOT NULL REFERENCES leads(id) ON DELETE CASCADE,
    merchant_id UUID NOT NULL REFERENCES merchants(id) ON DELETE CASCADE,
    validated_by UUID NOT NULL REFERENCES users(id),
    
    -- Validation
    previous_status VARCHAR(50),
    new_status VARCHAR(50) NOT NULL,
    quality_score INTEGER CHECK (quality_score BETWEEN 1 AND 10),
    
    -- Feedback
    feedback TEXT,
    rejection_reason VARCHAR(255),
    action_taken VARCHAR(50), -- 'validated', 'rejected', 'requested_info'
    
    -- Timestamps
    created_at TIMESTAMP DEFAULT NOW(),
    
    -- Contraintes
    CHECK (new_status IN ('pending', 'validated', 'rejected', 'converted', 'lost'))
);

-- Index
CREATE INDEX idx_validation_lead ON lead_validation(lead_id);
CREATE INDEX idx_validation_merchant ON lead_validation(merchant_id);
CREATE INDEX idx_validation_created ON lead_validation(created_at);


-- ============================================
-- 5. TABLE INFLUENCER_AGREEMENTS - Accords influenceur/commercial
-- ============================================
CREATE TABLE IF NOT EXISTS influencer_agreements (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    
    -- Parties
    merchant_id UUID NOT NULL REFERENCES merchants(id) ON DELETE CASCADE,
    influencer_id UUID REFERENCES influencers(id) ON DELETE CASCADE,
    commercial_id UUID REFERENCES users(id) ON DELETE CASCADE,
    campaign_id UUID REFERENCES campaigns(id) ON DELETE CASCADE,
    
    -- Termes de l'accord
    commission_percentage DECIMAL(5, 2) NOT NULL, -- % pour l'influenceur/commercial
    minimum_deposit DECIMAL(10, 2) NOT NULL DEFAULT 2000, -- Dépôt minimum requis
    quality_threshold INTEGER DEFAULT 7, -- Score qualité minimum requis
    
    -- Conditions
    requires_validation BOOLEAN DEFAULT TRUE, -- Leads doivent être validés
    auto_payment BOOLEAN DEFAULT FALSE, -- Paiement automatique si validé
    payment_delay_days INTEGER DEFAULT 14, -- Délai de paiement en jours
    
    -- Statut
    status VARCHAR(50) NOT NULL DEFAULT 'pending', -- 'pending', 'active', 'suspended', 'terminated'
    signed_by_merchant BOOLEAN DEFAULT FALSE,
    signed_by_influencer BOOLEAN DEFAULT FALSE,
    termination_reason TEXT,
    
    -- Timestamps
    start_date TIMESTAMP DEFAULT NOW(),
    end_date TIMESTAMP,
    signed_at TIMESTAMP,
    terminated_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    
    -- Contraintes
    CHECK (influencer_id IS NOT NULL OR commercial_id IS NOT NULL),
    CHECK (commission_percentage > 0 AND commission_percentage <= 100),
    CHECK (minimum_deposit >= 2000),
    CHECK (status IN ('pending', 'active', 'suspended', 'terminated'))
);

-- Index
CREATE INDEX idx_agreements_merchant ON influencer_agreements(merchant_id);
CREATE INDEX idx_agreements_influencer ON influencer_agreements(influencer_id);
CREATE INDEX idx_agreements_campaign ON influencer_agreements(campaign_id);
CREATE INDEX idx_agreements_status ON influencer_agreements(status);


-- ============================================
-- 6. TABLE CAMPAIGN_SETTINGS - Paramètres spécifiques campagnes LEADS
-- ============================================
CREATE TABLE IF NOT EXISTS campaign_settings (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    
    -- Relations
    campaign_id UUID NOT NULL UNIQUE REFERENCES campaigns(id) ON DELETE CASCADE,
    merchant_id UUID NOT NULL REFERENCES merchants(id) ON DELETE CASCADE,
    
    -- Type de campagne
    campaign_type VARCHAR(50) NOT NULL DEFAULT 'service_leads', -- 'service_leads', 'product_sales'
    
    -- Paramètres LEADS
    lead_generation_enabled BOOLEAN DEFAULT TRUE,
    auto_stop_on_depletion BOOLEAN DEFAULT TRUE, -- Arrêt auto si dépôt épuisé
    
    -- Seuils de commission
    percentage_commission_rate DECIMAL(5, 2) DEFAULT 10.00, -- 10% pour < 800 dhs
    fixed_commission_amount DECIMAL(10, 2) DEFAULT 80.00, -- 80 dhs pour >= 800 dhs
    commission_threshold DECIMAL(10, 2) DEFAULT 800.00, -- Seuil 800 dhs
    
    -- Validation
    requires_lead_validation BOOLEAN DEFAULT TRUE,
    validation_timeout_hours INTEGER DEFAULT 72, -- 72h pour valider un lead
    auto_validate_after_timeout BOOLEAN DEFAULT FALSE,
    
    -- Qualité
    minimum_quality_score INTEGER DEFAULT 5,
    max_rejected_leads INTEGER DEFAULT 10, -- Max leads rejetés avant suspension
    
    -- Notifications
    notify_on_new_lead BOOLEAN DEFAULT TRUE,
    notify_on_low_balance BOOLEAN DEFAULT TRUE,
    notify_on_depletion BOOLEAN DEFAULT TRUE,
    
    -- Timestamps
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    
    -- Contraintes
    CHECK (campaign_type IN ('service_leads', 'product_sales')),
    CHECK (percentage_commission_rate >= 0 AND percentage_commission_rate <= 100),
    CHECK (fixed_commission_amount >= 0),
    CHECK (commission_threshold > 0)
);

-- Index
CREATE INDEX idx_settings_campaign ON campaign_settings(campaign_id);
CREATE INDEX idx_settings_merchant ON campaign_settings(merchant_id);


-- ============================================
-- 7. VUES UTILES
-- ============================================

-- Vue: Statistiques des leads par campagne
CREATE OR REPLACE VIEW lead_campaign_stats AS
SELECT 
    l.campaign_id,
    c.name AS campaign_name,
    l.merchant_id,
    COUNT(l.id) AS total_leads,
    COUNT(CASE WHEN l.status = 'validated' THEN 1 END) AS validated_leads,
    COUNT(CASE WHEN l.status = 'rejected' THEN 1 END) AS rejected_leads,
    COUNT(CASE WHEN l.status = 'converted' THEN 1 END) AS converted_leads,
    SUM(l.estimated_value) AS total_estimated_value,
    SUM(l.commission_amount) AS total_commission,
    AVG(l.quality_score) AS avg_quality_score,
    MAX(l.created_at) AS last_lead_date
FROM leads l
JOIN campaigns c ON l.campaign_id = c.id
GROUP BY l.campaign_id, c.name, l.merchant_id;

-- Vue: Soldes dépôts par merchant
CREATE OR REPLACE VIEW merchant_deposit_balances AS
SELECT 
    cd.merchant_id,
    m.company_name,
    COUNT(cd.id) AS total_deposits,
    SUM(cd.initial_amount) AS total_deposited,
    SUM(cd.current_balance) AS total_balance,
    SUM(cd.reserved_amount) AS total_reserved,
    SUM(cd.current_balance + cd.reserved_amount) AS available_balance,
    COUNT(CASE WHEN cd.status = 'active' THEN 1 END) AS active_deposits,
    COUNT(CASE WHEN cd.status = 'depleted' THEN 1 END) AS depleted_deposits
FROM company_deposits cd
JOIN merchants m ON cd.merchant_id = m.id
GROUP BY cd.merchant_id, m.company_name;

-- Vue: Performance influenceurs LEADS
CREATE OR REPLACE VIEW influencer_lead_performance AS
SELECT 
    l.influencer_id,
    i.user_id,
    u.email,
    COUNT(l.id) AS total_leads_generated,
    COUNT(CASE WHEN l.status = 'validated' THEN 1 END) AS validated_leads,
    COUNT(CASE WHEN l.status = 'rejected' THEN 1 END) AS rejected_leads,
    COUNT(CASE WHEN l.status = 'converted' THEN 1 END) AS converted_leads,
    ROUND(AVG(l.quality_score), 2) AS avg_quality_score,
    SUM(l.influencer_commission) AS total_earned,
    ROUND(
        COUNT(CASE WHEN l.status = 'validated' THEN 1 END)::DECIMAL / 
        NULLIF(COUNT(l.id), 0) * 100, 
        2
    ) AS validation_rate
FROM leads l
JOIN influencers i ON l.influencer_id = i.id
JOIN users u ON i.user_id = u.id
GROUP BY l.influencer_id, i.user_id, u.email;


-- ============================================
-- 8. FONCTIONS UTILES
-- ============================================

-- Fonction: Calculer la commission d'un lead
CREATE OR REPLACE FUNCTION calculate_lead_commission(
    p_estimated_value DECIMAL,
    p_commission_threshold DECIMAL DEFAULT 800.00,
    p_percentage_rate DECIMAL DEFAULT 10.00,
    p_fixed_amount DECIMAL DEFAULT 80.00
) RETURNS TABLE (
    commission_amount DECIMAL,
    commission_type VARCHAR
) AS $$
BEGIN
    IF p_estimated_value < p_commission_threshold THEN
        -- Commission en pourcentage (10%)
        RETURN QUERY SELECT 
            ROUND(p_estimated_value * p_percentage_rate / 100, 2),
            'percentage'::VARCHAR;
    ELSE
        -- Commission fixe (80 dhs)
        RETURN QUERY SELECT 
            p_fixed_amount,
            'fixed'::VARCHAR;
    END IF;
END;
$$ LANGUAGE plpgsql;

-- Fonction: Déduire commission du dépôt
CREATE OR REPLACE FUNCTION deduct_from_deposit(
    p_deposit_id UUID,
    p_amount DECIMAL,
    p_lead_id UUID DEFAULT NULL,
    p_description TEXT DEFAULT NULL
) RETURNS BOOLEAN AS $$
DECLARE
    v_current_balance DECIMAL;
    v_merchant_id UUID;
BEGIN
    -- Récupérer le solde actuel
    SELECT current_balance, merchant_id 
    INTO v_current_balance, v_merchant_id
    FROM company_deposits 
    WHERE id = p_deposit_id AND status = 'active';
    
    IF NOT FOUND THEN
        RAISE EXCEPTION 'Dépôt non trouvé ou inactif';
    END IF;
    
    IF v_current_balance < p_amount THEN
        RAISE EXCEPTION 'Solde insuffisant';
    END IF;
    
    -- Déduire le montant
    UPDATE company_deposits
    SET 
        current_balance = current_balance - p_amount,
        updated_at = NOW(),
        status = CASE 
            WHEN current_balance - p_amount <= 0 THEN 'depleted'::VARCHAR
            ELSE status 
        END,
        depleted_at = CASE 
            WHEN current_balance - p_amount <= 0 THEN NOW()
            ELSE depleted_at
        END
    WHERE id = p_deposit_id;
    
    -- Enregistrer la transaction
    INSERT INTO deposit_transactions (
        deposit_id,
        merchant_id,
        lead_id,
        transaction_type,
        amount,
        balance_before,
        balance_after,
        description
    ) VALUES (
        p_deposit_id,
        v_merchant_id,
        p_lead_id,
        'deduction',
        -p_amount,
        v_current_balance,
        v_current_balance - p_amount,
        COALESCE(p_description, 'Déduction pour lead généré')
    );
    
    RETURN TRUE;
END;
$$ LANGUAGE plpgsql;

-- Fonction: Recharger un dépôt
CREATE OR REPLACE FUNCTION recharge_deposit(
    p_deposit_id UUID,
    p_amount DECIMAL,
    p_payment_method VARCHAR DEFAULT 'manual',
    p_payment_reference VARCHAR DEFAULT NULL
) RETURNS BOOLEAN AS $$
DECLARE
    v_current_balance DECIMAL;
    v_merchant_id UUID;
BEGIN
    SELECT current_balance, merchant_id
    INTO v_current_balance, v_merchant_id
    FROM company_deposits
    WHERE id = p_deposit_id;
    
    IF NOT FOUND THEN
        RAISE EXCEPTION 'Dépôt non trouvé';
    END IF;
    
    -- Recharger
    UPDATE company_deposits
    SET 
        current_balance = current_balance + p_amount,
        status = 'active',
        updated_at = NOW()
    WHERE id = p_deposit_id;
    
    -- Enregistrer la transaction
    INSERT INTO deposit_transactions (
        deposit_id,
        merchant_id,
        transaction_type,
        amount,
        balance_before,
        balance_after,
        description,
        payment_method,
        payment_reference
    ) VALUES (
        p_deposit_id,
        v_merchant_id,
        'recharge',
        p_amount,
        v_current_balance,
        v_current_balance + p_amount,
        'Recharge du dépôt',
        p_payment_method,
        p_payment_reference
    );
    
    RETURN TRUE;
END;
$$ LANGUAGE plpgsql;


-- ============================================
-- 9. TRIGGERS
-- ============================================

-- Trigger: Auto-update timestamp
CREATE OR REPLACE FUNCTION update_timestamp()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER update_leads_timestamp
    BEFORE UPDATE ON leads
    FOR EACH ROW
    EXECUTE FUNCTION update_timestamp();

CREATE TRIGGER update_deposits_timestamp
    BEFORE UPDATE ON company_deposits
    FOR EACH ROW
    EXECUTE FUNCTION update_timestamp();

CREATE TRIGGER update_agreements_timestamp
    BEFORE UPDATE ON influencer_agreements
    FOR EACH ROW
    EXECUTE FUNCTION update_timestamp();

CREATE TRIGGER update_campaign_settings_timestamp
    BEFORE UPDATE ON campaign_settings
    FOR EACH ROW
    EXECUTE FUNCTION update_timestamp();


-- ============================================
-- 10. DONNÉES DE TEST
-- ============================================

-- Note: À exécuter après avoir des merchants et influencers dans la base

-- Exemple de dépôt
-- INSERT INTO company_deposits (merchant_id, initial_amount, current_balance, alert_threshold)
-- VALUES ('merchant-uuid', 5000.00, 5000.00, 500.00);

-- Exemple d'accord influenceur
-- INSERT INTO influencer_agreements (merchant_id, influencer_id, campaign_id, commission_percentage, minimum_deposit)
-- VALUES ('merchant-uuid', 'influencer-uuid', 'campaign-uuid', 30.00, 2000.00);

-- Exemple de paramètres campagne
-- INSERT INTO campaign_settings (campaign_id, merchant_id, campaign_type)
-- VALUES ('campaign-uuid', 'merchant-uuid', 'service_leads');


-- ============================================
-- PERMISSIONS (RLS - Row Level Security)
-- ============================================

-- Activer RLS sur toutes les tables
ALTER TABLE leads ENABLE ROW LEVEL SECURITY;
ALTER TABLE company_deposits ENABLE ROW LEVEL SECURITY;
ALTER TABLE deposit_transactions ENABLE ROW LEVEL SECURITY;
ALTER TABLE lead_validation ENABLE ROW LEVEL SECURITY;
ALTER TABLE influencer_agreements ENABLE ROW LEVEL SECURITY;
ALTER TABLE campaign_settings ENABLE ROW LEVEL SECURITY;

-- Policies pour leads (merchants voient leurs leads, influenceurs voient les leurs)
CREATE POLICY "Merchants can view their leads"
    ON leads FOR SELECT
    USING (merchant_id IN (SELECT id FROM merchants WHERE user_id = auth.uid()));

CREATE POLICY "Influencers can view their leads"
    ON leads FOR SELECT
    USING (influencer_id IN (SELECT id FROM influencers WHERE user_id = auth.uid()));

-- Policies pour deposits (merchants uniquement)
CREATE POLICY "Merchants can view their deposits"
    ON company_deposits FOR SELECT
    USING (merchant_id IN (SELECT id FROM merchants WHERE user_id = auth.uid()));

CREATE POLICY "Merchants can manage their deposits"
    ON company_deposits FOR ALL
    USING (merchant_id IN (SELECT id FROM merchants WHERE user_id = auth.uid()));

-- Policies pour agreements
CREATE POLICY "Parties can view their agreements"
    ON influencer_agreements FOR SELECT
    USING (
        merchant_id IN (SELECT id FROM merchants WHERE user_id = auth.uid())
        OR influencer_id IN (SELECT id FROM influencers WHERE user_id = auth.uid())
    );

COMMENT ON TABLE leads IS 'Leads générés par influenceurs/commerciaux pour services marketplace';
COMMENT ON TABLE company_deposits IS 'Dépôts prépayés des entreprises pour génération de leads';
COMMENT ON TABLE deposit_transactions IS 'Historique des transactions de dépôts';
COMMENT ON TABLE lead_validation IS 'Historique de validation et qualité des leads';
COMMENT ON TABLE influencer_agreements IS 'Accords entre merchants et influenceurs/commerciaux';
COMMENT ON TABLE campaign_settings IS 'Paramètres spécifiques aux campagnes de génération de leads';
