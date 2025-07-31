import axios from 'axios';

// Create axios instance with base URL
const axiosInstance = axios.create({
  baseURL: 'http://127.0.0.1:8000',
  timeout: 1000000,
});

// Request interceptor
axiosInstance.interceptors.request.use(
  (config) => {
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Response interceptor
axiosInstance.interceptors.response.use(
  (response) => {
    return response;
  },
  (error) => {
    return Promise.reject(error);
  }
);

export default axiosInstance;