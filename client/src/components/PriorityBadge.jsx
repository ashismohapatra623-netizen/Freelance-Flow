export default function PriorityBadge({ priority }) {
  const map = {
    low: 'priority-low',
    medium: 'priority-medium',
    high: 'priority-high',
  };
  return <span className={`badge ${map[priority] || 'badge-default'}`}>{priority}</span>;
}
