import { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { clientsApi } from '../api/clients';
import { projectsApi } from '../api/projects';
import { useToast } from '../context/ToastContext';
import StatusBadge from '../components/StatusBadge';
import { Folder, Play, CheckCircle } from 'lucide-react';

export default function ClientDetail() {
  const { id } = useParams();
  const [client, setClient] = useState(null);
  const [projects, setProjects] = useState([]);
  const [loading, setLoading] = useState(true);
  const navigate = useNavigate();
  const { addToast } = useToast();

  useEffect(() => { loadData(); }, [id]);

  const loadData = async () => {
    try {
      const [clientRes, projectsRes] = await Promise.all([
        clientsApi.get(id),
        projectsApi.list({ client_id: id }),
      ]);
      setClient(clientRes.data);
      setProjects(projectsRes.data);
    } catch (err) {
      addToast('Failed to load client', 'error');
      navigate('/clients');
    } finally {
      setLoading(false);
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

  if (loading) return <div className="loading">Loading...</div>;
  if (!client) return null;

  return (
    <div className="page" id="client-detail-page">
      <button className="btn btn-secondary btn-back" onClick={() => navigate('/clients')}>← Back to Clients</button>

      <div className="detail-header">
        <div>
          <h1 className="page-title">{client.name}</h1>
          <StatusBadge status={client.status} type="client" />
        </div>
      </div>

      <div className="detail-info">
        {client.company && <div className="info-item"><span className="info-label">Company</span><span>{client.company}</span></div>}
        {client.email && <div className="info-item"><span className="info-label">Email</span><span>{client.email}</span></div>}
        {client.phone && <div className="info-item"><span className="info-label">Phone</span><span>{client.phone}</span></div>}
        {client.notes && <div className="info-item"><span className="info-label">Notes</span><span>{client.notes}</span></div>}
      </div>

      <div className="summary-cards" style={{ margin: '32px 0' }}>
        <div className="summary-card clickable" onClick={() => navigate('/projects', { state: { clientFilter: id } })}>
          <span className="summary-icon"><Folder size={24} className="text-muted" /></span>
          <span className="summary-number">{projects.length}</span>
          <span className="summary-label">Total Projects</span>
        </div>
        <div className="summary-card clickable" onClick={() => navigate('/projects', { state: { clientFilter: id, filter: 'active' } })}>
          <span className="summary-icon"><Play size={24} className="text-muted" /></span>
          <span className="summary-number">{projects.filter(p => p.status !== 'completed').length}</span>
          <span className="summary-label">Active / Working</span>
        </div>
        <div className="summary-card clickable" onClick={() => navigate('/projects', { state: { clientFilter: id, filter: 'completed' } })}>
          <span className="summary-icon"><CheckCircle size={24} className="text-muted" /></span>
          <span className="summary-number">{projects.filter(p => p.status === 'completed').length}</span>
          <span className="summary-label">Completed</span>
        </div>
      </div>

      <h2 className="section-title">Projects List</h2>
      {projects.length === 0 ? (
        <p className="text-muted">No projects for this client yet.</p>
      ) : (
        <div className="card-grid">
          {projects.map((p) => (
            <div key={p.id} className="card clickable" onClick={() => navigate(`/projects/${p.id}`)}>
              <div className="card-header">
                <h3>{p.name}</h3>
                <StatusBadge status={p.status} type="project" />
              </div>
              <div className="card-body">
                {p.deadline && (
                  <div className={`deadline-text ${getDeadlineClass(p.deadline, p.status)}`}>
                    Deadline: {p.deadline}
                  </div>
                )}
                <div className="card-stats">
                  <span>{p.task_count} tasks</span>
                  <span>{p.total_hours}h logged</span>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
