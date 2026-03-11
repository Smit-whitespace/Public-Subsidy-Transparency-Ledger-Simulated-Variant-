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