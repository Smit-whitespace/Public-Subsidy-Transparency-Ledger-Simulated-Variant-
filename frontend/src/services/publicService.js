import apiClient from "./apiClient";

export async function getPublicSubsidies({ sector, status, q, limit = 50, offset = 0 } = {}) {
  const params = new URLSearchParams();
  if (sector) params.append("sector", sector);
  if (status) params.append("status", status);
  if (q) params.append("q", q);
  params.append("limit", limit);
  params.append("offset", offset);

  const res = await apiClient.get(`/public/subsidies?${params.toString()}`);
  return res.data;
}

export async function getPublicSubsidyById(subsidyId) {
  const res = await apiClient.get(`/public/subsidies/${subsidyId}`);
  return res.data;
}

export async function getPublicSummary() {
  const res = await apiClient.get("/public/analytics/summary");
  return res.data;
}

export async function getPublicSectorDistribution() {
  const res = await apiClient.get("/public/analytics/sector-distribution");
  return res.data;
}

export async function getPublicYearTrends() {
  const res = await apiClient.get("/public/analytics/year-trends");
  return res.data;
}

export async function getPublicRiskDistribution() {
  const res = await apiClient.get("/public/analytics/risk-distribution");
  return res.data;
}

export async function getPublicFundFlow() {
  const res = await apiClient.get("/public/analytics/fund-flow");
  return res.data;
}

export async function getPublicFundFlowSectors() {
  const res = await apiClient.get("/public/analytics/fund-flow/sectors");
  return res.data;
}

export async function getPublicTransparencyScores({ limit = 20, sector } = {}) {
  const params = new URLSearchParams();
  params.append("limit", limit);
  if (sector) params.append("sector", sector);

  const res = await apiClient.get(`/public/transparency-scores?${params.toString()}`);
  return res.data;
}

export async function getPublicSectors() {
  const res = await apiClient.get("/public/sectors");
  return res.data;
}
