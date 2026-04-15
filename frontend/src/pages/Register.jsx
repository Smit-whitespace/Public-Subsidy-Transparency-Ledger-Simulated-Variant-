import React, { useState } from "react";
import { useNavigate, Link } from "react-router-dom";
import { Shield, Eye, UserCog, Globe, Radio } from "lucide-react";
import Navbar from "../components/Navbar";
import Toast from "../components/Toast";
import { register } from "../services/authService";

const ROLE_OPTIONS = [
  { value: "public", label: "Public Citizen", icon: Globe, description: "View transparency portal, search subsidies" },
  { value: "media", label: "Media", icon: Radio, description: "Analytics, reports, dataset access" },
  { value: "auditor", label: "Auditor", icon: Eye, description: "Audit logs, anomaly investigation, risk analysis" },
  { value: "government_official", label: "Government Official", icon: UserCog, description: "Create subsidies, manage projects, disburse funds" },
  { value: "admin", label: "Administrator", icon: Shield, description: "Full system access, user management" },
];

export default function Register() {
  const navigate = useNavigate();
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [selectedRole, setSelectedRole] = useState("auditor");
  const [loading, setLoading] = useState(false);
  const [showError, setShowError] = useState(false);
  const [error, setError] = useState("");
  const [success, setSuccess] = useState(false);

  async function handleSubmit(e) {
    e.preventDefault();
    
    if (password !== confirmPassword) {
      setError("Passwords do not match");
      setShowError(true);
      return;
    }

    if (password.length < 6) {
      setError("Password must be at least 6 characters");
      setShowError(true);
      return;
    }

    setLoading(true);
    setShowError(false);

    try {
      await register(username, password, selectedRole);
      setSuccess(true);
      setTimeout(() => {
        navigate("/login");
      }, 1500);
    } catch (err) {
      setError(err.response?.data?.detail || "Registration failed");
      setShowError(true);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="login-page">
      <Navbar />
      <main className="login-content">
        <h1>Create Account</h1>

        {success && (
          <Toast
            visible={true}
            message="Registration successful! Redirecting to login..."
            type="success"
          />
        )}

        <form className="login-form" onSubmit={handleSubmit}>
          {/* Role Selection */}
          <div className="role-selection">
            <label className="role-label">Select Your Role</label>
            <div className="role-options">
              {ROLE_OPTIONS.map((role) => {
                const Icon = role.icon;
                return (
                  <div
                    key={role.value}
                    className={`role-option ${selectedRole === role.value ? 'selected' : ''}`}
                    onClick={() => setSelectedRole(role.value)}
                  >
                    <Icon size={18} />
                    <span className="role-option-label">{role.label}</span>
                  </div>
                );
              })}
            </div>
            <div className="role-description">
              {ROLE_OPTIONS.find(r => r.value === selectedRole)?.description}
            </div>
          </div>

          <label>
            Username
            <input
              type="text"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              placeholder="Choose a username"
              required
            />
          </label>

          <label>
            Password
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="At least 6 characters"
              required
            />
          </label>

          <label>
            Confirm Password
            <input
              type="password"
              value={confirmPassword}
              onChange={(e) => setConfirmPassword(e.target.value)}
              placeholder="Re-enter password"
              required
            />
          </label>

          <button type="submit" disabled={loading}>
            {loading ? "Creating account..." : "Register"}
          </button>
        </form>

        <Toast
          visible={showError}
          message={error}
          type="error"
          onClose={() => setShowError(false)}
        />

        <div className="login-footer">
          <p>Already have an account? <Link to="/login" className="register-link">Login here</Link></p>
        </div>
      </main>
    </div>
  );
}