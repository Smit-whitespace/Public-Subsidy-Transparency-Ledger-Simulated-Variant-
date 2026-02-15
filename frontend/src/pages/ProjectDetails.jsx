import React, { useEffect } from "react";
import { useParams, useNavigate } from "react-router-dom";
import Navbar from "../components/Navbar";
import Sidebar from "../components/Sidebar";
import AuditTimeline from "../components/AuditTimeline";
import Loader from "../components/Loader";
import ProjectCard from "../components/ProjectCard";
import SubsidyCard from "../components/SubsidyCard";
import BlockchainProofBadge from "../components/BlockchainProofBadge";
import { fetchProjectById } from "../api/projects";
import { fetchSubsidies } from "../api/subsidies";
import useAuth from "../hooks/useAuth";
import useFetch from "../hooks/useFetch";

export default function ProjectDetails() {
  const { id } = useParams();
  const navigate = useNavigate();
  const { user, token, isAuthenticated } = useAuth();

  const projectId = id ? parseInt(id, 10) : null;

  const {
    data: projectData,
    loading: projectLoading,
    error: projectError,
    execute: loadProject
  } = useFetch(
    () => fetchProjectById(projectId, token),
    { immediate: false }
  );

  const {
    data: subsidiesData,
    loading: subsidiesLoading,
    error: subsidiesError,
    execute: loadSubsidies
  } = useFetch(
    () =>
      fetchSubsidies({
        projectId,
        limit: 50,
        offset: 0,
        token
      }),
    { immediate: false }
  );

  useEffect(() => {
    if (isAuthenticated && token && projectId) {
      loadProject();
      loadSubsidies();
    }
  }, [isAuthenticated, token, projectId, loadProject, loadSubsidies]);

  if (!isAuthenticated) {
    return <div className="project-details unauthorized">Access denied</div>;
  }

  if (!projectId || isNaN(projectId)) {
    return <div className="project-details error">Invalid project ID</div>;
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

  function handleSubsidyClick(subsidy) {
    if (!subsidy?.id) return;
    navigate(`/subsidies/${subsidy.id}`);
  }

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
                    onClick={handleSubsidyClick}
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
