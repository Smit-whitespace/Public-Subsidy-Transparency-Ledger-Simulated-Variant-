import apiClient, { setAuthToken } from "./apiClient";

const TOKEN_KEY = "pstl_token";
const USER_KEY = "pstl_user";

/* -------------------------------------------------------
   LOGIN
------------------------------------------------------- */

export async function login(username, password) {

  const formData = new URLSearchParams();
  formData.append("username", username);
  formData.append("password", password);

  const response = await apiClient.post("/auth/login", formData, {
    headers: {
      "Content-Type": "application/x-www-form-urlencoded"
    }
  });

  const token = response.data.access_token;

  if (token) {
    setAuthToken(token);
    localStorage.setItem(TOKEN_KEY, token);
  }

  return response.data;

}

/* -------------------------------------------------------
   CURRENT USER
------------------------------------------------------- */

export async function getCurrentUser() {

  const token = localStorage.getItem(TOKEN_KEY);

  if (!token) {
    throw new Error("No auth token found");
  }

  setAuthToken(token);

  const response = await apiClient.get("/auth/me");

  const user = response.data;

  localStorage.setItem(USER_KEY, JSON.stringify(user));

  return user;

}

/* -------------------------------------------------------
   SAVE AUTH (MANUAL)
------------------------------------------------------- */

export function saveAuth(token, user) {

  if (token) {
    localStorage.setItem(TOKEN_KEY, token);
    setAuthToken(token);
  }

  if (user) {
    localStorage.setItem(USER_KEY, JSON.stringify(user));
  }

}

/* -------------------------------------------------------
   LOAD AUTH
------------------------------------------------------- */

export function loadAuth() {

  const token = localStorage.getItem(TOKEN_KEY);
  const user = localStorage.getItem(USER_KEY);

  if (token) {
    setAuthToken(token);
  }

  return {
    token,
    user: user ? JSON.parse(user) : null
  };

}

/* -------------------------------------------------------
   LOGOUT
------------------------------------------------------- */

export function logout() {

  localStorage.removeItem(TOKEN_KEY);
  localStorage.removeItem(USER_KEY);

  setAuthToken(null);

}

/* -------------------------------------------------------
   REGISTER
------------------------------------------------------- */

export async function register(username, password, role = "auditor") {

  const response = await apiClient.post("/auth/register", {
    username,
    password,
    role
  });

  return response.data;

}