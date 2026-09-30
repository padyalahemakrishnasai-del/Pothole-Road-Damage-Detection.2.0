/**
 * API service layer for communicating with the AI RoadGuard backend.
 * All backend calls go through this module for centralized error handling.
 */
import axios from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_URL || '';

const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 120000, // 2 minutes for large video uploads
});

// Response interceptor for error handling
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response) {
      console.error('API Error:', error.response.status, error.response.data);
    } else if (error.request) {
      console.error('Network Error: Backend is not reachable');
    }
    return Promise.reject(error);
  }
);

/** Check API health */
export const checkHealth = () => api.get('/health');

/** Get model information */
export const getModelInfo = () => api.get('/api/model/info');

/** Analyze an image for road damage */
export const analyzeImage = (file, onProgress) => {
  const formData = new FormData();
  formData.append('file', file);
  return api.post('/api/analyze/image', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
    onUploadProgress: onProgress,
  });
};

/** Analyze a video for road damage */
export const analyzeVideo = (file, onProgress) => {
  const formData = new FormData();
  formData.append('file', file);
  return api.post('/api/analyze/video', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
    onUploadProgress: onProgress,
  });
};

/** Get a specific analysis result */
export const getAnalysis = (analysisId) => api.get(`/api/analysis/${analysisId}`);

/** Get analysis history */
export const getHistory = () => api.get('/api/history');

/** Get dashboard statistics */
export const getDashboard = () => api.get('/api/dashboard/stats');

/** Delete an analysis record */
export const deleteAnalysis = (analysisId) => api.delete(`/api/analysis/${analysisId}`);

/** Get direct download URL for PDF inspection report */
export const getReportUrl = (analysisId) => `${API_BASE_URL}/api/analysis/${analysisId}/report`;

/** Get the output file URL */
export const getOutputUrl = (path) => {
  if (!path) return '';
  if (path.startsWith('http://') || path.startsWith('https://')) return path;
  return `${API_BASE_URL}${path}`;
};

export default api;
