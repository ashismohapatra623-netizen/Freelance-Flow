import { useState, useEffect } from 'react';
import { tasksApi } from '../api/tasks';
import { useToast } from '../context/ToastContext';
import StatusBadge from '../components/StatusBadge';
import PriorityBadge from '../components/PriorityBadge';
import Timer from '../components/Timer';
import { FileText, RefreshCw, CheckCircle, X, Plus } from 'lucide-react';

export default function Today() {
  const [tasks, setTasks] = useState([]);
  const [allTasks, setAllTasks] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showPicker, setShowPicker] = useState(false);
  const { addToast } = useToast();

  useEffect(() => { loadTasks(); }, []);

  const loadTasks = async () => {
    try {
      const [todayRes, allRes] = await Promise.all([
        tasksApi.getToday(),
        tasksApi.list(),
      ]);
      setTasks(todayRes.data);
      setAllTasks(allRes.data.filter((t) => !t.is_today && t.status !== 'done'));
    } catch (err) {
      addToast('Failed to load tasks', 'error');
    } finally {
      setLoading(false);
    }
  };

  const handleStatusChange = async (taskId, newStatus) => {
    try {
      await tasksApi.changeStatus(taskId, newStatus);
      loadTasks();
    } catch (err) {
      addToast('Failed to update status', 'error');
    }
  };

  const handleToggleToday = async (taskId) => {
    try {
      await tasksApi.toggleToday(taskId);
      loadTasks();
    } catch (err) {
      addToast('Failed to update', 'error');
    }
  };

  const formatTime = (seconds) => {
    if (!seconds) return '0m';
    const h = Math.floor(seconds / 3600);
    const m = Math.floor((seconds % 3600) / 60);
    return h > 0 ? `${h}h ${m}m` : `${m}m`;
  };

  const todoTasks = tasks.filter((t) => t.status === 'todo');
  const inProgressTasks = tasks.filter((t) => t.status === 'in-progress');
  const doneTasks = tasks.filter((t) => t.status === 'done');

  if (loading) return <div className="loading">Loading today's tasks...</div>;

  return (
    <div className="page" id="today-page">
      <div className="page-header">
        <h1 className="page-title">Today's Tasks</h1>
        <button className="btn btn-primary" onClick={() => setShowPicker(!showPicker)} id="add-to-today-btn">
          <Plus size={16} /> Add to Today
        </button>
      </div>

      {showPicker && (
        <div className="task-picker">
          <h3>Add tasks to today</h3>
          {allTasks.length === 0 ? (
            <p className="text-muted">No available tasks to add.</p>
          ) : (
            <div className="picker-list">
              {allTasks.map((task) => (
                <div key={task.id} className="picker-item" onClick={() => handleToggleToday(task.id)}>
                  <span className="picker-title">{task.title}</span>
                  <span className="text-muted">{task.project_name}</span>
                  <button className="btn btn-sm btn-primary">Add</button>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      <div className="today-columns">
        <div className="today-column" id="column-todo">
          <div className="column-header column-header-todo">
            <h3 style={{ display: 'flex', alignItems: 'center', gap: '6px' }}><FileText size={16} /> To Do ({todoTasks.length})</h3>
          </div>
          {todoTasks.map((task) => (
            <TodayTaskCard key={task.id} task={task} onStatusChange={handleStatusChange}
              onRemove={handleToggleToday} formatTime={formatTime} />
          ))}
        </div>

        <div className="today-column" id="column-in-progress">
          <div className="column-header column-header-in-progress">
            <h3 style={{ display: 'flex', alignItems: 'center', gap: '6px' }}><RefreshCw size={16} /> In Progress ({inProgressTasks.length})</h3>
          </div>
          {inProgressTasks.map((task) => (
            <TodayTaskCard key={task.id} task={task} onStatusChange={handleStatusChange}
              onRemove={handleToggleToday} formatTime={formatTime} onReload={loadTasks} />
          ))}
        </div>

        <div className="today-column" id="column-done">
          <div className="column-header column-header-done">
            <h3 style={{ display: 'flex', alignItems: 'center', gap: '6px' }}><CheckCircle size={16} /> Done ({doneTasks.length})</h3>
          </div>
          {doneTasks.map((task) => (
            <TodayTaskCard key={task.id} task={task} onStatusChange={handleStatusChange}
              onRemove={handleToggleToday} formatTime={formatTime} onReload={loadTasks} />
          ))}
        </div>
      </div>
    </div>
  );
}

function TodayTaskCard({ task, onStatusChange, onRemove, formatTime, onReload }) {
  const [isExpanded, setIsExpanded] = useState(false);

  return (
    <div className="today-task-card" onClick={() => setIsExpanded(!isExpanded)} style={{ cursor: 'pointer', background: isExpanded ? 'var(--bg-card-hover)' : 'var(--bg-card)' }}>
      <div className="task-card-header">
        <span className="task-card-title">{task.title}</span>
        <div style={{ display: 'flex', gap: '6px' }}>
          <button className="btn-icon" onClick={(e) => { e.stopPropagation(); setIsExpanded(!isExpanded); }} title="Details">
            <FileText size={14} />
          </button>
          <button className="btn-icon" onClick={(e) => { e.stopPropagation(); onRemove(task.id); }} title="Remove from today">
            <X size={14} />
          </button>
        </div>
      </div>
      <div className="task-card-meta">
        <span className="text-muted text-sm">{task.project_name}</span>
        <PriorityBadge priority={task.priority} />
      </div>
      
      {isExpanded && (
        <div className="task-details-pane" style={{ marginTop: '12px', paddingTop: '12px', borderTop: '1px solid var(--border-subtle)', display: 'flex', flexDirection: 'column', gap: '8px' }}>
          <div>
            <h4 style={{ fontSize: '0.75rem', color: 'var(--text-muted)', textTransform: 'uppercase', marginBottom: '2px' }}>Notes</h4>
            <p style={{ fontSize: '0.85rem', color: 'var(--text-primary)', whiteSpace: 'pre-wrap' }}>
              {task.description || <span className="text-muted italic">No description</span>}
            </p>
          </div>
          <div style={{ display: 'flex', gap: '16px' }}>
            <span style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>Est: <strong style={{ color: 'var(--text-primary)' }}>{task.estimated_hours ? `${task.estimated_hours}h` : '--'}</strong></span>
            <span style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>Logged: <strong style={{ color: 'var(--success)' }}>{formatTime(task.total_time_spent)}</strong></span>
          </div>
        </div>
      )}

      <div className="task-card-footer" style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginTop: '12px', flexWrap: 'wrap', gap: '8px' }} onClick={(e) => e.stopPropagation()}>
        <Timer taskId={task.id} taskTitle={task.title} initialSeconds={task.total_time_spent} onStop={onReload} />
        {task.status !== 'done' && (
          <button className="btn btn-sm btn-primary" onClick={() => onStatusChange(task.id, 'done')} style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
            <CheckCircle size={14} /> Done
          </button>
        )}
      </div>
    </div>
  );
}
