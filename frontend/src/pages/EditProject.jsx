import React, { useState, useEffect } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { Save, ArrowLeft, Loader } from "lucide-react";
import Navbar from "../components/Navbar";
import Sidebar from "../components/Sidebar";
import Toast from "../components/Toast";
import { useAuth } from "../context/AuthContext";
import { fetchProjectById, updateProject } from "../services/projectService";

const STATUSES = ["planned", "active", "completed", "suspended", "cancelled"];

export default function EditProject() {
  const { id } = useParams();
  const navigate = useNavigate();
  const { token } = useAuth();

  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState(null);
  const [success, setSuccess] = useState(false);
  const [formData, setFormData] = useState({
    name: "", owner: "", description: "", status: "planned",
    start_date: "", end_date: ""
  });

  useEffect(() => {
    if (!id || !token) return;
    fetchProjectById(parseInt(id), token)
      .then(data => {
        setFormData({
          name: data.name || "",
          owner: data.owner || "",
          description: data.description || "",
          status: data.status || "planned",
          start_date: data.start_date ? data.start_date.substring(0, 10) : "",
          end_date: data.end_date ? data.end_date.substring(0, 10) : "",
        });
        setLoading(false);
      })
      .catch(() => { setError("Failed to load project"); setLoading(false); });
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
      const payload = { ...formData };
      if (!payload.start_date) delete payload.start_date;
      if (!payload.end_date) delete payload.end_date;
      await updateProject(parseInt(id), payload, token);
      setSuccess(true);
      setTimeout(() => navigate(`/projects/${id}`), 1500);
    } catch (err) {
      setError(err.response?.data?.detail || "Failed to update project");
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
          <h1>Edit Project</h1>
          <p>Update project details</p>

          <form className="create-form" onSubmit={handleSubmit}>
            <div className="form-group">
              <label>Project Name *</label>
              <input type="text" name="name" value={formData.name} onChange={handleChange} required />
            </div>
            <div className="form-group">
              <label>Owner</label>
              <input type="text" name="owner" value={formData.owner} onChange={handleChange} />
            </div>
            <div className="form-group">
              <label>Status *</label>
              <select name="status" value={formData.status} onChange={handleChange} required>
                {STATUSES.map(s => <option key={s} value={s}>{s.charAt(0).toUpperCase() + s.slice(1)}</option>)}
              </select>
            </div>
            <div className="form-row">
              <div className="form-group">
                <label>Start Date</label>
                <input type="date" name="start_date" value={formData.start_date} onChange={handleChange} />
              </div>
              <div className="form-group">
                <label>End Date</label>
                <input type="date" name="end_date" value={formData.end_date} onChange={handleChange} />
              </div>
            </div>
            <div className="form-group">
              <label>Description</label>
              <textarea name="description" value={formData.description} onChange={handleChange} rows="3" />
            </div>
            <div className="form-actions">
              <button type="submit" className="btn-primary" disabled={saving}>
                {saving ? <><Loader size={16} className="spin" /> Saving...</> : <><Save size={16} /> Save Changes</>}
              </button>
              <button type="button" className="btn-secondary" onClick={() => navigate(-1)}>Cancel</button>
            </div>
          </form>

          <Toast visible={success} message="Project updated successfully!" type="success" onClose={() => setSuccess(false)} />
          <Toast visible={!!error} message={error} type="error" onClose={() => setError(null)} />
        </main>
      </div>
    </div>
  );
}
