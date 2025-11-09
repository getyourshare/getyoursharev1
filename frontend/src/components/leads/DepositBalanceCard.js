import React, { useState, useEffect } from 'react';
import { Card, Progress, Button, Badge, Statistic, Modal, InputNumber, message, Spin } from 'antd';
import { 
  DollarOutlined, 
  WarningOutlined, 
  ReloadOutlined,
  AlertOutlined,
  CheckCircleOutlined 
} from '@ant-design/icons';
import axios from 'axios';

/**
 * Widget Solde Dépôt - Dashboard Merchant
 * 
 * Affiche le solde du dépôt avec alertes visuelles multi-niveau:
 * - VERT (>50%): Solde sain
 * - JAUNE (50-20%): Attention - Recharge recommandée
 * - ORANGE (20-10%): Avertissement - Recharge urgente
 * - ROUGE (10-0%): Critique - Leads bloqués bientôt
 * - NOIR (0%): Épuisé - Leads bloqués
 */
const DepositBalanceCard = ({ merchantId, campaignId = null }) => {
  const [loading, setLoading] = useState(true);
  const [deposit, setDeposit] = useState(null);
  const [transactions, setTransactions] = useState([]);
  const [rechargeModalVisible, setRechargeModalVisible] = useState(false);
  const [rechargeAmount, setRechargeAmount] = useState(2000);
  const [recharging, setRecharging] = useState(false);

  // Charger les données du dépôt
  useEffect(() => {
    loadDepositData();
    
    // Rafraîchir toutes les 30 secondes
    const interval = setInterval(loadDepositData, 30000);
    return () => clearInterval(interval);
  }, [merchantId, campaignId]);

  const loadDepositData = async () => {
    try {
      const token = localStorage.getItem('token');
      
      // Récupérer le solde
      const balanceResponse = await axios.get('/api/leads/deposits/balance', {
        headers: { Authorization: `Bearer ${token}` },
        params: { merchant_id: merchantId, campaign_id: campaignId }
      });
      
      setDeposit(balanceResponse.data);
      
      // Récupérer les transactions récentes
      const transactionsResponse = await axios.get('/api/leads/deposits/transactions', {
        headers: { Authorization: `Bearer ${token}` },
        params: { limit: 5 }
      });
      
      setTransactions(transactionsResponse.data.transactions || []);
      setLoading(false);
    } catch (error) {
      console.error('Erreur chargement dépôt:', error);
      message.error('Impossible de charger le solde');
      setLoading(false);
    }
  };

  const handleRecharge = async () => {
    if (!rechargeAmount || rechargeAmount < 500) {
      message.error('Montant minimum: 500 dhs');
      return;
    }

    setRecharging(true);
    try {
      const token = localStorage.getItem('token');
      
      const response = await axios.post('/api/leads/deposits/recharge', {
        deposit_id: deposit.id,
        amount: rechargeAmount,
        payment_method: 'stripe' // ou 'cmi'
      }, {
        headers: { Authorization: `Bearer ${token}` }
      });

      if (response.data.payment_url) {
        // Rediriger vers la page de paiement
        window.location.href = response.data.payment_url;
      } else {
        message.success(`Dépôt rechargé de ${rechargeAmount} dhs`);
        setRechargeModalVisible(false);
        loadDepositData();
      }
    } catch (error) {
      console.error('Erreur recharge:', error);
      message.error('Échec de la recharge');
    } finally {
      setRecharging(false);
    }
  };

  if (loading) {
    return (
      <Card>
        <div style={{ textAlign: 'center', padding: '40px' }}>
          <Spin size="large" />
        </div>
      </Card>
    );
  }

  if (!deposit) {
    return (
      <Card>
        <div style={{ textAlign: 'center', padding: '20px' }}>
          <p>Aucun dépôt actif</p>
          <Button type="primary" onClick={() => setRechargeModalVisible(true)}>
            Créer un dépôt
          </Button>
        </div>
      </Card>
    );
  }

  // Calculer le pourcentage et le niveau d'alerte
  const percentage = (deposit.current_balance / deposit.initial_amount) * 100;
  
  let alertLevel = 'HEALTHY';
  let progressColor = '#52c41a'; // Vert
  let statusText = 'Solde sain';
  let icon = <CheckCircleOutlined style={{ color: '#52c41a' }} />;
  
  if (percentage <= 0) {
    alertLevel = 'DEPLETED';
    progressColor = '#000000'; // Noir
    statusText = 'ÉPUISÉ - Leads bloqués';
    icon = <AlertOutlined style={{ color: '#000000' }} />;
  } else if (percentage <= 10) {
    alertLevel = 'CRITICAL';
    progressColor = '#ff4d4f'; // Rouge
    statusText = 'CRITIQUE - Rechargez maintenant';
    icon = <WarningOutlined style={{ color: '#ff4d4f' }} />;
  } else if (percentage <= 20) {
    alertLevel = 'WARNING';
    progressColor = '#fa8c16'; // Orange
    statusText = 'AVERTISSEMENT - Recharge urgente';
    icon = <WarningOutlined style={{ color: '#fa8c16' }} />;
  } else if (percentage <= 50) {
    alertLevel = 'ATTENTION';
    progressColor = '#faad14'; // Jaune
    statusText = 'Attention - Recharge recommandée';
    icon = <WarningOutlined style={{ color: '#faad14' }} />;
  }

  return (
    <>
      <Card
        title={
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <span>
              <DollarOutlined /> Solde Dépôt LEADS
            </span>
            {icon}
          </div>
        }
        extra={
          <Button 
            type="primary" 
            icon={<ReloadOutlined />}
            onClick={() => setRechargeModalVisible(true)}
            disabled={alertLevel === 'DEPLETED'}
          >
            Recharger
          </Button>
        }
        style={{ 
          borderLeft: `4px solid ${progressColor}`,
          boxShadow: alertLevel !== 'HEALTHY' ? `0 0 10px ${progressColor}` : undefined
        }}
      >
        {/* Progression circulaire */}
        <div style={{ textAlign: 'center', marginBottom: 24 }}>
          <Progress
            type="circle"
            percent={percentage}
            strokeColor={progressColor}
            format={() => `${percentage.toFixed(1)}%`}
            width={120}
          />
          <div style={{ marginTop: 12 }}>
            <Badge 
              status={alertLevel === 'HEALTHY' ? 'success' : 'error'} 
              text={statusText}
              style={{ fontSize: 14, fontWeight: 'bold' }}
            />
          </div>
        </div>

        {/* Statistiques */}
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: 16, marginBottom: 24 }}>
          <Statistic
            title="Solde actuel"
            value={deposit.current_balance}
            suffix="dhs"
            valueStyle={{ color: progressColor }}
          />
          <Statistic
            title="Réservé"
            value={deposit.reserved_amount}
            suffix="dhs"
            valueStyle={{ color: '#1890ff' }}
          />
          <Statistic
            title="Disponible"
            value={deposit.available_balance}
            suffix="dhs"
            valueStyle={{ color: '#52c41a' }}
          />
        </div>

        {/* Barre de progression linéaire */}
        <Progress
          percent={percentage}
          strokeColor={progressColor}
          status={alertLevel === 'DEPLETED' ? 'exception' : 'active'}
          showInfo={false}
        />

        {/* Messages d'alerte */}
        {alertLevel === 'DEPLETED' && (
          <div style={{ 
            marginTop: 16, 
            padding: 12, 
            background: '#fff2e8', 
            border: '1px solid #ffbb96',
            borderRadius: 4 
          }}>
            <AlertOutlined style={{ color: '#ff4d4f', marginRight: 8 }} />
            <strong>Dépôt épuisé!</strong> Aucun lead ne peut être généré. 
            Rechargez votre compte immédiatement.
          </div>
        )}

        {alertLevel === 'CRITICAL' && (
          <div style={{ 
            marginTop: 16, 
            padding: 12, 
            background: '#fff1f0', 
            border: '1px solid #ffa39e',
            borderRadius: 4 
          }}>
            <WarningOutlined style={{ color: '#ff4d4f', marginRight: 8 }} />
            Il vous reste moins de <strong>10%</strong> de votre dépôt. 
            Les leads seront bientôt bloqués.
          </div>
        )}

        {/* Transactions récentes */}
        {transactions.length > 0 && (
          <div style={{ marginTop: 16 }}>
            <h4>Dernières transactions</h4>
            <div style={{ maxHeight: 150, overflowY: 'auto' }}>
              {transactions.map((tx, index) => (
                <div 
                  key={index}
                  style={{ 
                    display: 'flex', 
                    justifyContent: 'space-between',
                    padding: '8px 0',
                    borderBottom: '1px solid #f0f0f0'
                  }}
                >
                  <span style={{ fontSize: 12, color: '#888' }}>
                    {new Date(tx.created_at).toLocaleDateString('fr-FR')}
                  </span>
                  <span>{tx.description}</span>
                  <span style={{ 
                    fontWeight: 'bold',
                    color: tx.transaction_type === 'recharge' ? '#52c41a' : '#ff4d4f'
                  }}>
                    {tx.transaction_type === 'recharge' ? '+' : ''}{tx.amount} dhs
                  </span>
                </div>
              ))}
            </div>
          </div>
        )}
      </Card>

      {/* Modal de recharge */}
      <Modal
        title="Recharger le dépôt"
        visible={rechargeModalVisible}
        onOk={handleRecharge}
        onCancel={() => setRechargeModalVisible(false)}
        confirmLoading={recharging}
        okText="Payer"
        cancelText="Annuler"
      >
        <div style={{ marginBottom: 16 }}>
          <p>Choisissez le montant à recharger:</p>
          <div style={{ display: 'flex', gap: 8, marginBottom: 16 }}>
            <Button onClick={() => setRechargeAmount(2000)}>2 000 dhs</Button>
            <Button onClick={() => setRechargeAmount(5000)}>5 000 dhs</Button>
            <Button onClick={() => setRechargeAmount(10000)}>10 000 dhs</Button>
          </div>
          
          <InputNumber
            style={{ width: '100%' }}
            min={500}
            max={100000}
            value={rechargeAmount}
            onChange={setRechargeAmount}
            formatter={value => `${value} dhs`}
            parser={value => value.replace(' dhs', '')}
          />
        </div>

        <div style={{ 
          padding: 12, 
          background: '#e6f7ff', 
          border: '1px solid #91d5ff',
          borderRadius: 4 
        }}>
          <p style={{ margin: 0, fontSize: 12 }}>
            💡 <strong>Astuce:</strong> Rechargez au moins 5 000 dhs pour éviter 
            les recharges fréquentes et bénéficier de plusieurs centaines de leads.
          </p>
        </div>
      </Modal>
    </>
  );
};

export default DepositBalanceCard;
