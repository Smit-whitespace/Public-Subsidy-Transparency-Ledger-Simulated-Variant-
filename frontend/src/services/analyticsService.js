import apiClient from "./apiClient";

export async function getDashboardSummary() {
  const res = await apiClient.get("/analytics/summary");
  return res.data;
}

export async function getSectorDistribution() {
  const res = await apiClient.get("/analytics/sector-distribution");
  return res.data;
}

export async function getRiskDistribution() {
  const res = await apiClient.get("/analytics/risk-distribution");
  return res.data;
}

export async function getYearTrends() {
  const res = await apiClient.get("/analytics/year-trends");
  return res.data;
}

export async function getHighRiskSubsidies(limit = 10, sector = null) {
  const params = new URLSearchParams();
  if (limit) params.append("limit", limit);
  if (sector) params.append("sector", sector);
  const res = await apiClient.get(`/analytics/high-risk-subsidies?${params}`);
  return res.data;
}

export async function getAnomalySummary() {
  const res = await apiClient.get("/analytics/anomalies");
  return res.data;
}

export async function getSubsidyAnomalies(subsidyId) {
  const res = await apiClient.get(`/analytics/subsidy/${subsidyId}/anomalies`);
  return res.data;
}

export async function getFundFlowSummary() {
  const res = await apiClient.get("/analytics/fund-flow/summary");
  return res.data;
}

export async function getFundFlowTimeline(subsidyId = null) {
  const params = subsidyId ? `?subsidy_id=${subsidyId}` : "";
  const res = await apiClient.get(`/analytics/fund-flow/timeline${params}`);
  return res.data;
}

export async function getFundFlowBySector() {
  const res = await apiClient.get("/analytics/fund-flow/sectors");
  return res.data;
}

export async function getFraudNetwork() {
  const res = await apiClient.get("/analytics/fraud-network");
  return res.data;
}

export async function getSectorRiskOverview() {
  const res = await apiClient.get("/analytics/sector-risk-overview");
  return res.data;
}