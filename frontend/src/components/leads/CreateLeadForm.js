import React, { useState, useEffect } from 'react';
import { 
  Form, 
  Input, 
  InputNumber, 
  Select, 
  Button, 
  Card, 
  message, 
  Statistic, 
  Alert,
  Divider 
} from 'antd';
import { 
  UserAddOutlined, 
  DollarOutlined, 
  CalculatorOutlined,
  SendOutlined 
} from '@ant-design/icons';
import axios from 'axios';

const { Option } = Select;
const { TextArea } = Input;

/**
 * Formulaire de création de lead - Dashboard Influenceur
 * 
 * Permet aux influenceurs de:
 * - Créer un nouveau lead pour une campagne
 * - Saisir les informations du client
 * - Voir le preview de la commission en temps réel
 * - Valider la disponibilité du dépôt merchant
 */
const CreateLeadForm = ({ influencerId }) => {
  const [form] = Form.useForm();
  const [loading, setLoading] = useState(false);
  const [campaigns, setCampaigns] = useState([]);
  const [selectedCampaign, setSelectedCampaign] = useState(null);
  const [estimatedValue, setEstimatedValue] = useState(0);
  const [commissionPreview, setCommissionPreview] = useState(null);
  const [depositAvailable, setDepositAvailable] = useState(true);

  useEffect(() => {
    loadActiveCampaigns();
  }, [influencerId]);

  useEffect(() => {
    if (estimatedValue > 0 && selectedCampaign) {
      calculateCommission();
    }
  }, [estimatedValue, selectedCampaign]);

  const loadActiveCampaigns = async () => {
    try {
      const token = localStorage.getItem('token');
      const response = await axios.get('/api/campaigns/active', {
        headers: { Authorization: `Bearer ${token}` },
        params: { 
          type: 'service_leads',
          status: 'active'
        }
      });
      
      setCampaigns(response.data.campaigns || []);
    } catch (error) {
      console.error('Erreur chargement campagnes:', error);
      message.error('Impossible de charger les campagnes');
    }
  };

  const calculateCommission = async () => {
    try {
      const token = localStorage.getItem('token');
      const response = await axios.post('/api/leads/calculate-commission', {
        campaign_id: selectedCampaign.id,
        estimated_value: estimatedValue
      }, {
        headers: { Authorization: `Bearer ${token}` }
      });

      setCommissionPreview(response.data);
      setDepositAvailable(response.data.deposit_available);
    } catch (error) {
      console.error('Erreur calcul commission:', error);
      setCommissionPreview(null);
    }
  };

  const handleSubmit = async (values) => {
    if (!depositAvailable) {
      message.error('Le merchant n\'a pas assez de solde pour ce lead');
      return;
    }

    setLoading(true);
    try {
      const token = localStorage.getItem('token');
      const response = await axios.post('/api/leads/create', {
        campaign_id: values.campaign_id,
        customer_name: values.customer_name,
        customer_email: values.customer_email,
        customer_phone: values.customer_phone,
        customer_company: values.customer_company,
        customer_notes: values.customer_notes,
        estimated_value: values.estimated_value,
        source: values.source
      }, {
        headers: { Authorization: `Bearer ${token}` }
      });

      message.success('Lead créé avec succès! En attente de validation merchant.');
      form.resetFields();
      setEstimatedValue(0);
      setCommissionPreview(null);
      
      // Afficher un récapitulatif
      message.info(`Vous gagnerez ${response.data.lead.influencer_commission} dhs si validé`);
    } catch (error) {
      console.error('Erreur création lead:', error);
      message.error(error.response?.data?.detail || 'Échec de la création du lead');
    } finally {
      setLoading(false);
    }
  };

  return (
    <Card
      title={
        <span>
          <UserAddOutlined /> Créer un nouveau lead
        </span>
      }
      extra={
        <span style={{ fontSize: 14, fontWeight: 'normal', color: '#888' }}>
          Remplissez les informations du client potentiel
        </span>
      }
    >
      <Form
        form={form}
        layout="vertical"
        onFinish={handleSubmit}
        initialValues={{
          source: 'instagram'
        }}
      >
        {/* Sélection campagne */}
        <Form.Item
          name="campaign_id"
          label="Campagne"
          rules={[{ required: true, message: 'Sélectionnez une campagne' }]}
        >
          <Select
            placeholder="Choisissez une campagne active"
            size="large"
            onChange={(value) => {
              const campaign = campaigns.find(c => c.id === value);
              setSelectedCampaign(campaign);
            }}
          >
            {campaigns.map(campaign => (
              <Option key={campaign.id} value={campaign.id}>
                <div>
                  <strong>{campaign.name}</strong>
                  <div style={{ fontSize: 12, color: '#888' }}>
                    {campaign.merchant_company} - Commission: {campaign.commission_rate}%
                  </div>
                </div>
              </Option>
            ))}
          </Select>
        </Form.Item>

        <Divider>Informations du client</Divider>

        {/* Nom du client */}
        <Form.Item
          name="customer_name"
          label="Nom complet"
          rules={[
            { required: true, message: 'Nom requis' },
            { min: 3, message: 'Minimum 3 caractères' }
          ]}
        >
          <Input 
            placeholder="Ex: Ahmed Bennani" 
            size="large"
          />
        </Form.Item>

        {/* Email et Téléphone */}
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16 }}>
          <Form.Item
            name="customer_email"
            label="Email"
            rules={[
              { required: true, message: 'Email requis' },
              { type: 'email', message: 'Email invalide' }
            ]}
          >
            <Input 
              placeholder="client@email.com" 
              size="large"
              type="email"
            />
          </Form.Item>

          <Form.Item
            name="customer_phone"
            label="Téléphone"
            rules={[
              { required: true, message: 'Téléphone requis' },
              { pattern: /^(\+212|0)[5-7]\d{8}$/, message: 'Format: +212XXXXXXXXX ou 06XXXXXXXX' }
            ]}
          >
            <Input 
              placeholder="+212 6 XX XX XX XX" 
              size="large"
            />
          </Form.Item>
        </div>

        {/* Entreprise (optionnel) */}
        <Form.Item
          name="customer_company"
          label="Entreprise (optionnel)"
        >
          <Input 
            placeholder="Nom de l'entreprise du client" 
            size="large"
          />
        </Form.Item>

        <Divider>Détails du service</Divider>

        {/* Valeur estimée */}
        <Form.Item
          name="estimated_value"
          label="Valeur estimée du service"
          rules={[
            { required: true, message: 'Valeur requise' },
            { type: 'number', min: 50, message: 'Minimum 50 dhs' }
          ]}
        >
          <InputNumber
            style={{ width: '100%' }}
            size="large"
            min={50}
            max={1000000}
            formatter={value => `${value} dhs`}
            parser={value => value.replace(' dhs', '')}
            onChange={setEstimatedValue}
          />
        </Form.Item>

        {/* Preview commission */}
        {commissionPreview && (
          <Card 
            size="small" 
            style={{ 
              marginBottom: 16,
              background: depositAvailable ? '#e6f7ff' : '#fff2e8',
              border: `1px solid ${depositAvailable ? '#91d5ff' : '#ffbb96'}`
            }}
          >
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: 16 }}>
              <Statistic
                title="Commission totale"
                value={commissionPreview.commission_amount}
                suffix="dhs"
                prefix={<DollarOutlined />}
                valueStyle={{ color: '#1890ff', fontSize: 18 }}
              />
              <Statistic
                title="Votre commission"
                value={commissionPreview.influencer_commission}
                suffix="dhs"
                prefix={<CalculatorOutlined />}
                valueStyle={{ color: '#52c41a', fontSize: 18, fontWeight: 'bold' }}
              />
              <Statistic
                title="Type"
                value={commissionPreview.commission_type === 'percentage' ? '10%' : '80 dhs fixe'}
                valueStyle={{ fontSize: 14 }}
              />
            </div>

            {!depositAvailable && (
              <Alert
                message="Dépôt insuffisant"
                description="Le merchant n'a pas assez de solde. Le lead sera en attente de recharge."
                type="warning"
                showIcon
                style={{ marginTop: 12 }}
              />
            )}
          </Card>
        )}

        {/* Source */}
        <Form.Item
          name="source"
          label="Source du lead"
          rules={[{ required: true, message: 'Source requise' }]}
        >
          <Select size="large">
            <Option value="instagram">📷 Instagram</Option>
            <Option value="tiktok">🎵 TikTok</Option>
            <Option value="whatsapp">💬 WhatsApp</Option>
            <Option value="direct">🎯 Direct</Option>
          </Select>
        </Form.Item>

        {/* Notes */}
        <Form.Item
          name="customer_notes"
          label="Notes supplémentaires (optionnel)"
        >
          <TextArea
            rows={3}
            placeholder="Budget estimé, timeline, besoins spécifiques..."
            maxLength={500}
            showCount
          />
        </Form.Item>

        {/* Bouton de soumission */}
        <Form.Item>
          <Button
            type="primary"
            htmlType="submit"
            size="large"
            icon={<SendOutlined />}
            loading={loading}
            block
            disabled={!depositAvailable}
          >
            Créer le lead
          </Button>
        </Form.Item>

        {/* Informations importantes */}
        <Alert
          message="💡 Conseils pour un lead de qualité"
          description={
            <ul style={{ margin: '8px 0', paddingLeft: 20 }}>
              <li>Vérifiez que les informations sont complètes et exactes</li>
              <li>Ajoutez des notes détaillées sur les besoins du client</li>
              <li>Un lead de qualité = validation rapide = paiement rapide</li>
              <li>Les leads mal qualifiés peuvent être rejetés sans commission</li>
            </ul>
          }
          type="info"
          showIcon
        />
      </Form>
    </Card>
  );
};

export default CreateLeadForm;
