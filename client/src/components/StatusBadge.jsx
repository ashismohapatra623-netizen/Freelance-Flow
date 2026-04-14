export default function StatusBadge({ status, type = 'task' }) {
  const getClass = () => {
    if (type === 'client') {
      return status === 'active' ? 'badge-active' : 'badge-inactive';
    }
    const map = {
      'todo': 'badge-todo',
      'in-progress': 'badge-in-progress',
      'done': 'badge-done',
      'active': 'badge-active',
      'on-hold': 'badge-on-hold',
      'completed': 'badge-done',
      'inactive': 'badge-inactive',
    };
    return map[status] || 'badge-default';
  };

  return <span className={`badge ${getClass()}`}>{status}</span>;
}
