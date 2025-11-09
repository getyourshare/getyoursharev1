import React, { useState, useEffect } from 'react';
import { Table, Tag, Button, Space, Modal, Input, Rate, message, Badge, Select, DatePicker } from 'antd';
import { 
  CheckOutlined, 
  CloseOutlined, 
  EyeOutlined,
  FilterOutlined,
  DownloadOutlined 
} from '@ant-design/icons';
import axios from 'axios';
import moment from 'moment';

const { TextArea } = Input;
const { Option } = Select;
const { RangePicker } = DatePicker;

/**
 * Table des leads en attente - Dashboard Merchant
 * 
 * Permet de:
 * - Visualiser tous les leads en attente de validation
 * - Valider ou rejeter les leads
 * - Noter la qualité (1-10)
 * - Filtrer par campagne, date, source
 * - Exporter en CSV
 */
const PendingLeadsTable = ({ merchantId }) => {
  const [loading, setLoading] = useState(true);
  const [leads, setLeads] = useState([]);
  const [filteredLeads, setFilteredLeads] = useState([]);
  const [campaigns, setCampaigns] = useState([]);
  const [selectedLead, setSelectedLead] = useState(null);
  const [validationModalVisible, setValidationModalVisible] = useState(false);
  const [rejectionModalVisible, setRejectionModalVisible] = useState(false);
  const [qualityScore, setQualityScore] = useState(7);
  const [feedback, setFeedback] = useState('');
  const [rejectionReason, setRejectionReason] = useState('');
  const [validating, setValidating] = useState(false);
  
  // Filtres
  const [filterCampaign, setFilterCampaign] = useState(null);
  const [filterSource, setFilterSource] = useState(null);
  const [filterDateRange, setFilterDateRange] = useState(null);

  useEffect(() => {
    loadLeads();
    loadCampaigns();
  }, [merchantId]);

  useEffect(() => {
    applyFilters();
  }, [leads, filterCampaign, filterSource, filterDateRange]);

  const loadLeads = async () => {
    try {
      const token = localStorage.getItem('token');
      const response = await axios.get('/api/leads/merchant/my-leads', {
        headers: { Authorization: `Bearer ${token}` },
        params: { status: 'pending' }
      });
      
      setLeads(response.data.leads || []);
      setLoading(false);
    } catch (error) {
      console.error('Erreur chargement leads:', error);
      message.error('Impossible de charger les leads');
      setLoading(false);
    }
  };

  const loadCampaigns = async () => {
    try {
      const token = localStorage.getItem('token');
      const response = await axios.get('/api/campaigns/my-campaigns', {
        headers: { Authorization: `Bearer ${token}` }
      });
      
      setCampaigns(response.data.campaigns || []);
    } catch (error) {
      console.error('Erreur chargement campagnes:', error);
    }
  };

  const applyFilters = () => {
    let filtered = [...leads];

    // Filtrer par campagne
    if (filterCampaign) {
      filtered = filtered.filter(lead => lead.campaign_id === filterCampaign);
    }

    // Filtrer par source
    if (filterSource) {
      filtered = filtered.filter(lead => lead.source === filterSource);
    }

    // Filtrer par date
    if (filterDateRange && filterDateRange.length === 2) {
      const [start, end] = filterDateRange;
      filtered = filtered.filter(lead => {
        const leadDate = moment(lead.created_at);
        return leadDate.isBetween(start, end, 'day', '[]');
      });
    }

    setFilteredLeads(filtered);
  };

  const handleValidate = async () => {
    if (!selectedLead || !qualityScore) {
      message.error('Veuillez donner une note de qualité');
      return;
    }

    setValidating(true);
    try {
      const token = localStorage.getItem('token');
      await axios.put(`/api/leads/${selectedLead.id}/validate`, {
        quality_score: qualityScore,
        feedback: feedback
      }, {
        headers: { Authorization: `Bearer ${token}` }
      });

      message.success('Lead validé avec succès');
      setValidationModalVisible(false);
      loadLeads();
      
      // Réinitialiser
      setQualityScore(7);
      setFeedback('');
    } catch (error) {
      console.error('Erreur validation:', error);
      message.error('Échec de la validation');
    } finally {
      setValidating(false);
    }
  };

  const handleReject = async () => {
    if (!selectedLead || !rejectionReason) {
      message.error('Veuillez indiquer une raison de rejet');
      return;
    }

    setValidating(true);
    try {
      const token = localStorage.getItem('token');
      await axios.put(`/api/leads/${selectedLead.id}/reject`, {
        rejection_reason: rejectionReason
      }, {
        headers: { Authorization: `Bearer ${token}` }
      });

      message.success('Lead rejeté');
      setRejectionModalVisible(false);
      loadLeads();
      
      // Réinitialiser
      setRejectionReason('');
    } catch (error) {
      console.error('Erreur rejet:', error);
      message.error('Échec du rejet');
    } finally {
      setValidating(false);
    }
  };

  const exportToCSV = () => {
    const headers = ['Date', 'Client', 'Email', 'Téléphone', 'Valeur', 'Commission', 'Source', 'Influenceur'];
    const rows = filteredLeads.map(lead => [
      moment(lead.created_at).format('DD/MM/YYYY HH:mm'),
      lead.customer_name,
      lead.customer_email,
      lead.customer_phone,
      `${lead.estimated_value} dhs`,
      `${lead.commission_amount} dhs`,
      lead.source,
      lead.influencer_email || 'N/A'
    ]);

    const csv = [headers, ...rows].map(row => row.join(',')).join('\n');
    const blob = new Blob([csv], { type: 'text/csv' });
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `leads_${moment().format('YYYYMMDD')}.csv`;
    a.click();
  };

  const columns = [
    {
      title: 'Date',
      dataIndex: 'created_at',
      key: 'created_at',
      render: (date) => moment(date).format('DD/MM HH:mm'),
      sorter: (a, b) => moment(a.created_at).unix() - moment(b.created_at).unix(),
    },
    {
      title: 'Client',
      key: 'customer',
      render: (_, record) => (
        <div>
          <div style={{ fontWeight: 'bold' }}>{record.customer_name}</div>
          <div style={{ fontSize: 12, color: '#888' }}>{record.customer_email}</div>
          <div style={{ fontSize: 12, color: '#888' }}>{record.customer_phone}</div>
        </div>
      ),
    },
    {
      title: 'Entreprise',
      dataIndex: 'customer_company',
      key: 'customer_company',
      render: (company) => company || <span style={{ color: '#ccc' }}>-</span>,
    },
    {
      title: 'Valeur estimée',
      dataIndex: 'estimated_value',
      key: 'estimated_value',
      render: (value) => <strong>{value} dhs</strong>,
      sorter: (a, b) => a.estimated_value - b.estimated_value,
    },
    {
      title: 'Commission',
      key: 'commission',
      render: (_, record) => (
        <div>
          <div style={{ fontWeight: 'bold', color: '#1890ff' }}>
            {record.commission_amount} dhs
          </div>
          <Tag color={record.commission_type === 'percentage' ? 'blue' : 'green'}>
            {record.commission_type === 'percentage' ? '10%' : 'Fixe'}
          </Tag>
        </div>
      ),
    },
    {
      title: 'Source',
      dataIndex: 'source',
      key: 'source',
      render: (source) => {
        const colors = {
          instagram: 'pink',
          tiktok: 'purple',
          whatsapp: 'green',
          direct: 'blue'
        };
        return <Tag color={colors[source] || 'default'}>{source}</Tag>;
      },
    },
    {
      title: 'Influenceur',
      dataIndex: 'influencer_email',
      key: 'influencer_email',
      render: (email) => email || <span style={{ color: '#ccc' }}>N/A</span>,
    },
    {
      title: 'Actions',
      key: 'actions',
      fixed: 'right',
      width: 180,
      render: (_, record) => (
        <Space size="small">
          <Button
            type="primary"
            size="small"
            icon={<CheckOutlined />}
            onClick={() => {
              setSelectedLead(record);
              setValidationModalVisible(true);
            }}
          >
            Valider
          </Button>
          <Button
            danger
            size="small"
            icon={<CloseOutlined />}
            onClick={() => {
              setSelectedLead(record);
              setRejectionModalVisible(true);
            }}
          >
            Rejeter
          </Button>
        </Space>
      ),
    },
  ];

  return (
    <>
      {/* Filtres et actions */}
      <div style={{ 
        marginBottom: 16, 
        display: 'flex', 
        justifyContent: 'space-between',
        flexWrap: 'wrap',
        gap: 12 
      }}>
        <Space wrap>
          <Select
            style={{ width: 200 }}
            placeholder="Filtrer par campagne"
            allowClear
            onChange={setFilterCampaign}
          >
            {campaigns.map(camp => (
              <Option key={camp.id} value={camp.id}>{camp.name}</Option>
            ))}
          </Select>

          <Select
            style={{ width: 150 }}
            placeholder="Source"
            allowClear
            onChange={setFilterSource}
          >
            <Option value="instagram">Instagram</Option>
            <Option value="tiktok">TikTok</Option>
            <Option value="whatsapp">WhatsApp</Option>
            <Option value="direct">Direct</Option>
          </Select>

          <RangePicker
            onChange={setFilterDateRange}
            format="DD/MM/YYYY"
          />
        </Space>

        <Space>
          <Badge count={filteredLeads.length} showZero>
            <Button icon={<FilterOutlined />}>
              Leads en attente
            </Button>
          </Badge>
          
          <Button
            icon={<DownloadOutlined />}
            onClick={exportToCSV}
            disabled={filteredLeads.length === 0}
          >
            Exporter CSV
          </Button>
        </Space>
      </div>

      {/* Table */}
      <Table
        columns={columns}
        dataSource={filteredLeads}
        rowKey="id"
        loading={loading}
        pagination={{
          pageSize: 10,
          showSizeChanger: true,
          showTotal: (total) => `Total: ${total} leads`
        }}
        scroll={{ x: 1200 }}
      />

      {/* Modal de validation */}
      <Modal
        title="Valider le lead"
        visible={validationModalVisible}
        onOk={handleValidate}
        onCancel={() => setValidationModalVisible(false)}
        confirmLoading={validating}
        okText="Valider"
        cancelText="Annuler"
        width={600}
      >
        {selectedLead && (
          <div>
            <h4>Informations du lead</h4>
            <div style={{ marginBottom: 16, padding: 12, background: '#f5f5f5', borderRadius: 4 }}>
              <p><strong>Client:</strong> {selectedLead.customer_name}</p>
              <p><strong>Email:</strong> {selectedLead.customer_email}</p>
              <p><strong>Téléphone:</strong> {selectedLead.customer_phone}</p>
              <p><strong>Valeur:</strong> {selectedLead.estimated_value} dhs</p>
              <p><strong>Commission:</strong> {selectedLead.commission_amount} dhs</p>
            </div>

            <div style={{ marginBottom: 16 }}>
              <label style={{ display: 'block', marginBottom: 8 }}>
                <strong>Note de qualité (1-10):</strong>
              </label>
              <Rate
                count={10}
                value={qualityScore}
                onChange={setQualityScore}
                style={{ fontSize: 24 }}
              />
              <span style={{ marginLeft: 12, fontSize: 18, fontWeight: 'bold', color: '#1890ff' }}>
                {qualityScore}/10
              </span>
            </div>

            <div>
              <label style={{ display: 'block', marginBottom: 8 }}>
                <strong>Commentaire (optionnel):</strong>
              </label>
              <TextArea
                rows={4}
                value={feedback}
                onChange={(e) => setFeedback(e.target.value)}
                placeholder="Ajoutez vos remarques sur ce lead..."
              />
            </div>
          </div>
        )}
      </Modal>

      {/* Modal de rejet */}
      <Modal
        title="Rejeter le lead"
        visible={rejectionModalVisible}
        onOk={handleReject}
        onCancel={() => setRejectionModalVisible(false)}
        confirmLoading={validating}
        okText="Confirmer le rejet"
        okButtonProps={{ danger: true }}
        cancelText="Annuler"
      >
        {selectedLead && (
          <div>
            <div style={{ marginBottom: 16, padding: 12, background: '#fff2e8', borderRadius: 4 }}>
              <p><strong>Client:</strong> {selectedLead.customer_name}</p>
              <p><strong>Valeur:</strong> {selectedLead.estimated_value} dhs</p>
            </div>

            <div>
              <label style={{ display: 'block', marginBottom: 8 }}>
                <strong>Raison du rejet:</strong>
              </label>
              <Select
                style={{ width: '100%', marginBottom: 12 }}
                placeholder="Choisissez une raison"
                onChange={setRejectionReason}
              >
                <Option value="Informations incomplètes">Informations incomplètes</Option>
                <Option value="Client non qualifié">Client non qualifié</Option>
                <Option value="Doublon">Doublon</Option>
                <Option value="Fausses informations">Fausses informations</Option>
                <Option value="Hors budget">Hors budget</Option>
                <Option value="Autre">Autre</Option>
              </Select>

              <TextArea
                rows={3}
                value={rejectionReason}
                onChange={(e) => setRejectionReason(e.target.value)}
                placeholder="Détaillez la raison du rejet..."
              />
            </div>
          </div>
        )}
      </Modal>
    </>
  );
};

export default PendingLeadsTable;
