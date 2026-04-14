import { Inbox } from 'lucide-react';

export default function EmptyState({ icon = <Inbox size={48} className="text-muted" />, message, action, onAction }) {
  return (
    <div className="empty-state">
      <div className="empty-icon" style={{ marginBottom: '16px', display: 'flex', justifyContent: 'center' }}>{icon}</div>
      <p className="empty-message">{message}</p>
      {action && (
        <button className="btn btn-primary" onClick={onAction}>
          {action}
        </button>
      )}
    </div>
  );
}
