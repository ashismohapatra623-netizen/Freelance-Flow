import api from './client';

export const timeEntriesApi = {
  start: (taskId, note) => api.post('/time-entries', { task_id: taskId, note }),
  stop: (entryId, note) => api.put(`/time-entries/${entryId}/stop`, { note }),
  list: () => api.get('/time-entries'),
  get: (id) => api.get(`/time-entries/${id}`),
  delete: (id) => api.delete(`/time-entries/${id}`),
};
