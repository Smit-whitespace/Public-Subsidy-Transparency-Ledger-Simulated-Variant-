import React, { useState, useEffect, useCallback } from "react";
import { useNavigate } from "react-router-dom";

import Navbar from "../components/Navbar";
import Sidebar from "../components/Sidebar";
import SearchBar from "../components/SearchBar";
import FilterPanel from "../components/FilterPanel";
import SubsidyCard from "../components/SubsidyCard";
import Loader from "../components/Loader";

import { fetchSubsidies, createSubsidy, deleteSubsidy } from "../services/subsidyService";
import { useAuth } from "../context/AuthContext";
import useFetch from "../hooks/useFetch";

const SECTORS = [
  "Agriculture",
  "Education",
  "Healthcare",
  "Infrastructure",
  "MSME",
  "Renewable Energy",
  "Social Welfare"
];

export default function SubsidyList() {

  const navigate = useNavigate();
  const { token, isAuthenticated, user } = useAuth();
  const isAdmin = user?.role === "admin";

  const [query, setQuery] = useState("");
  const [filters, setFilters] = useState({});
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [newSubsidy, setNewSubsidy] = useState({
    title: "",
    recipient: "",
    sector: "",
    total_allocation: "",
    description: "",
    status: "active"
  });
  const [creating, setCreating] = useState(false);
  const [deletingIds, setDeletingIds] = useState(new Set());

  async function handleCreateSubsidy(e) {
    e.preventDefault();
    if (creating || !token) return;
    setCreating(true);
    try {
      await createSubsidy(newSubsidy, token);
      setShowCreateModal(false);
      setNewSubsidy({
        title: "",
        recipient: "",
        sector: "",
        total_allocation: "",
        description: "",
        status: "active"
      });
      execute();
    } catch (err) {
      console.error("Failed to create subsidy:", err);
    } finally {
      setCreating(false);
    }
  }

  async function handleDeleteSubsidy(subsidyId, e) {
    e.stopPropagation();
    if (!token || deletingIds.has(subsidyId)) return;
    setDeletingIds((prev) => new Set(prev).add(subsidyId));
    try {
      await deleteSubsidy(subsidyId, token);
      execute();
    } catch (err) {
      console.error("Failed to delete subsidy:", err);
    } finally {
      setDeletingIds((prev) => {
        const next = new Set(prev);
        next.delete(subsidyId);
        return next;
      });
    }
  }

  const fetchSubsidyData = useCallback(() => {

    if (!token) {
      return Promise.resolve([]);
    }

    return fetchSubsidies({
      limit: 50,
      offset: 0,
      status: filters.status || null,
      token
    });

  }, [filters, token]);

  const {
    data,
    loading,
    error,
    execute
  } = useFetch(fetchSubsidyData, { immediate: true });

useEffect(() => {
  if (isAuthenticated && token) {
    execute();
  }  }, [filters, token, isAuthenticated, execute]);

  // Early returns for loading, error, unauthorized states
  if (!isAuthenticated) {
    return (
      <div className="subsidy-list unauthorized">
        Access denied
      </div>
    );
  }

  if (loading) {
    return <Loader message="Loading subsidies..." />;
  }

  if (error) {
    return (
      <div className="subsidy-list error">
        Failed to load subsidies
      </div>
    );
  }

  // Render create modal when active
  if (showCreateModal) {
    return (
      <div className="subsidy-list">
        <Navbar />
        <div className="subsidy-layout">
          <Sidebar />
          <main className="subsidy-content">
            <h1>Create New Subsidy</h1>
            <form onSubmit={handleCreateSubsidy} className="create-form">
              <div className="form-group">
                <label>Title</label>
                <input
                  type="text"
                  value={newSubsidy.title}
                  onChange={e => setNewSubsidy({...newSubsidy, title: e.target.value})}
                  required
                />
              </div>
              <div className="form-group">
                <label>Recipient</label>
                <input
                  type="text"
                  value={newSubsidy.recipient}
                  onChange={e => setNewSubsidy({...newSubsidy, recipient: e.target.value})}
                  required
                />
              </div>
              <div className="form-group">
                <label>Sector</label>
                <select
                  value={newSubsidy.sector}
                  onChange={e => setNewSubsidy({...newSubsidy, sector: e.target.value})}
                  required
                >
                  <option value="">Select sector</option>
                  {SECTORS.map(s => <option key={s} value={s}>{s}</option>)}
                </select>
              </div>
              <div className="form-group">
                <label>Total Allocation (INR)</label>
                <input
                  type="number"
                  value={newSubsidy.total_allocation}
                  onChange={e => setNewSubsidy({...newSubsidy, total_allocation: e.target.value})}
                  required
                  min="1"
                />
              </div>
              <div className="form-group">
                <label>Description</label>
                <textarea
                  value={newSubsidy.description}
                  onChange={e => setNewSubsidy({...newSubsidy, description: e.target.value})}
                />
              </div>
              <div className="form-group">
                <label>Status</label>
                <select
                  value={newSubsidy.status}
                  onChange={e => setNewSubsidy({...newSubsidy, status: e.target.value})}
                >
                  <option value="active">Active</option>
                  <option value="pending">Pending</option>
                  <option value="expired">Expired</option>
                </select>
              </div>
              <div className="form-actions">
                <button type="submit" className="btn-primary" disabled={creating}>
                  {creating ? "Creating..." : "Create Subsidy"}
                </button>
                <button type="button" className="btn-secondary" onClick={() => setShowCreateModal(false)}>
                  Cancel
                </button>
              </div>
            </form>
          </main>
        </div>
      </div>
    );
  }

  // Main list view
  const subsidies = data?.data || data || [];

  const filterSchema = [
    { key: "status", label: "Status", type: "text" }
  ];

  function handleFilterReset() {
    setFilters({});
  }

  return (
    <div className="subsidy-list">
      <Navbar />
      <div className="subsidy-layout">
        <Sidebar />
        <main className="subsidy-content">
          <h1>Subsidies</h1>
          <p>Browse and track public subsidies</p>

          <section>
            <SearchBar
              value={query}
              onChange={setQuery}
              onSubmit={() => {}}
              placeholder="Search subsidies..."
            />
          </section>

          <section>
            <FilterPanel
              filters={filters}
              schema={filterSchema}
              onChange={setFilters}
              onReset={handleFilterReset}
            />
          </section>

          <section>
            {isAdmin && (
              <button className="btn-primary" onClick={() => setShowCreateModal(true)} style={{ marginBottom: "1rem" }}>
                + Create New Subsidy
              </button>
            )}

            {subsidies.length > 0 ? (
              <div className="subsidies-grid">
                {subsidies.map((subsidy, index) => (
                  <div key={subsidy.id || index} className="subsidy-card-wrapper">
                    <SubsidyCard subsidy={subsidy} onClick={() => navigate(`/subsidies/${subsidy.id}`)} />
                    {isAdmin && (
                      <div className="card-actions">
                        <button
                          className="btn-secondary"
                          onClick={(e) => { e.stopPropagation(); navigate(`/admin/edit-subsidy/${subsidy.id}`); }}
                          style={{ marginRight: "0.5rem" }}
                        >
                          Edit
                        </button>
                        <button
                          className="btn-delete"
                          onClick={(e) => handleDeleteSubsidy(subsidy.id, e)}
                          disabled={deletingIds.has(subsidy.id)}
                        >
                          {deletingIds.has(subsidy.id) ? "Deleting..." : "Delete"}
                        </button>
                      </div>
                    )}
                  </div>
                ))}
              </div>
            ) : (
              <div className="subsidy-list empty">No subsidies found</div>
            )}
          </section>
        </main>
      </div>
    </div>
  );
}