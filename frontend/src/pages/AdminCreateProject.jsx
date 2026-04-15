import React, { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { Plus, ArrowLeft, Loader } from "lucide-react";

import Navbar from "../components/Navbar";
import Sidebar from "../components/Sidebar";
import Toast from "../components/Toast";
import { useAuth } from "../context/AuthContext";
import apiClient from "../services/apiClient";
import { fetchSubsidies } from "../services/subsidyService";

const STATUSES = ["planned", "active", "completed", "paused", "cancelled"];

export default function AdminCreateProject() {
  const navigate = useNavigate();
  const { token } = useAuth();
  
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [success, setSuccess] = useState(false);
  const [subsidies, setSubsidies] = useState([]);
  
  const [formData, setFormData] = useState({
    name: "",
    subsidy_id: "",
    description: "",
    owner: "",
    status: "planned"
  });

  useEffect(() => {
    async function loadSubsidies() {
      try {
        const data = await fetchSubsidies({ limit: 100, token });
        setSubsidies(Array.isArray(data) ? data : data.data || []);
      } catch (err) {
        console.error("Failed to load subsidies:", err);
      }
    }
    if (token) loadSubsidies();
  }, [token]);

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({ ...prev, [name]: value }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError(null);
    setSuccess(false);

    try {
      const payload = {
        ...formData,
        subsidy_id: formData.subsidy_id ? parseInt(formData.subsidy_id) : null
      };
      
      await apiClient.post("/projects/", payload, {
        headers: { Authorization: `Bearer ${token}` }
      });
      
      setSuccess(true);
      setTimeout(() => navigate("/projects"), 1500);
    } catch (err) {
      setError(err.response?.data?.detail || "Failed to create project");
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
            <ArrowLeft size={16} /> Back
          </button>

          <h1>Create New Project</h1>
          <p>Add a new project linked to a subsidy</p>

          <form className="create-form" onSubmit={handleSubmit}>
            <div className="form-group">
              <label>Project Name *</label>
              <input
                type="text"
                name="name"
                value={formData.name}
                onChange={handleChange}
                required
                placeholder="e.g., Rural Electrification Phase 1"
              />
            </div>

            <div className="form-group">
              <label>Linked Subsidy</label>
              <select
                name="subsidy_id"
                value={formData.subsidy_id}
                onChange={handleChange}
              >
                <option value="">Select a subsidy (optional)</option>
                {subsidies.map(s => (
                  <option key={s.id} value={s.id}>{s.title}</option>
                ))}
              </select>
            </div>

            <div className="form-row">
              <div className="form-group">
                <label>Owner / Department *</label>
                <input
                  type="text"
                  name="owner"
                  value={formData.owner}
                  onChange={handleChange}
                  required
                  placeholder="e.g., District Administration"
                />
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

            <div className="form-group">
              <label>Description</label>
              <textarea
                name="description"
                value={formData.description}
                onChange={handleChange}
                rows="3"
                placeholder="Describe the project objectives..."
              />
            </div>

            <div className="form-actions">
              <button type="submit" className="btn-primary" disabled={loading}>
                {loading ? <><Loader size={16} className="spin" /> Creating...</> : <><Plus size={16} /> Create Project</>}
              </button>
              <button type="button" className="btn-secondary" onClick={() => navigate(-1)}>
                Cancel
              </button>
            </div>
          </form>

          <Toast visible={success} message="Project created successfully!" type="success" onClose={() => setSuccess(false)} />
          <Toast visible={!!error} message={error} type="error" onClose={() => setError(null)} />
        </main>
      </div>
    </div>
  );
}