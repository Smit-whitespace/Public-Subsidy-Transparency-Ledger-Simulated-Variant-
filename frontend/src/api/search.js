const API_BASE_URL = import.meta?.env?.VITE_API_BASE_URL || "http://localhost:8000";
const SEARCH_BASE_PATH = "/search";

async function request(url, options = {}) {
  const headers = {
    "Content-Type": "application/json",
    "Accept": "application/json"
  };

  if (options.token) {
    headers["Authorization"] = `Bearer ${options.token}`;
  }

  const fetchOptions = {
    method: options.method || "GET",
    headers
  };

  const response = await fetch(url, fetchOptions);

  if (!response.ok) {
    let errorMessage = "Search request failed";
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

function buildQueryParams(params) {
  const searchParams = new URLSearchParams();
  for (const [key, value] of Object.entries(params)) {
    if (value !== null && value !== undefined) {
      searchParams.append(key, value);
    }
  }
  return searchParams.toString();
}

export async function searchAll(query, { limit = 20, offset = 0, token } = {}) {
  if (!query) {
    throw new Error("query is required");
  }

  const params = {
    q: query,
    limit,
    offset
  };

  const queryString = buildQueryParams(params);
  const url = `${API_BASE_URL}${SEARCH_BASE_PATH}?${queryString}`;

  return await request(url, { token });
}

export async function searchProjects(query, { limit = 20, offset = 0, token } = {}) {
  if (!query) {
    throw new Error("query is required");
  }

  const params = {
    entity: "project",
    q: query,
    limit,
    offset
  };

  const queryString = buildQueryParams(params);
  const url = `${API_BASE_URL}${SEARCH_BASE_PATH}?${queryString}`;

  return await request(url, { token });
}

export async function searchSubsidies(query, { limit = 20, offset = 0, token } = {}) {
  if (!query) {
    throw new Error("query is required");
  }

  const params = {
    entity: "subsidy",
    q: query,
    limit,
    offset
  };

  const queryString = buildQueryParams(params);
  const url = `${API_BASE_URL}${SEARCH_BASE_PATH}?${queryString}`;

  return await request(url, { token });
}

export async function searchDisbursements(query, { limit = 20, offset = 0, token } = {}) {
  if (!query) {
    throw new Error("query is required");
  }

  const params = {
    entity: "disbursement",
    q: query,
    limit,
    offset
  };

  const queryString = buildQueryParams(params);
  const url = `${API_BASE_URL}${SEARCH_BASE_PATH}?${queryString}`;

  return await request(url, { token });
}

export async function searchAudits(query, { limit = 20, offset = 0, token } = {}) {
  if (!query) {
    throw new Error("query is required");
  }

  const params = {
    entity: "audit",
    q: query,
    limit,
    offset
  };

  const queryString = buildQueryParams(params);
  const url = `${API_BASE_URL}${SEARCH_BASE_PATH}?${queryString}`;

  return await request(url, { token });
}