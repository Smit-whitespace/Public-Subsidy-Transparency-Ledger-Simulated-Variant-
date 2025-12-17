const API_BASE_URL = import.meta?.env?.VITE_API_BASE_URL || "http://localhost:8000";
const AUTH_BASE_PATH = "/auth";

async function request(url, options = {}) {
  const headers = {
    "Content-Type": "application/json",
    "Accept": "application/json"
  };

  if (options.token) {
    headers["Authorization"] = `Bearer ${options.token}`;
  }

  const fetchOptions = {
    method: options.method || "POST",
    headers,
    ...options
  };

  if (options.body && typeof options.body === "object") {
    fetchOptions.body = JSON.stringify(options.body);
  }

  const response = await fetch(url, fetchOptions);

  if (!response.ok) {
    let errorMessage = "Authentication request failed";
    try {
      const errorData = await response.json();
      errorMessage = errorData.detail || errorData.message || errorMessage;
    } catch (_) {
      errorMessage = `Request failed with status ${response.status}`;
    }
    throw new Error(errorMessage);
  }

  return await response.json();
}

export async function login(username, password) {
  if (!username) {
    throw new Error("username is required");
  }
  if (!password) {
    throw new Error("password is required");
  }

  const url = `${API_BASE_URL}${AUTH_BASE_PATH}/login`;
  const body = { username, password };

  return await request(url, { method: "POST", body });
}

export async function getCurrentUser(token) {
  if (!token) {
    throw new Error("token is required");
  }

  const url = `${API_BASE_URL}${AUTH_BASE_PATH}/me`;
  return await request(url, { method: "GET", token });
}

export async function refreshToken(token) {
  if (!token) {
    throw new Error("token is required");
  }

  const url = `${API_BASE_URL}${AUTH_BASE_PATH}/refresh`;
  return await request(url, { method: "POST", token });
}

export function logout() {
  try {
    localStorage.removeItem("access_token");
    localStorage.removeItem("user");
  } catch (_) {
    // Silently fail if localStorage is unavailable
  }
}

export function saveAuth(token, user) {
  try {
    if (token) {
      localStorage.setItem("access_token", token);
    }
    if (user) {
      localStorage.setItem("user", JSON.stringify(user));
    }
  } catch (_) {
    // Silently fail if localStorage is unavailable
  }
}

export function loadAuth() {
  try {
    const token = localStorage.getItem("access_token");
    const userStr = localStorage.getItem("user");
    const user = userStr ? JSON.parse(userStr) : null;
    return { token, user };
  } catch (_) {
    return { token: null, user: null };
  }
}