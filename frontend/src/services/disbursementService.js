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