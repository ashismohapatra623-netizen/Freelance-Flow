import api from './client';

export const tasksApi = {
  list: (params) => api.get('/tasks', { params }),
  get: (id) => api.get(`/tasks/${id}`),
  create: (data) => api.post('/tasks', data),
  update: (id, data) => api.put(`/tasks/${id}`, data),
  delete: (id) => api.delete(`/tasks/${id}`),
  changeStatus: (id, status) => api.patch(`/tasks/${id}/status`, { status }),
  toggleToday: (id) => api.patch(`/tasks/${id}/today`),
  getToday: () => api.get('/tasks/today/list'),
  getSummary: (id) => api.get(`/tasks/${id}/summary`),
};
