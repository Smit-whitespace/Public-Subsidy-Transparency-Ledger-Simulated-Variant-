import React, { useState, useEffect } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { Save, ArrowLeft, Loader } from "lucide-react";
import Navbar from "../components/Navbar";
import Sidebar from "../components/Sidebar";
import Toast from "../components/Toast";
import { useAuth } from "../context/AuthContext";
import { fetchDisbursementById, updateDisbursement } from "../services/disbursementService";

export default function EditDisbursement() {
  const { id } = useParams();
  const navigate = useNavigate();
  const { token } = useAuth();

  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState(null);
  const [success, setSuccess] = useState(false);
  const [formData, setFormData] = useState({
    amount: "", currency: "INR", reference: "", notes: "", date: ""
  });

  useEffect(() => {
    if (!id || !token) return;
    fetchDisbursementById(parseInt(id), token)
      .then(data => {
        setFormData({
          amount: data.amount || "",
          currency: data.currency || "INR",
          reference: data.reference || "",
          notes: data.notes || "",
          date: data.date ? data.date.substring(0, 10) : "",
        });
        setLoading(false);
      })
      .catch(() => { setError("Failed to load disbursement"); setLoading(false); });
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
      const payload = { ...formData, amount: parseFloat(formData.amount) };
      if (!payload.date) delete payload.date;
      await updateDisbursement(parseInt(id), payload, token);
      setSuccess(true);
      setTimeout(() => navigate("/disbursements"), 1500);
    } catch (err) {
      setError(err.response?.data?.detail || "Failed to update disbursement");
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
          <h1>Edit Disbursement</h1>
          <p>Update disbursement record</p>

          <form className="create-form" onSubmit={handleSubmit}>
            <div className="form-row">
              <div className="form-group">
                <label>Amount (INR) *</label>
                <input type="number" name="amount" value={formData.amount} onChange={handleChange} required min="0.01" step="0.01" />
              </div>
              <div className="form-group">
                <label>Currency</label>
                <input type="text" name="currency" value={formData.currency} onChange={handleChange} maxLength={3} />
              </div>
            </div>
            <div className="form-group">
              <label>Date</label>
              <input type="date" name="date" value={formData.date} onChange={handleChange} />
            </div>
            <div className="form-group">
              <label>Reference</label>
              <input type="text" name="reference" value={formData.reference} onChange={handleChange} placeholder="External transaction ID" />
            </div>
            <div className="form-group">
              <label>Notes</label>
              <textarea name="notes" value={formData.notes} onChange={handleChange} rows="3" />
            </div>
            <div className="form-actions">
              <button type="submit" className="btn-primary" disabled={saving}>
                {saving ? <><Loader size={16} className="spin" /> Saving...</> : <><Save size={16} /> Save Changes</>}
              </button>
              <button type="button" className="btn-secondary" onClick={() => navigate(-1)}>Cancel</button>
            </div>
          </form>

          <Toast visible={success} message="Disbursement updated successfully!" type="success" onClose={() => setSuccess(false)} />
          <Toast visible={!!error} message={error} type="error" onClose={() => setError(null)} />
        </main>
      </div>
    </div>
  );
}
