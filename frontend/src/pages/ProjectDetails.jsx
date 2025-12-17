import React, { useState } from "react";
import Navbar from "../components/Navbar";
import Sidebar from "../components/Sidebar";
import DataTable from "../components/DataTable";
import AuditTimeline from "../components/AuditTimeline";
import Loader from "../components/Loader";
import ProjectCard from "../components/ProjectCard";
import SubsidyCard from "../components/SubsidyCard";
import BlockchainProofBadge from "../components/BlockchainProofBadge";
import { fetchProjectById } from "../api/projects";
import { fetchSubsidies } from "../api/subsidies";
import useAuth from "../hooks/useAuth";
import useFetch from "../hooks/useFetch";

export default function ProjectDetails({ projectId = null }) {
  const { user, token, isAuthenticated } = useAuth();

  const {
    data: projectData,
    loading: projectLoading,
    error: projectError
  } = useFetch(() => (projectId ? fetchProjectById(projectId, token) : null), {
    immediate: isAuthenticated && projectId
  });

  const {
    data: subsidiesData,
    loading: subsidiesLoading,
    error: subsidiesError
  } = useFetch(
    () =>
      projectId
        ? fetchSubsidies({ projectId, limit: 50, offset: 0, token })
        : null,
    {
      immediate: isAuthenticated && projectId
    }
  );

  if (!isAuthenticated || !projectId) {
    return <div className="project-details error">Invalid access</div>;
  }

  if (projectLoading || subsidiesLoading) {
    return <Loader message="Loading project details..." />;
  }

  if (projectError || subsidiesError) {
    return <div className="project-details error">Failed to load project</div>;
  }

  const project = projectData || {};
  const subsidies = subsidiesData?.data || subsidiesData || [];
  const audits = project.audits || [];

  return (
    <div className="project-details">
      <Navbar user={user} />
      <div className="project-layout">
        <Sidebar user={user} />
        <main className="project-content">
          <h1>Project Details</h1>

          <section>
            <h2>Project Summary</h2>
            <ProjectCard project={project} onClick={() => {}} />
          </section>

          {(project.proofHash || project.proofId) && (
            <section>
              <h2>Blockchain Proof</h2>
              <BlockchainProofBadge
                proofHash={project.proofHash}
                proofId={project.proofId}
                verified={project.proofVerified}
              />
            </section>
          )}

          <section>
            <h2>Related Subsidies</h2>
            {subsidies.length > 0 ? (
              <div className="subsidies-list">
                {subsidies.map((subsidy, index) => (
                  <SubsidyCard
                    key={subsidy.id || index}
                    subsidy={subsidy}
                    onClick={() => {}}
                  />
                ))}
              </div>
            ) : (
              <p>No subsidies found for this project</p>
            )}
          </section>

          <section>
            <h2>Audit Timeline</h2>
            <AuditTimeline audits={audits} />
          </section>
        </main>
      </div>
    </div>
  );
}