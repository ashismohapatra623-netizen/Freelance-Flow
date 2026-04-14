import { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { projectsApi } from '../api/projects';
import { tasksApi } from '../api/tasks';
import { useToast } from '../context/ToastContext';
import StatusBadge from '../components/StatusBadge';
import PriorityBadge from '../components/PriorityBadge';
import Timer from '../components/Timer';
import Modal from '../components/Modal';
import ConfirmDialog from '../components/ConfirmDialog';
import { ArrowLeft, Plus, Trash2, DollarSign } from 'lucide-react';

export default function ProjectDetail() {
  const { id } = useParams();
  const [project, setProject] = useState(null);
  const [summary, setSummary] = useState(null);
  const [tasks, setTasks] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showTaskModal, setShowTaskModal] = useState(false);
  const [deleteTarget, setDeleteTarget] = useState(null);
  const [expandedTasks, setExpandedTasks] = useState(new Set());
  const [taskForm, setTaskForm] = useState({ title: '', description: '', priority: 'medium', estimated_hours: '' });
  const navigate = useNavigate();
  const { addToast } = useToast();

  useEffect(() => { loadData(); }, [id]);

  const toggleTaskExpand = (taskId) => {
    setExpandedTasks(prev => {
      const newSet = new Set(prev);
      if (newSet.has(taskId)) newSet.delete(taskId);
      else newSet.add(taskId);
      return newSet;
    });
  };

  const loadData = async () => {
    try {
      const [projRes, summaryRes, tasksRes] = await Promise.all([
        projectsApi.get(id),
        projectsApi.getSummary(id),
        tasksApi.list({ project_id: id }),
      ]);
      setProject(projRes.data);
      setSummary(summaryRes.data);
      setTasks(tasksRes.data);
    } catch (err) {
      addToast('Failed to load project', 'error');
      navigate('/projects');
    } finally {
      setLoading(false);
    }
  };

  const handleCreateTask = async (e) => {
    e.preventDefault();
    try {
      const data = { ...taskForm, project_id: id };
      if (data.estimated_hours) data.estimated_hours = parseFloat(data.estimated_hours);
      else delete data.estimated_hours;
      await tasksApi.create(data);
      addToast('Task created', 'success');
      setShowTaskModal(false);
      setTaskForm({ title: '', description: '', priority: 'medium', estimated_hours: '' });
      loadData();
    } catch (err) {
      addToast(err.response?.data?.detail || 'Failed to create task', 'error');
    }
  };

  const handleTaskStatusChange = async (taskId, newStatus) => {
    try {
      await tasksApi.changeStatus(taskId, newStatus);
      loadData();
    } catch (err) {
      addToast('Failed to update status', 'error');
    }
  };

  const handleDeleteTask = async () => {
    try {
      await tasksApi.delete(deleteTarget.id);
      addToast('Task deleted', 'success');
      setDeleteTarget(null);
      loadData();
    } catch (err) {
      addToast('Failed to delete task', 'error');
    }
  };

  const formatTime = (seconds) => {
    if (!seconds) return '0m';
    const h = Math.floor(seconds / 3600);
    const m = Math.floor((seconds % 3600) / 60);
    return h > 0 ? `${h}h ${m}m` : `${m}m`;
  };

  if (loading) return <div className="loading">Loading...</div>;
  if (!project) return null;

  return (
    <div className="page" id="project-detail-page">
      <button className="btn btn-secondary btn-back" onClick={() => navigate('/projects')}><ArrowLeft size={16} /> Back to Projects</button>

      <div className="detail-header">
        <div>
          <h1 className="page-title">{project.name}</h1>
          <div className="detail-meta">
            <StatusBadge status={project.status} type="project" />
            <span className="text-muted">{project.client_name}</span>
            {project.is_billable && <span className="badge badge-billable" style={{ display: 'flex', alignItems: 'center', gap: '4px' }}><DollarSign size={14} /> ${project.hourly_rate}/hr</span>}
          </div>
        </div>
      </div>

      {project.description && <p className="detail-description">{project.description}</p>}

      {summary && (
        <div className="summary-cards">
          <div className="summary-card">
            <span className="summary-number">{summary.tasks.total}</span>
            <span className="summary-label">Total Tasks</span>
          </div>
          <div className="summary-card">
            <span className="summary-number">{summary.tasks.done}/{summary.tasks.total}</span>
            <span className="summary-label">Completed</span>
          </div>
          <div className="summary-card">
            <span className="summary-number">{summary.total_hours}h</span>
            <span className="summary-label">Hours Logged</span>
          </div>
          {summary.billable_amount !== null && (
            <div className="summary-card">
              <span className="summary-number">${summary.billable_amount}</span>
              <span className="summary-label">Billable Amount</span>
            </div>
          )}
        </div>
      )}

      <div className="section-header">
        <h2 className="section-title">Tasks ({tasks.length})</h2>
        <button className="btn btn-primary" onClick={() => setShowTaskModal(true)} id="add-task-btn"><Plus size={16} /> Add Task</button>
      </div>

      {tasks.length === 0 ? (
        <p className="text-muted">No tasks yet. Add your first task.</p>
      ) : (
        <div className="task-list">
          {tasks.map((task) => {
            const isExpanded = expandedTasks.has(task.id);
            return (
              <div key={task.id} className="task-container" style={{ background: 'var(--bg-card)', border: '1px solid var(--border-color)', borderRadius: 'var(--radius-sm)', overflow: 'hidden', transition: 'all 150ms ease', marginBottom: '10px' }}>
                <div 
                  className="task-item" 
                  onClick={() => toggleTaskExpand(task.id)}
                  style={{ border: 'none', borderRadius: '0', marginBottom: '0', cursor: 'pointer', background: isExpanded ? 'var(--bg-card-hover)' : 'transparent' }}
                >
                  <div className="task-info">
                    <div className="task-title" style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                      {task.title}
                    </div>
                    <div className="task-meta">
                      <StatusBadge status={task.status} type="task" />
                      <PriorityBadge priority={task.priority} />
                    </div>
                  </div>
                  <div className="task-actions" onClick={(e) => e.stopPropagation()}>
                    <select
                      value={task.status}
                      onChange={(e) => handleTaskStatusChange(task.id, e.target.value)}
                      className="status-select"
                    >
                      <option value="todo">Todo</option>
                      <option value="in-progress">In Progress</option>
                      <option value="done">Done</option>
                    </select>
                    <Timer taskId={task.id} taskTitle={task.title} initialSeconds={task.total_time_spent} onStop={loadData} />
                    <button 
                      className="btn btn-sm btn-secondary" 
                      onClick={(e) => { e.stopPropagation(); toggleTaskExpand(task.id); }}
                      title="Task Details"
                    >
                      Details
                    </button>
                    <button className="btn btn-sm btn-danger" onClick={(e) => { e.stopPropagation(); setDeleteTarget(task); }} title="Delete Task">
                      <Trash2 size={16} />
                    </button>
                  </div>
                </div>
                {isExpanded && (
                  <div className="task-details-pane" style={{ padding: '16px 18px', borderTop: '1px solid var(--border-subtle)', background: 'var(--bg-secondary)', display: 'flex', flexDirection: 'column', gap: '12px' }}>
                    <div>
                      <h4 style={{ fontSize: '0.85rem', color: 'var(--text-muted)', textTransform: 'uppercase', marginBottom: '4px' }}>Notes & Description</h4>
                      <p style={{ fontSize: '0.9rem', color: 'var(--text-primary)', whiteSpace: 'pre-wrap' }}>
                        {task.description || <span className="text-muted italic">No description provided.</span>}
                      </p>
                    </div>
                    <div style={{ display: 'flex', gap: '20px', flexWrap: 'wrap' }}>
                      <div>
                        <h4 style={{ fontSize: '0.85rem', color: 'var(--text-muted)', textTransform: 'uppercase', marginBottom: '4px' }}>Estimated Time</h4>
                        <p style={{ fontSize: '0.9rem', fontWeight: 600 }}>{task.estimated_hours ? `${task.estimated_hours}h` : 'Not set'}</p>
                      </div>
                      <div>
                        <h4 style={{ fontSize: '0.85rem', color: 'var(--text-muted)', textTransform: 'uppercase', marginBottom: '4px' }}>Logged Time</h4>
                        <p style={{ fontSize: '0.9rem', fontWeight: 600, color: 'var(--success)' }}>{formatTime(task.total_time_spent)}</p>
                      </div>
                    </div>
                  </div>
                )}
              </div>
            );
          })}
        </div>
      )}

      <Modal isOpen={showTaskModal} onClose={() => setShowTaskModal(false)} title="Add Task">
        <form onSubmit={handleCreateTask} className="form">
          <div className="form-group">
            <label>Title *</label>
            <input type="text" value={taskForm.title} onChange={(e) => setTaskForm({ ...taskForm, title: e.target.value })} required />
          </div>
          <div className="form-group">
            <label>Description</label>
            <textarea value={taskForm.description} onChange={(e) => setTaskForm({ ...taskForm, description: e.target.value })} rows={3} />
          </div>
          <div className="form-row">
            <div className="form-group">
              <label>Priority</label>
              <select value={taskForm.priority} onChange={(e) => setTaskForm({ ...taskForm, priority: e.target.value })}>
                <option value="low">Low</option>
                <option value="medium">Medium</option>
                <option value="high">High</option>
              </select>
            </div>
            <div className="form-group">
              <label>Estimated Hours</label>
              <input type="number" step="0.5" min="0" value={taskForm.estimated_hours} onChange={(e) => setTaskForm({ ...taskForm, estimated_hours: e.target.value })} />
            </div>
          </div>
          <div className="modal-footer">
            <button type="button" className="btn btn-secondary" onClick={() => setShowTaskModal(false)}>Cancel</button>
            <button type="submit" className="btn btn-primary">Create Task</button>
          </div>
        </form>
      </Modal>

      <ConfirmDialog isOpen={!!deleteTarget} onClose={() => setDeleteTarget(null)} onConfirm={handleDeleteTask}
        title="Delete Task" message={`Delete "${deleteTarget?.title}"? This will also remove all time entries.`} danger />
    </div>
  );
}
