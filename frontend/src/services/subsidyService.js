import apiClient from "./apiClient";

export async function fetchSubsidies({
  projectId = null,
  status = null,
  limit = 50,
  offset = 0,
  token
}) {

  const params = new URLSearchParams();

  if (projectId) params.append("project_id", projectId);
  if (status) params.append("status", status);
  if (limit) params.append("limit", limit);
  if (offset) params.append("offset", offset);

  const response = await apiClient.get(`/subsidies?${params.toString()}`, {
    headers: token ? { Authorization: `Bearer ${token}` } : {}
  });

  return response.data;
}

export async function fetchSubsidyById(subsidyId, token) {

  const response = await apiClient.get(`/subsidies/${subsidyId}`, {
    headers: token ? { Authorization: `Bearer ${token}` } : {}
  });

  return response.data;
}

export async function createSubsidy(subsidyData, token) {

  const response = await apiClient.post("/subsidies", subsidyData, {
    headers: token ? { Authorization: `Bearer ${token}` } : {}
  });

  return response.data;
}

export async function deleteSubsidy(subsidyId, token) {

  const response = await apiClient.delete(`/subsidies/${subsidyId}`, {
    headers: token ? { Authorization: `Bearer ${token}` } : {}
  });

  return response.data;
}

export async function updateSubsidy(subsidyId, subsidyData, token) {

  const response = await apiClient.patch(`/subsidies/${subsidyId}`, subsidyData, {
    headers: token ? { Authorization: `Bearer ${token}` } : {}
  });

  return response.data;
}