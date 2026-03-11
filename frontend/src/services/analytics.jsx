const API_BASE_URL = import.meta?.env?.VITE_API_BASE_URL || "http://localhost:8000";
const ANALYTICS_BASE = "/analytics";

async function request(url, options = {}) {
  const headers = {
    "Content-Type": "application/json",
    "Accept": "application/json"
  };

  if (options.token) {
    headers["Authorization"] = `Bearer ${options.token}`;
  }

  const response = await fetch(url, {
    method: options.method || "GET",
    headers
  });

  if (!response.ok) {
    let errorMessage = "Analytics request failed";
    try {
      const errorData = await response.json();
      errorMessage = errorData.detail || errorData.message || errorMessage;
    } catch (_) {
      errorMessage = `Request failed with status ${response.status}`;
    }
    throw new Error(errorMessage);
  }

  return await response.json();
}

/* ---------- SUMMARY ---------- */

export async function fetchAnalyticsSummary(token) {
  const url = `${API_BASE_URL}${ANALYTICS_BASE}/summary`;
  return request(url, { token });
}

/* ---------- SECTOR DISTRIBUTION ---------- */

export async function fetchSectorDistribution(token) {
  const url = `${API_BASE_URL}${ANALYTICS_BASE}/sector-distribution`;
  return request(url, { token });
}

/* ---------- RISK DISTRIBUTION ---------- */

export async function fetchRiskDistribution(token) {
  const url = `${API_BASE_URL}${ANALYTICS_BASE}/risk-distribution`;
  return request(url, { token });
}

/* ---------- YEAR TRENDS ---------- */

export async function fetchYearTrends(token) {
  const url = `${API_BASE_URL}${ANALYTICS_BASE}/year-trends`;
  return request(url, { token });
}

/* ---------- HIGH RISK SUBSIDIES ---------- */

export async function fetchHighRiskSubsidies(token) {
  const url = `${API_BASE_URL}${ANALYTICS_BASE}/high-risk-subsidies`;
  return request(url, { token });
}