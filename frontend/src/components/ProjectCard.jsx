import React from "react";

export default function ProjectCard({ project = null, onClick = () => {} }) {
  if (!project) {
    return <div className="project-card empty">No project data</div>;
  }

  function formatDate(dateValue) {
    if (!dateValue) return "N/A";
    try {
      return new Date(dateValue).toLocaleDateString();
    } catch (_) {
      return String(dateValue);
    }
  }

  function handleClick() {
    onClick(project);
  }

  function handleKeyDown(e) {
    if (e.key === "Enter") {
      onClick(project);
    }
  }

  const name = project.name || "Untitled Project";
  const description = project.description || "No description available";
  const status = project.status || "Unknown";
  const budget = project.budget ? String(project.budget) : "N/A";
  const startDate = formatDate(project.start_date);
  const endDate = formatDate(project.end_date);

  return (
    <div
      className="project-card"
      role="button"
      tabIndex={0}
      onClick={handleClick}
      onKeyDown={handleKeyDown}
    >
      <div className="project-card-header">
        <div className="project-title">{name}</div>
        <div className="project-status">{status}</div>
      </div>
      <div className="project-card-body">
        <div className="project-description">{description}</div>
      </div>
      <div className="project-card-meta">
        <div className="project-budget">Budget: {budget}</div>
        <div className="project-dates">
          {startDate} – {endDate}
        </div>
      </div>
    </div>
  );
}