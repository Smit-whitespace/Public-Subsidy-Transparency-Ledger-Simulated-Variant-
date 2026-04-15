import React, { useState } from "react";
import { useNavigate } from "react-router-dom";
import { Plus, ArrowLeft, Loader } from "lucide-react";

import Navbar from "../components/Navbar";
import Sidebar from "../components/Sidebar";
import Toast from "../components/Toast";
import { useAuth } from "../context/AuthContext";
import apiClient from "../services/apiClient";

const SECTORS = [
  "Agriculture",
  "Education", 
  "Healthcare",
  "Infrastructure",
  "MSME",
  "Renewable Energy",
  "Social Welfare"
];

const STATUSES = ["planned", "active", "completed", "expired", "suspended"];

export default function AdminCreateSubsidy() {
  const navigate = useNavigate();
  const { token } = useAuth();
  
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [success, setSuccess] = useState(false);
  
  const [formData, setFormData] = useState({
    title: "",
    recipient: "",
    sector: "Agriculture",
    total_allocation: "",
    currency: "INR",
    description: "",
    status: "active",
    is_active: true
  });

  const handleChange = (e) => {
    const { name, value, type, checked } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: type === "checkbox" ? checked : value
    }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError(null);
    setSuccess(false);

    try {
      const payload = {
        ...formData,
        total_allocation: parseFloat(formData.total_allocation)
      };
      
      await apiClient.post("/subsidies/", payload, {
        headers: { Authorization: `Bearer ${token}` }
      });
      
      setSuccess(true);
      setTimeout(() => navigate("/subsidies"), 1500);
    } catch (err) {
      setError(err.response?.data?.detail || "Failed to create subsidy");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="subsidy-details">
      <Navbar />
      <div className="subsidy-layout">
        <Sidebar />
        <main className="subsidy-content">
          <button className="back-link" onClick={() => navigate(-1)}>
            <ArrowLeft size={16} /> Back to Dashboard
          </button>

          <h1>Create New Subsidy</h1>
          <p>Add a new subsidy program to the system</p>

          <form className="create-form" onSubmit={handleSubmit}>
            <div className="form-group">
              <label>Title *</label>
              <input
                type="text"
                name="title"
                value={formData.title}
                onChange={handleChange}
                required
                placeholder="e.g., PM-KISAN Support 2024"
              />
            </div>

            <div className="form-group">
              <label>Recipient *</label>
              <input
                type="text"
                name="recipient"
                value={formData.recipient}
                onChange={handleChange}
                required
                placeholder="e.g., Rural Development Authority"
              />
            </div>

            <div className="form-row">
              <div className="form-group">
                <label>Sector *</label>
                <select
                  name="sector"
                  value={formData.sector}
                  onChange={handleChange}
                  required
                >
                  {SECTORS.map(s => (
                    <option key={s} value={s}>{s}</option>
                  ))}
                </select>
              </div>

              <div className="form-group">
                <label>Status *</label>
                <select
                  name="status"
                  value={formData.status}
                  onChange={handleChange}
                  required
                >
                  {STATUSES.map(s => (
                    <option key={s} value={s}>{s.charAt(0).toUpperCase() + s.slice(1)}</option>
                  ))}
                </select>
              </div>
            </div>

            <div className="form-row">
              <div className="form-group">
                <label>Total Allocation (INR) *</label>
                <input
                  type="number"
                  name="total_allocation"
                  value={formData.total_allocation}
                  onChange={handleChange}
                  required
                  min="1"
                  step="0.01"
                  placeholder="e.g., 5000000"
                />
              </div>

              <div className="form-group">
                <label>Currency</label>
                <input
                  type="text"
                  name="currency"
                  value={formData.currency}
                  onChange={handleChange}
                  disabled
                />
              </div>
            </div>

            <div className="form-group">
              <label>Description</label>
              <textarea
                name="description"
                value={formData.description}
                onChange={handleChange}
                rows="3"
                placeholder="Describe the subsidy program..."
              />
            </div>

            <div className="form-group checkbox-group">
              <label>
                <input
                  type="checkbox"
                  name="is_active"
                  checked={formData.is_active}
                  onChange={handleChange}
                />
                Active
              </label>
            </div>

            <div className="form-actions">
              <button type="submit" className="btn-primary" disabled={loading}>
                {loading ? <><Loader size={16} className="spin" /> Creating...</> : <><Plus size={16} /> Create Subsidy</>}
              </button>
              <button type="button" className="btn-secondary" onClick={() => navigate(-1)}>
                Cancel
              </button>
            </div>
          </form>

          <Toast
            visible={success}
            message="Subsidy created successfully!"
            type="success"
            onClose={() => setSuccess(false)}
          />
          <Toast
            visible={!!error}
            message={error}
            type="error"
            onClose={() => setError(null)}
          />
        </main>
      </div>
    </div>
  );
}