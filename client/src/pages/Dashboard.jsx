import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { dashboardApi } from '../api/dashboard';
import { Users, Folder, CalendarCheck, Clock, AlertTriangle, FileText, RefreshCw, CheckCircle } from 'lucide-react';

export default function Dashboard() {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const navigate = useNavigate();

  useEffect(() => { loadDashboard(); }, []);

  const loadDashboard = async () => {
    try {
      const res = await dashboardApi.get();
      setData(res.data);
    } catch (err) {
      console.error('Dashboard load error:', err);
    } finally {
      setLoading(false);
    }
  };

  if (loading) return <div className="loading">Loading dashboard...</div>;
  if (!data) return <div className="loading">Failed to load dashboard.</div>;

  return (
    <div className="page" id="dashboard-page">
      <h1 className="page-title">Dashboard</h1>

      <div className="summary-cards">
        <div className="summary-card clickable" onClick={() => navigate('/clients', { state: { filter: 'active' } })}>
          <span className="summary-icon"><Users size={28} className="text-muted" /></span>
          <span className="summary-number">{data.active_clients}</span>
          <span className="summary-label">Active Clients</span>
        </div>
        <div className="summary-card clickable" onClick={() => navigate('/projects', { state: { filter: 'active' } })}>
          <span className="summary-icon"><Folder size={28} className="text-muted" /></span>
          <span className="summary-number">{data.active_projects}</span>
          <span className="summary-label">Active Projects</span>
        </div>
        <div className="summary-card clickable" onClick={() => navigate('/today')}>
          <span className="summary-icon"><CalendarCheck size={28} className="text-muted" /></span>
          <span className="summary-number">{data.today_tasks.total}</span>
          <span className="summary-label">Today's Tasks</span>
        </div>
        <div className="summary-card">
          <span className="summary-icon"><Clock size={28} className="text-muted" /></span>
          <span className="summary-number">{data.weekly_billable_hours}h</span>
          <span className="summary-label">Billable This Week</span>
        </div>
      </div>

      {data.overdue_projects.length > 0 && (
        <div className="alert-section alert-danger">
          <h3 style={{ display: 'flex', alignItems: 'center', gap: '8px' }}><AlertTriangle size={18} /> Overdue Projects</h3>
          {data.overdue_projects.map((p) => (
            <div key={p.id} className="alert-item" onClick={() => navigate(`/projects/${p.id}`)}>
              <span>{p.name}</span>
              <span className="deadline-text deadline-overdue">Due: {p.deadline}</span>
            </div>
          ))}
        </div>
      )}

      {data.approaching_deadline_projects.length > 0 && (
        <div className="alert-section alert-warning">
          <h3 style={{ display: 'flex', alignItems: 'center', gap: '8px' }}><Clock size={18} /> Approaching Deadlines</h3>
          {data.approaching_deadline_projects.map((p) => (
            <div key={p.id} className="alert-item" onClick={() => navigate(`/projects/${p.id}`)}>
              <span>{p.name}</span>
              <span className="deadline-text deadline-approaching">Due: {p.deadline}</span>
            </div>
          ))}
        </div>
      )}

      <div className="today-summary">
        <h3>Today's Tasks</h3>
        <div className="today-stats">
          <span className="stat" style={{ display: 'flex', alignItems: 'center', gap: '6px' }}><FileText size={16} /> {data.today_tasks.todo} todo</span>
          <span className="stat" style={{ display: 'flex', alignItems: 'center', gap: '6px' }}><RefreshCw size={16} /> {data.today_tasks.in_progress} in progress</span>
          <span className="stat" style={{ display: 'flex', alignItems: 'center', gap: '6px' }}><CheckCircle size={16} /> {data.today_tasks.done} done</span>
        </div>
      </div>
    </div>
  );
}
