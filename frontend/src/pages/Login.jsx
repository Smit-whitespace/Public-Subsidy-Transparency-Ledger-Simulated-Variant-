import React, { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";

import Navbar from "../components/Navbar";
import Loader from "../components/Loader";
import Toast from "../components/Toast";

import { useAuth } from "../context/AuthContext";

export default function Login() {

  const { login, loading, error, isAuthenticated } = useAuth();
  const navigate = useNavigate();

  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [showError, setShowError] = useState(false);

  useEffect(() => {

    if (isAuthenticated) {
      navigate("/dashboard", { replace: true });
    }

  }, [isAuthenticated, navigate]);

  async function handleSubmit(e) {

    e.preventDefault();

    if (loading) return;

    setShowError(false);

    try {

      await login(username, password);

      navigate("/dashboard", { replace: true });

    } catch (err) {

      setShowError(true);

    }

  }

  return (
    <div className="login-page">

      <Navbar />

      <main className="login-content">

        <h1>Login</h1>

        {loading && (
          <Loader message="Authenticating..." />
        )}

        <form
          className="login-form"
          onSubmit={handleSubmit}
        >

          <label>

            Username

            <input
              type="text"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              required
            />

          </label>

          <label>

            Password

            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
            />

          </label>

          <button
            type="submit"
            disabled={loading}
          >
            {loading ? "Signing in..." : "Login"}
          </button>

        </form>

        <Toast
          visible={showError}
          message={error || "Login failed"}
          type="error"
          onClose={() => setShowError(false)}
        />

      </main>

    </div>
  );
}