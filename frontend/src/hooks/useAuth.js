import { useState, useEffect, useCallback } from "react";

import {
  login as apiLogin,
  logout as apiLogout,
  getCurrentUser,
  saveAuth,
  loadAuth
} from "../services/authService";

import { setAuthToken } from "../services/apiClient";

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

          // Set token BEFORE making API calls
          setAuthToken(savedToken);
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

  // Set auth token on apiClient whenever token changes
  useEffect(() => {
    setAuthToken(token);
  }, [token]);

  const login = useCallback(async (username, password) => {

    setLoading(true);
    setError(null);

    try {

      const loginResponse = await apiLogin(username, password);

      const accessToken = loginResponse?.access_token;

      if (!accessToken) {
        throw new Error("No access token received");
      }

      const currentUser = await getCurrentUser(accessToken);

      setToken(accessToken);
      setUser(currentUser);

      saveAuth(accessToken, currentUser);

    } catch (err) {

      const errorMessage = err?.message || "Login failed";

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

  // Helper to check if user has a specific role
  const hasRole = useCallback((role) => {
    if (!user || !user.roles) return false;
    if (Array.isArray(role)) {
      return role.some(r => user.roles.includes(r));
    }
    return user.roles.includes(role);
  }, [user]);

  // Helper to check if user has any of the required roles
  const hasAnyRole = useCallback((roles) => {
    return hasRole(roles);
  }, [hasRole]);

  // Helper to check if user is admin
  const isAdmin = useCallback(() => hasRole('admin'), [hasRole]);

  // Helper to check if user can access admin features
  const canAccessAdmin = useCallback(() => hasRole(['admin', 'government_official']), [hasRole]);

  // Helper to check if user can investigate
  const canInvestigate = useCallback(() => hasRole(['admin', 'auditor', 'media']), [hasRole]);

  return {

    user,
    token,

    loading,
    error,

    isAuthenticated: Boolean(token),
    roles: user?.roles || [],

    hasRole,
    hasAnyRole,
    isAdmin,
    canAccessAdmin,
    canInvestigate,

    login,
    logout

  };

}