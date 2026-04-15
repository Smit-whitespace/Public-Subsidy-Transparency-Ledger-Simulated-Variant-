import apiClient from "./apiClient";

export async function fetchAudits({
  limit = 50,
  offset = 0,
  entity = null,
  action = null,
  token
} = {}) {

  const params = new URLSearchParams();

  if (limit) params.append("limit", limit);
  if (offset) params.append("offset", offset);
  if (entity) params.append("entity", entity);
  if (action) params.append("action", action);

  const response = await apiClient.get(`/audits?${params.toString()}`, {
    headers: token ? { Authorization: `Bearer ${token}` } : {}
  });

  return response.data;
}

export async function getAudits(token, limit = 50, offset = 0) {

  const params = new URLSearchParams();
  if (limit) params.append("limit", limit);
  if (offset) params.append("offset", offset);

  const response = await apiClient.get(`/audits?${params.toString()}`, {
    headers: token ? { Authorization: `Bearer ${token}` } : {}
  });

  return response.data;
}