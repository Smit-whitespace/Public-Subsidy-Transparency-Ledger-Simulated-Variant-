import React, { useState, useEffect } from "react";
import Navbar from "../components/Navbar";
import Sidebar from "../components/Sidebar";
import SearchBar from "../components/SearchBar";
import FilterPanel from "../components/FilterPanel";
import ProjectCard from "../components/ProjectCard";
import Loader from "../components/Loader";
import { fetchProjects } from "../api/projects";
import useAuth from "../hooks/useAuth";
import useFetch from "../hooks/useFetch";
import useDebounce from "../hooks/useDebounce";

export default function ProjectList() {
  const { user, token, isAuthenticated } = useAuth();
  const [query, setQuery] = useState("");
  const [filters, setFilters] = useState({});

  const debouncedQuery = useDebounce(query, 400);

  const { data, loading, error, execute } = useFetch(
    () =>
      fetchProjects({
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
    return <div className="project-list unauthorized">Access denied</div>;
  }

  if (loading) {
    return <Loader message="Loading projects..." />;
  }

  if (error) {
    return <div className="project-list error">Failed to load projects</div>;
  }

  const projects = data?.data || data || [];

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

  function handleProjectClick(project) {
    // Placeholder for navigation
  }

  return (
    <div className="project-list">
      <Navbar user={user} />
      <div className="project-layout">
        <Sidebar user={user} />
        <main className="project-content">
          <h1>Projects</h1>
          <p>Browse and manage public projects</p>

          <section>
            <SearchBar
              value={query}
              onChange={setQuery}
              onSubmit={() => {}}
              placeholder="Search projects..."
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
            {projects.length > 0 ? (
              <div className="projects-grid">
                {projects.map((project, index) => (
                  <ProjectCard
                    key={project.id || index}
                    project={project}
                    onClick={handleProjectClick}
                  />
                ))}
              </div>
            ) : (
              <div className="project-list empty">No projects found</div>
            )}
          </section>
        </main>
      </div>
    </div>
  );
}