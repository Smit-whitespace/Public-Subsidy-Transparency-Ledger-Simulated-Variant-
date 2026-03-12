import React, { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { Shield, Eye, Radio, Globe, UserCog } from "lucide-react";

import Navbar from "../components/Navbar";
import Loader from "../components/Loader";
import Toast from "../components/Toast";

import { useAuth } from "../context/AuthContext";

const ROLE_INFO = [
  { role: "admin", label: "Administrator", icon: Shield, description: "Full system access, create/edit records" },
  { role: "auditor", label: "Auditor", icon: Eye, description: "View all data, investigation tools" },
  { role: "official", label: "Government Official", icon: UserCog, description: "Subsidy monitoring, approvals" },
  { role: "media", label: "Media", icon: Radio, description: "Investigation, public transparency" },
];

export default function Login() {

  const { login, loading, error, isAuthenticated } = useAuth();
  const navigate = useNavigate();

  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [selectedRole, setSelectedRole] = useState("admin");
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

      // Route based on selected role
      const roleRoutes = {
        admin: "/dashboard",
        auditor: "/dashboard",
        official: "/subsidies",
        media: "/investigation"
      };
      navigate(roleRoutes[selectedRole] || "/dashboard", { replace: true });

    } catch (err) {

      setShowError(true);

    }

  }

  const selectedRoleInfo = ROLE_INFO.find(r => r.role === selectedRole);

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

          {/* Role Selection */}
          <div className="role-selection">
            <label className="role-label">Select Your Role (Demo)</label>
            <div className="role-options">
              {ROLE_INFO.map((roleInfo) => {
                const Icon = roleInfo.icon;
                return (
                  <div
                    key={roleInfo.role}
                    className={`role-option ${selectedRole === roleInfo.role ? 'selected' : ''}`}
                    onClick={() => setSelectedRole(roleInfo.role)}
                  >
                    <Icon size={18} />
                    <span className="role-option-label">{roleInfo.label}</span>
                  </div>
                );
              })}
            </div>
            {selectedRoleInfo && (
              <div className="role-description">
                {selectedRoleInfo.description}
              </div>
            )}
          </div>

          <label>

            Username

            <input
              type="text"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              placeholder="admin, auditor, official, or media"
              required
            />

          </label>

          <label>

            Password

            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="admin123"
              required
            />

          </label>

          <button
            type="submit"
            disabled={loading}
          >
            {loading ? "Signing in..." : `Login as ${selectedRoleInfo?.label || 'User'}`}
          </button>

        </form>

        <Toast
          visible={showError}
          message={error || "Login failed"}
          type="error"
          onClose={() => setShowError(false)}
        />

        <div className="login-footer">
          <p>Don't have an account? <a href="/register" className="register-link">Register here</a></p>
        </div>

      </main>

    </div>
  );
}