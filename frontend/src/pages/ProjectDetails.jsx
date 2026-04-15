import React, { useEffect, useCallback } from "react";
import { useParams, useNavigate } from "react-router-dom";

import Navbar from "../components/Navbar";
import Sidebar from "../components/Sidebar";
import AuditTimeline from "../components/AuditTimeline";
import Loader from "../components/Loader";
import ProjectCard from "../components/ProjectCard";
import SubsidyCard from "../components/SubsidyCard";
import BlockchainProofBadge from "../components/BlockchainProofBadge";

import { fetchProjectById } from "../services/projectService";
import { fetchSubsidies } from "../services/subsidyService";

import { useAuth } from "../context/AuthContext";
import useFetch from "../hooks/useFetch";

export default function ProjectDetails() {

  const { id } = useParams();
  const navigate = useNavigate();

  const { token, isAuthenticated } = useAuth();

  const projectId = id ? parseInt(id, 10) : null;

  const fetchProject = useCallback(() => {

    if (!token || !projectId) {
      return Promise.resolve(null);
    }

    return fetchProjectById(projectId, token);

  }, [projectId, token]);

  const fetchProjectSubsidies = useCallback(() => {

    if (!token || !projectId) {
      return Promise.resolve([]);
    }

    return fetchSubsidies({
      projectId,
      limit: 50,
      offset: 0,
      token
    });

  }, [projectId, token]);

  const {
    data: projectData,
    loading: projectLoading,
    error: projectError,
    execute: loadProject
  } = useFetch(fetchProject, { immediate: false });

  const {
    data: subsidiesData,
    loading: subsidiesLoading,
    error: subsidiesError,
    execute: loadSubsidies
  } = useFetch(fetchProjectSubsidies, { immediate: false });

  useEffect(() => {

    if (isAuthenticated && token && projectId) {
      loadProject();
      loadSubsidies();
    }

  }, [isAuthenticated, token, projectId, loadProject, loadSubsidies]);

  if (!isAuthenticated) {
    return (
      <div className="project-details unauthorized">
        Access denied
      </div>
    );
  }

  if (!projectId || isNaN(projectId)) {
    return (
      <div className="project-details error">
        Invalid project ID
      </div>
    );
  }

  if (projectLoading || subsidiesLoading) {
    return <Loader message="Loading project details..." />;
  }

  if (projectError || subsidiesError) {
    return (
      <div className="project-details error">
        Failed to load project
      </div>
    );
  }

  const project = projectData || {};
  const subsidies = subsidiesData?.data || subsidiesData || [];
  const audits = project?.audits || [];

  function handleSubsidyClick(subsidy) {
    if (!subsidy?.id) return;
    navigate(`/subsidies/${subsidy.id}`);
  }

  return (
    <div className="project-details">

      <Navbar />

      <div className="project-layout">

        <Sidebar />

        <main className="project-content">

          <h1>Project Details</h1>

          <section>

            <h2>Project Summary</h2>

            <ProjectCard
              project={project}
              onClick={() => {}}
            />

          </section>

          {(project?.proofHash || project?.proofId) && (

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