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

export async function getHighRiskSubsidies() {

  const res = await apiClient.get("/analytics/high-risk-subsidies");
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