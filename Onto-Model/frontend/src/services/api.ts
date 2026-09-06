import axios from 'axios';
import { Workspace } from '../types/models';

const API_BASE_URL = 'http://localhost:5000/api';

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

export const workspaceApi = {
  openWorkspace: async (directory: string) => {
    const response = await api.post('/workspace/open', { directory });
    return response.data;
  },

  saveWorkspace: async (workspace: Workspace, options?: any) => {
    const response = await api.post('/workspace/save', { workspace, options });
    return response.data;
  },

  getCurrentWorkspace: async () => {
    const response = await api.get('/workspace/current');
    return response.data;
  },

  scanWorkspaces: async (root?: string) => {
    const response = await api.post('/workspace/scan', { root });
    return response.data;
  },
};

export const validationApi = {
  runValidation: async (workspace: Workspace) => {
    const response = await api.post('/validation/run', { workspace });
    return response.data;
  },
};

export const referenceApi = {
  findReferences: async (nodeType: string, nodeId: string) => {
    const response = await api.post('/references/find', { nodeType, nodeId });
    return response.data;
  },

  analyzeDeleteImpact: async (nodeType: string, nodeId: string) => {
    const response = await api.post('/references/delete-impact', { nodeType, nodeId });
    return response.data;
  },
};

export default api;
