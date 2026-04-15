import React, { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { Plus, ArrowLeft, Loader } from "lucide-react";

import Navbar from "../components/Navbar";
import Sidebar from "../components/Sidebar";
import Toast from "../components/Toast";
import { useAuth } from "../context/AuthContext";
import apiClient from "../services/apiClient";
import { fetchSubsidies } from "../services/subsidyService";

const APPROVAL_STATUSES = ["pending", "approved", "rejected"];

export default function AdminCreateDisbursement() {
  const navigate = useNavigate();
  const { token } = useAuth();
  
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [success, setSuccess] = useState(false);
  const [subsidies, setSubsidies] = useState([]);
  
  const [formData, setFormData] = useState({
    subsidy_id: "",
    amount: "",
    reference: "",
    approval_status: "approved",
    notes: ""
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
        subsidy_id: formData.subsidy_id ? parseInt(formData.subsidy_id) : null,
        amount: parseFloat(formData.amount)
      };
      
      await apiClient.post("/disbursements/", payload, {
        headers: { Authorization: `Bearer ${token}` }
      });
      
      setSuccess(true);
      setTimeout(() => navigate("/disbursements"), 1500);
    } catch (err) {
      setError(err.response?.data?.detail || "Failed to create disbursement");
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

          <h1>Create New Disbursement</h1>
          <p>Record a new fund disbursement</p>

          <form className="create-form" onSubmit={handleSubmit}>
            <div className="form-group">
              <label>Linked Subsidy</label>
              <select
                name="subsidy_id"
                value={formData.subsidy_id}
                onChange={handleChange}
              >
                <option value="">Select a subsidy (optional)</option>
                {subsidies.map(s => (
                  <option key={s.id} value={s.id}>{s.title} - {s.recipient}</option>
                ))}
              </select>
            </div>

            <div className="form-row">
              <div className="form-group">
                <label>Amount (INR) *</label>
                <input
                  type="number"
                  name="amount"
                  value={formData.amount}
                  onChange={handleChange}
                  required
                  min="0.01"
                  step="0.01"
                  placeholder="e.g., 100000"
                />
              </div>

              <div className="form-group">
                <label>Approval Status *</label>
                <select
                  name="approval_status"
                  value={formData.approval_status}
                  onChange={handleChange}
                  required
                >
                  {APPROVAL_STATUSES.map(s => (
                    <option key={s} value={s}>{s.charAt(0).toUpperCase() + s.slice(1)}</option>
                  ))}
                </select>
              </div>
            </div>

            <div className="form-group">
              <label>Reference / Transaction ID</label>
              <input
                type="text"
                name="reference"
                value={formData.reference}
                onChange={handleChange}
                placeholder="e.g., TXN-123456"
              />
            </div>

            <div className="form-group">
              <label>Notes</label>
              <textarea
                name="notes"
                value={formData.notes}
                onChange={handleChange}
                rows="3"
                placeholder="Additional notes about this disbursement..."
              />
            </div>

            <div className="form-actions">
              <button type="submit" className="btn-primary" disabled={loading}>
                {loading ? <><Loader size={16} className="spin" /> Creating...</> : <><Plus size={16} /> Create Disbursement</>}
              </button>
              <button type="button" className="btn-secondary" onClick={() => navigate(-1)}>
                Cancel
              </button>
            </div>
          </form>

          <Toast visible={success} message="Disbursement created successfully!" type="success" onClose={() => setSuccess(false)} />
          <Toast visible={!!error} message={error} type="error" onClose={() => setError(null)} />
        </main>
      </div>
    </div>
  );
}