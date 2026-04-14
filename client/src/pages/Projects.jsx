import { useState, useEffect } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { projectsApi } from '../api/projects';
import { clientsApi } from '../api/clients';
import { useToast } from '../context/ToastContext';
import StatusBadge from '../components/StatusBadge';
import Modal from '../components/Modal';
import EmptyState from '../components/EmptyState';
import { Plus, Folder, DollarSign } from 'lucide-react';

export default function Projects() {
  const [projects, setProjects] = useState([]);
  const [clients, setClients] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showModal, setShowModal] = useState(false);
  const [clientFilter, setClientFilter] = useState('');
  const [statusFilter, setStatusFilter] = useState('');
  const [formData, setFormData] = useState({
    client_id: '', name: '', description: '', status: 'active',
    deadline: '', hourly_rate: '', is_billable: true,
  });
  const navigate = useNavigate();
  const location = useLocation();
  const { addToast } = useToast();

  useEffect(() => {
    if (location.state?.filter) setStatusFilter(location.state.filter);
    if (location.state?.clientFilter) setClientFilter(location.state.clientFilter);
    // clear state so it doesn't persist on subsequent loads
    if (location.state) {
      window.history.replaceState({}, document.title);
    }
  }, [location.state]);

  useEffect(() => { loadData(); }, [clientFilter, statusFilter]);

  const loadData = async () => {
    try {
      const params = {};
      if (clientFilter) params.client_id = clientFilter;
      if (statusFilter) params.status = statusFilter;
      const [projRes, clientRes] = await Promise.all([
        projectsApi.list(params),
        clientsApi.list(),
      ]);
      setProjects(projRes.data);
      setClients(clientRes.data);
    } catch (err) {
      addToast('Failed to load projects', 'error');
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      const submitData = { ...formData };
      if (submitData.hourly_rate) submitData.hourly_rate = parseFloat(submitData.hourly_rate);
      else delete submitData.hourly_rate;
      if (!submitData.deadline) delete submitData.deadline;
      await projectsApi.create(submitData);
      addToast('Project created successfully', 'success');
      setShowModal(false);
      setFormData({ client_id: '', name: '', description: '', status: 'active', deadline: '', hourly_rate: '', is_billable: true });
      loadData();
    } catch (err) {
      addToast(err.response?.data?.detail || 'Failed to create project', 'error');
    }
  };

  const getDeadlineClass = (deadline, status) => {
    if (!deadline || status === 'completed') return '';
    const today = new Date().toISOString().split('T')[0];
    const threeDays = new Date(Date.now() + 3 * 86400000).toISOString().split('T')[0];
    if (deadline < today) return 'deadline-overdue';
    if (deadline <= threeDays) return 'deadline-approaching';
    return '';
  };

  if (loading) return <div className="loading">Loading projects...</div>;

  return (
    <div className="page" id="projects-page">
      <div className="page-header">
        <h1 className="page-title">Projects</h1>
        <div className="page-actions">
          <select className="filter-select" value={clientFilter} onChange={(e) => setClientFilter(e.target.value)}>
            <option value="">All Clients</option>
            {clients.map((c) => <option key={c.id} value={c.id}>{c.name}</option>)}
          </select>
          <select className="filter-select" value={statusFilter} onChange={(e) => setStatusFilter(e.target.value)}>
            <option value="">All Statuses</option>
            <option value="active">Active</option>
            <option value="on-hold">On Hold</option>
            <option value="completed">Completed</option>
          </select>
          <button className="btn btn-primary" onClick={() => setShowModal(true)} id="add-project-btn"><Plus size={16} /> Add Project</button>
        </div>
      </div>

      {projects.length === 0 ? (
        <EmptyState icon={<Folder size={48} className="text-muted" />} message="No projects yet. Create your first project." action="Add Project" onAction={() => setShowModal(true)} />
      ) : (
        <div className="card-grid">
          {projects.map((p) => (
            <div key={p.id} className="card clickable" onClick={() => navigate(`/projects/${p.id}`)}>
              <div className="card-header">
                <h3>{p.name}</h3>
                <StatusBadge status={p.status} type="project" />
              </div>
              <div className="card-body">
                <div className="text-muted">{p.client_name}</div>
                {p.deadline && (
                  <div className={`deadline-text ${getDeadlineClass(p.deadline, p.status)}`}>
                    Deadline: {p.deadline}
                  </div>
                )}
                <div className="card-stats">
                  <span>{p.task_count} tasks</span>
                  <span>{p.total_hours}h logged</span>
                  {p.is_billable && <span className="badge badge-billable" style={{ display: 'flex', alignItems: 'center', gap: '4px' }}><DollarSign size={14} /> Billable</span>}
                </div>
              </div>
            </div>
          ))}
        </div>
      )}

      <Modal isOpen={showModal} onClose={() => setShowModal(false)} title="Add Project">
        <form onSubmit={handleSubmit} className="form">
          <div className="form-group">
            <label>Client *</label>
            <select value={formData.client_id} onChange={(e) => setFormData({ ...formData, client_id: e.target.value })} required id="project-client-select">
              <option value="">Select a client</option>
              {clients.map((c) => <option key={c.id} value={c.id}>{c.name}</option>)}
            </select>
          </div>
          <div className="form-group">
            <label>Project Name *</label>
            <input type="text" value={formData.name} onChange={(e) => setFormData({ ...formData, name: e.target.value })} required />
          </div>
          <div className="form-group">
            <label>Description</label>
            <textarea value={formData.description} onChange={(e) => setFormData({ ...formData, description: e.target.value })} rows={3} />
          </div>
          <div className="form-row">
            <div className="form-group">
              <label>Deadline</label>
              <input type="date" value={formData.deadline} onChange={(e) => setFormData({ ...formData, deadline: e.target.value })} />
            </div>
            <div className="form-group">
              <label>Hourly Rate ($)</label>
              <input type="number" step="0.01" min="0" value={formData.hourly_rate} onChange={(e) => setFormData({ ...formData, hourly_rate: e.target.value })} />
            </div>
          </div>
          <div className="form-group checkbox-group">
            <label>
              <input type="checkbox" checked={formData.is_billable} onChange={(e) => setFormData({ ...formData, is_billable: e.target.checked })} />
              Billable Project
            </label>
          </div>
          <div className="modal-footer">
            <button type="button" className="btn btn-secondary" onClick={() => setShowModal(false)}>Cancel</button>
            <button type="submit" className="btn btn-primary">Create Project</button>
          </div>
        </form>
      </Modal>
    </div>
  );
}
