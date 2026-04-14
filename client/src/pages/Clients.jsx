import { useState, useEffect } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { clientsApi } from '../api/clients';
import { useToast } from '../context/ToastContext';
import StatusBadge from '../components/StatusBadge';
import Modal from '../components/Modal';
import ConfirmDialog from '../components/ConfirmDialog';
import EmptyState from '../components/EmptyState';
import { Plus, Users, Edit2, Trash2, ChevronDown, ChevronUp } from 'lucide-react';

export default function Clients() {
  const [clients, setClients] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showModal, setShowModal] = useState(false);
  const [editingClient, setEditingClient] = useState(null);
  const [deleteTarget, setDeleteTarget] = useState(null);
  const [statusFilter, setStatusFilter] = useState('');
  const [expandedId, setExpandedId] = useState(null);
  const [formData, setFormData] = useState({ name: '', email: '', phone: '', company: '', notes: '', status: 'active' });
  const navigate = useNavigate();
  const location = useLocation();
  const { addToast } = useToast();

  useEffect(() => {
    if (location.state?.filter) setStatusFilter(location.state.filter);
    if (location.state) {
      window.history.replaceState({}, document.title);
    }
  }, [location.state]);

  useEffect(() => { loadClients(); }, [statusFilter]);

  const loadClients = async () => {
    try {
      const params = statusFilter ? { status: statusFilter } : {};
      const res = await clientsApi.list(params);
      setClients(res.data);
    } catch (err) {
      addToast('Failed to load clients', 'error');
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      if (editingClient) {
        await clientsApi.update(editingClient.id, formData);
        addToast('Client updated successfully', 'success');
      } else {
        await clientsApi.create(formData);
        addToast('Client created successfully', 'success');
      }
      setShowModal(false);
      setEditingClient(null);
      resetForm();
      loadClients();
    } catch (err) {
      addToast(err.response?.data?.detail || 'Failed to save client', 'error');
    }
  };

  const handleEdit = (client) => {
    setEditingClient(client);
    setFormData({ name: client.name, email: client.email || '', phone: client.phone || '', company: client.company || '', notes: client.notes || '', status: client.status });
    setShowModal(true);
  };

  const handleDelete = async () => {
    try {
      await clientsApi.delete(deleteTarget.id);
      addToast('Client deleted', 'success');
      setDeleteTarget(null);
      loadClients();
    } catch (err) {
      addToast('Failed to delete client', 'error');
    }
  };

  const resetForm = () => {
    setFormData({ name: '', email: '', phone: '', company: '', notes: '', status: 'active' });
  };

  const openNewModal = () => {
    setEditingClient(null);
    resetForm();
    setShowModal(true);
  };

  const toggleExpand = (id) => {
    setExpandedId(expandedId === id ? null : id);
  };

  if (loading) return <div className="loading">Loading clients...</div>;

  return (
    <div className="page" id="clients-page">
      <div className="page-header">
        <h1 className="page-title">Clients</h1>
        <div className="page-actions">
          <select className="filter-select" value={statusFilter} onChange={(e) => setStatusFilter(e.target.value)} id="client-status-filter">
            <option value="">All</option>
            <option value="active">Active</option>
            <option value="inactive">Inactive</option>
          </select>
          <button className="btn btn-primary" onClick={openNewModal} id="add-client-btn"><Plus size={16} /> Add Client</button>
        </div>
      </div>

      {clients.length === 0 ? (
        <EmptyState icon={<Users size={48} className="text-muted" />} message="No clients yet. Add your first client." action="Add Client" onAction={openNewModal} />
      ) : (
        <div className="client-accordion-list" style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
          {clients.map((c) => (
            <div key={c.id} className="card" style={{ padding: 0, overflow: 'hidden' }}>
              <div className="client-card-header clickable" onClick={() => toggleExpand(c.id)} style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '20px' }}>
                <span style={{ fontSize: '1.1rem', fontWeight: 600 }}>{c.name}</span>
                <button className="btn-icon" onClick={(e) => { e.stopPropagation(); toggleExpand(c.id); }} title="Toggle Details">
                  {expandedId === c.id ? <ChevronUp size={20} /> : <ChevronDown size={20} />}
                </button>
              </div>
              {expandedId === c.id && (
                <div className="client-card-details clickable" onClick={() => navigate(`/clients/${c.id}`)} style={{ padding: '0 20px 20px', borderTop: '1px solid var(--border-subtle)', backgroundColor: 'var(--bg-secondary)', cursor: 'pointer' }}>
                  <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '16px', marginTop: '20px' }}>
                    <div><span className="text-muted text-sm">Company</span><div style={{ marginTop: '4px' }}>{c.company || '—'}</div></div>
                    <div><span className="text-muted text-sm">Email</span><div style={{ marginTop: '4px' }}>{c.email || '—'}</div></div>
                    <div><span className="text-muted text-sm">Status</span><div style={{ marginTop: '4px' }}><StatusBadge status={c.status} type="client" /></div></div>
                    <div><span className="text-muted text-sm">Projects</span><div style={{ marginTop: '4px' }}>{c.project_count}</div></div>
                  </div>

                  <div className="client-details-cta" style={{ textAlign: 'center', margin: '24px 0 16px', padding: '12px', background: 'var(--bg-card)', borderRadius: 'var(--radius-md)', border: '1px solid var(--border-color)', fontWeight: 600, color: 'var(--text-primary)', display: 'flex', justifyContent: 'center', alignItems: 'center', gap: '8px' }}>
                    Click for Full Client Details
                  </div>

                  <div className="client-actions" onClick={(e) => e.stopPropagation()} style={{ display: 'flex', gap: '8px', marginTop: '24px', justifyContent: 'flex-end', borderTop: '1px solid var(--border-color)', paddingTop: '16px' }}>
                    <button className="btn btn-sm btn-secondary" onClick={() => handleEdit(c)}><Edit2 size={14} /> Edit</button>
                    <button className="btn btn-sm btn-danger" onClick={() => setDeleteTarget(c)}><Trash2 size={14} /> Delete</button>
                  </div>
                </div>
              )}
            </div>
          ))}
        </div>
      )}

      <Modal isOpen={showModal} onClose={() => setShowModal(false)} title={editingClient ? 'Edit Client' : 'Add Client'}>
        <form onSubmit={handleSubmit} className="form">
          <div className="form-group">
            <label>Name *</label>
            <input type="text" value={formData.name} onChange={(e) => setFormData({ ...formData, name: e.target.value })} required />
          </div>
          <div className="form-row">
            <div className="form-group">
              <label>Email</label>
              <input type="email" value={formData.email} onChange={(e) => setFormData({ ...formData, email: e.target.value })} />
            </div>
            <div className="form-group">
              <label>Phone</label>
              <input type="text" value={formData.phone} onChange={(e) => setFormData({ ...formData, phone: e.target.value })} />
            </div>
          </div>
          <div className="form-group">
            <label>Company</label>
            <input type="text" value={formData.company} onChange={(e) => setFormData({ ...formData, company: e.target.value })} />
          </div>
          <div className="form-group">
            <label>Notes</label>
            <textarea value={formData.notes} onChange={(e) => setFormData({ ...formData, notes: e.target.value })} rows={3} />
          </div>
          <div className="form-group">
            <label>Status</label>
            <select value={formData.status} onChange={(e) => setFormData({ ...formData, status: e.target.value })}>
              <option value="active">Active</option>
              <option value="inactive">Inactive</option>
            </select>
          </div>
          <div className="modal-footer">
            <button type="button" className="btn btn-secondary" onClick={() => setShowModal(false)}>Cancel</button>
            <button type="submit" className="btn btn-primary">{editingClient ? 'Update' : 'Create'}</button>
          </div>
        </form>
      </Modal>

      <ConfirmDialog
        isOpen={!!deleteTarget}
        onClose={() => setDeleteTarget(null)}
        onConfirm={handleDelete}
        title="Delete Client"
        message={`This will also delete all projects and tasks under "${deleteTarget?.name}". Are you sure?`}
        danger
      />
    </div>
  );
}
