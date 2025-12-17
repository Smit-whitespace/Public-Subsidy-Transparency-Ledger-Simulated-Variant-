import React, { useState, useEffect } from "react";
import Navbar from "../components/Navbar";
import Sidebar from "../components/Sidebar";
import SearchBar from "../components/SearchBar";
import FilterPanel from "../components/FilterPanel";
import SubsidyCard from "../components/SubsidyCard";
import Loader from "../components/Loader";
import { fetchSubsidies } from "../api/subsidies";
import useAuth from "../hooks/useAuth";
import useFetch from "../hooks/useFetch";
import useDebounce from "../hooks/useDebounce";

export default function SubsidyList() {
  const { user, token, isAuthenticated } = useAuth();
  const [query, setQuery] = useState("");
  const [filters, setFilters] = useState({});

  const debouncedQuery = useDebounce(query, 400);

  const { data, loading, error, execute } = useFetch(
    () =>
      fetchSubsidies({
        limit: 50,
        offset: 0,
        status: filters.status || null,
        token
      }),
    { immediate: true }
  );

  useEffect(() => {
    if (isAuthenticated && token) {
      execute();
    }
  }, [debouncedQuery, filters, token, isAuthenticated, execute]);

  if (!isAuthenticated) {
    return <div className="subsidy-list unauthorized">Access denied</div>;
  }

  if (loading) {
    return <Loader message="Loading subsidies..." />;
  }

  if (error) {
    return <div className="subsidy-list error">Failed to load subsidies</div>;
  }

  const subsidies = data?.data || data || [];

  const filterSchema = [
    {
      key: "status",
      label: "Status",
      type: "text"
    }
  ];

  function handleFilterChange(updatedFilters) {
    setFilters(updatedFilters);
  }

  function handleFilterReset() {
    setFilters({});
  }

  function handleSubsidyClick(subsidy) {
    // Placeholder for navigation
  }

  return (
    <div className="subsidy-list">
      <Navbar user={user} />
      <div className="subsidy-layout">
        <Sidebar user={user} />
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
              onChange={handleFilterChange}
              onReset={handleFilterReset}
            />
          </section>

          <section>
            {subsidies.length > 0 ? (
              <div className="subsidies-grid">
                {subsidies.map((subsidy, index) => (
                  <SubsidyCard
                    key={subsidy.id || index}
                    subsidy={subsidy}
                    onClick={handleSubsidyClick}
                  />
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