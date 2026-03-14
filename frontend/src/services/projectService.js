import apiClient from "./apiClient";

export async function fetchProjects({
  limit = 50,
  offset = 0,
  status = null,
  token
}) {

  const params = new URLSearchParams();

  if (limit) params.append("limit", limit);
  if (offset) params.append("offset", offset);
  if (status) params.append("status", status);

  const response = await apiClient.get(`/projects?${params.toString()}`, {
    headers: token ? { Authorization: `Bearer ${token}` } : {}
  });

  return response.data;
}

export async function fetchProjectById(projectId, token) {

  const response = await apiClient.get(`/projects/${projectId}`, {
    headers: token ? { Authorization: `Bearer ${token}` } : {}
  });

  return response.data;
}

export async function updateProject(projectId, projectData, token) {
  const response = await apiClient.patch(`/projects/${projectId}`, projectData, {
    headers: token ? { Authorization: `Bearer ${token}` } : {}
  });
  return response.data;
}

export async function deleteProject(projectId, token) {
  const response = await apiClient.delete(`/projects/${projectId}`, {
    headers: token ? { Authorization: `Bearer ${token}` } : {}
  });
  return response.data;
}

export async function createProject(projectData, token) {
  const response = await apiClient.post("/projects/", projectData, {
    headers: token ? { Authorization: `Bearer ${token}` } : {}
  });
  return response.data;
}