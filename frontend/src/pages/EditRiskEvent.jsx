import React, { useState, useEffect } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { Save, ArrowLeft, Loader } from "lucide-react";
import Navbar from "../components/Navbar";
import Sidebar from "../components/Sidebar";
import Toast from "../components/Toast";
import { useAuth } from "../context/AuthContext";
import apiClient from "../services/apiClient";

const SEVERITIES = ["low", "medium", "high"];
const EVENT_TYPES = ["anomaly", "fraud", "duplicate", "delay", "overpayment", "shell_entity", "rapid_disbursement", "sector_risk"];

export default function EditRiskEvent() {
  const { id } = useParams();
  const navigate = useNavigate();
  const { token } = useAuth();

  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState(null);
  const [success, setSuccess] = useState(false);
  const [formData, setFormData] = useState({
    event_type: "anomaly", severity: "medium", description: ""
  });

  useEffect(() => {
    if (!id || !token) return;
    apiClient.get(`/risk-events/${id}`, { headers: { Authorization: `Bearer ${token}` } })
      .then(res => {
        const data = res.data;
        setFormData({
          event_type: data.event_type || "anomaly",
          severity: data.severity || "medium",
          description: data.description || ""
        });
        setLoading(false);
      })
      .catch(() => { setError("Failed to load risk event"); setLoading(false); });
  }, [id, token]);

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({ ...prev, [name]: value }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setSaving(true);
    setError(null);
    try {
      await apiClient.patch(`/risk-events/${id}`, formData, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setSuccess(true);
      setTimeout(() => navigate(-1), 1500);
    } catch (err) {
      setError(err.response?.data?.detail || "Failed to update risk event");
    } finally {
      setSaving(false);
    }
  };

  if (loading) return (
    <div className="subsidy-details"><Navbar /><div className="subsidy-layout"><Sidebar /><main className="subsidy-content"><p>Loading...</p></main></div></div>
  );

  return (
    <div className="subsidy-details">
      <Navbar />
      <div className="subsidy-layout">
        <Sidebar />
        <main className="subsidy-content">
          <button className="back-link" onClick={() => navigate(-1)}><ArrowLeft size={16} /> Back</button>
          <h1>Edit Risk Event</h1>
          <p>Update risk event details</p>

          <form className="create-form" onSubmit={handleSubmit}>
            <div className="form-row">
              <div className="form-group">
                <label>Event Type *</label>
                <select name="event_type" value={formData.event_type} onChange={handleChange} required>
                  {EVENT_TYPES.map(t => (
                    <option key={t} value={t}>{t.replace(/_/g, " ").replace(/\b\w/g, c => c.toUpperCase())}</option>
                  ))}
                </select>
              </div>
              <div className="form-group">
                <label>Severity *</label>
                <select name="severity" value={formData.severity} onChange={handleChange} required>
                  {SEVERITIES.map(s => <option key={s} value={s}>{s.charAt(0).toUpperCase() + s.slice(1)}</option>)}
                </select>
              </div>
            </div>
            <div className="form-group">
              <label>Description *</label>
              <textarea name="description" value={formData.description} onChange={handleChange} rows="4" required />
            </div>
            <div className="form-actions">
              <button type="submit" className="btn-primary" disabled={saving}>
                {saving ? <><Loader size={16} className="spin" /> Saving...</> : <><Save size={16} /> Save Changes</>}
              </button>
              <button type="button" className="btn-secondary" onClick={() => navigate(-1)}>Cancel</button>
            </div>
          </form>

          <Toast visible={success} message="Risk event updated successfully!" type="success" onClose={() => setSuccess(false)} />
          <Toast visible={!!error} message={error} type="error" onClose={() => setError(null)} />
        </main>
      </div>
    </div>
  );
}
