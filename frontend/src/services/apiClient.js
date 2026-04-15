import axios from "axios";

const API_BASE = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000";

const apiClient = axios.create({
  baseURL: API_BASE,
  headers: {
    "Content-Type": "application/json",
    Accept: "application/json"
  }
});

/* -----------------------------
   AUTH TOKEN HANDLER
------------------------------ */

export function setAuthToken(token) {

  if (token) {
    apiClient.defaults.headers.common["Authorization"] = `Bearer ${token}`;
  } else {
    delete apiClient.defaults.headers.common["Authorization"];
  }

}

/* -----------------------------
   LOAD TOKEN ON APP START
------------------------------ */

const storedToken =
  localStorage.getItem("pstl_token") ||
  localStorage.getItem("access_token");

if (storedToken) {
  setAuthToken(storedToken);
}

/* -----------------------------
   RESPONSE INTERCEPTOR
------------------------------ */

apiClient.interceptors.response.use(
  (response) => response,
  (error) => {

    if (error.response && error.response.status === 401) {

      console.warn("Authentication expired. Logging out.");

      localStorage.removeItem("pstl_token");
      localStorage.removeItem("pstl_user");

      window.location.href = "/login";

    }

    return Promise.reject(error);
  }
);

export default apiClient;