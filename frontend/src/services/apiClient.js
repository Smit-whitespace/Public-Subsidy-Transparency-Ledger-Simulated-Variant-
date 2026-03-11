import axios from "axios";

const API_BASE = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000";

const apiClient = axios.create({
  baseURL: API_BASE,
  headers: {
    "Content-Type": "application/json",
    Accept: "application/json"
  }
});

/* ---------- AUTH TOKEN HANDLER ---------- */

export function setAuthToken(token) {

  if (token) {
    apiClient.defaults.headers.common["Authorization"] = `Bearer ${token}`;
  } else {
    delete apiClient.defaults.headers.common["Authorization"];
  }

}

/* ---------- EXPORT CLIENT ---------- */

export default apiClient;