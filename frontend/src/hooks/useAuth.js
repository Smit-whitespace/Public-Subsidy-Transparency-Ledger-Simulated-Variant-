import { useState, useEffect, useCallback } from "react";
import {
  login as apiLogin,
  logout as apiLogout,
  getCurrentUser,
  saveAuth,
  loadAuth
} from "../api/auth";

export default function useAuth() {
  const [user, setUser] = useState(null);
  const [token, setToken] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    async function initializeAuth() {
      setLoading(true);
      try {
        const { token: savedToken, user: savedUser } = loadAuth();

        if (savedToken) {
          setToken(savedToken);

          try {
            const freshUser = await getCurrentUser(savedToken);
            setUser(freshUser);
            saveAuth(savedToken, freshUser);
          } catch (err) {
            setToken(null);
            setUser(null);
            apiLogout();
          }
        } else {
          setToken(null);
          setUser(null);
        }
      } catch (err) {
        setToken(null);
        setUser(null);
      } finally {
        setLoading(false);
      }
    }

    initializeAuth();
  }, []);

  const login = useCallback(async (username, password) => {
    setLoading(true);
    setError(null);

    try {
      const loginResponse = await apiLogin(username, password);
      const accessToken = loginResponse.access_token;

      if (!accessToken) {
        throw new Error("No access token received");
      }

      const currentUser = await getCurrentUser(accessToken);

      setToken(accessToken);
      setUser(currentUser);
      saveAuth(accessToken, currentUser);
    } catch (err) {
      const errorMessage = err.message || "Login failed";
      setError(errorMessage);
      setToken(null);
      setUser(null);
      apiLogout();
      throw err;
    } finally {
      setLoading(false);
    }
  }, []);

  const logout = useCallback(() => {
    apiLogout();
    setToken(null);
    setUser(null);
    setError(null);
  }, []);

  return {
    user,
    token,
    loading,
    error,
    isAuthenticated: Boolean(token),
    login,
    logout
  };
}