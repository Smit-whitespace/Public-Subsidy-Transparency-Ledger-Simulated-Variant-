import apiClient from "./apiClient";

export async function getDisbursements(params = {}) {

  const res = await apiClient.get("/disbursements", { params });

  return res.data;

}

export async function fetchDisbursements({
  subsidyId = null,
  limit = 50,
  offset = 0,
  token
} = {}) {

  const params = new URLSearchParams();

  if (subsidyId) params.append("subsidy_id", subsidyId);
  if (limit) params.append("limit", limit);
  if (offset) params.append("offset", offset);

  const response = await apiClient.get(`/disbursements?${params.toString()}`, {
    headers: token ? { Authorization: `Bearer ${token}` } : {}
  });

  return response.data;
}

export async function createDisbursement(disbursementData, token) {
  const response = await apiClient.post("/disbursements/", disbursementData, {
    headers: token ? { Authorization: `Bearer ${token}` } : {}
  });
  return response.data;
}

export async function updateDisbursement(disbursementId, data, token) {
  const response = await apiClient.patch(`/disbursements/${disbursementId}`, data, {
    headers: token ? { Authorization: `Bearer ${token}` } : {}
  });
  return response.data;
}

export async function deleteDisbursement(disbursementId, token) {
  const response = await apiClient.delete(`/disbursements/${disbursementId}`, {
    headers: token ? { Authorization: `Bearer ${token}` } : {}
  });
  return response.data;
}

export async function fetchDisbursementById(disbursementId, token) {
  const response = await apiClient.get(`/disbursements/${disbursementId}`, {
    headers: token ? { Authorization: `Bearer ${token}` } : {}
  });
  return response.data;
}