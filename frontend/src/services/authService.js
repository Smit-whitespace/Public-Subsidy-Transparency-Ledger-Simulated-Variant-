import apiClient, { setAuthToken } from "./apiClient";

const TOKEN_KEY = "pstl_token";
const USER_KEY = "pstl_user";

export async function login(username, password) {

  const formData = new URLSearchParams();
  formData.append("username", username);
  formData.append("password", password);

  const response = await apiClient.post("/auth/login", formData, {
    headers: {
      "Content-Type": "application/x-www-form-urlencoded"
    }
  });

  return response.data;

}

export async function getCurrentUser(token) {

  setAuthToken(token);

  const response = await apiClient.get("/auth/me");

  return response.data;

}

export function saveAuth(token, user) {

  localStorage.setItem(TOKEN_KEY, token);
  localStorage.setItem(USER_KEY, JSON.stringify(user));

}

export function loadAuth() {

  const token = localStorage.getItem(TOKEN_KEY);
  const user = localStorage.getItem(USER_KEY);

  return {
    token,
    user: user ? JSON.parse(user) : null
  };

}

export function logout() {

  localStorage.removeItem(TOKEN_KEY);
  localStorage.removeItem(USER_KEY);
  setAuthToken(null);

}

export async function register(username, password, role = "auditor") {

  const response = await apiClient.post("/auth/register", {
    username,
    password,
    role
  });

  return response.data;

}