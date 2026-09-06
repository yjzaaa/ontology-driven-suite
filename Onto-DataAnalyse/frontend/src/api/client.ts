import axios from 'axios';

export const apiClient = axios.create({
  baseURL: '/api',
  timeout: 30000,
  headers: { 'Content-Type': 'application/json' },
});

apiClient.interceptors.response.use(
  (resp) => resp,
  (error) => {
    const message = error?.response?.data?.message || error.message || '请求失败';
    return Promise.reject(new Error(message));
  },
);
