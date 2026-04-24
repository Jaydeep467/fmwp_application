import axios from "axios";

const API_BASE = import.meta.env.VITE_API_URL || "http://localhost:8000/api/v1";

const api = axios.create({ baseURL: API_BASE });

api.interceptors.request.use((config) => {
  const token = localStorage.getItem("fmwp_token");
  if (token) config.headers.Authorization = `Bearer ${token}`;
  return config;
});

api.interceptors.response.use(
  (res) => res,
  (err) => {
    if (err.response?.status === 401) {
      localStorage.removeItem("fmwp_token");
      window.location.href = "/login";
    }
    return Promise.reject(err);
  }
);

export const authAPI = {
  register: (data) => api.post("/auth/register", data),
  login:    (data) => api.post("/auth/login", data),
  me:       ()     => api.get("/auth/me"),
};

export const accountsAPI = {
  getAll: ()     => api.get("/accounts"),
  create: (data) => api.post("/accounts", data),
};

export const transactionsAPI = {
  getAll:      (params) => api.get("/transactions", { params }),
  create:      (data)   => api.post("/transactions", data),
  getAnomalies: ()      => api.get("/transactions/anomalies"),
  getSpending: (month, year) => api.get("/transactions/analytics/spending", { params: { month, year } }),
  getTrend:    (months) => api.get("/transactions/analytics/trend", { params: { months } }),
};

export const exportAPI = {
  csv: () => api.get("/export/csv", { responseType: "blob" }),
  pdf: () => api.get("/export/pdf", { responseType: "blob" }),
};

export default api;