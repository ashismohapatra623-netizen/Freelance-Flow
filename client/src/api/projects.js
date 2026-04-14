import api from './client';

export const projectsApi = {
  list: (params) => api.get('/projects', { params }),
  get: (id) => api.get(`/projects/${id}`),
  create: (data) => api.post('/projects', data),
  update: (id, data) => api.put(`/projects/${id}`, data),
  delete: (id) => api.delete(`/projects/${id}`),
  changeStatus: (id, status) => api.patch(`/projects/${id}/status`, { status }),
  getSummary: (id) => api.get(`/projects/${id}/summary`),
};
