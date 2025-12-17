const API_BASE_URL = import.meta?.env?.VITE_API_BASE_URL || "http://localhost:8000";
const AUDIT_BASE_PATH = "/audits";

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
    headers,
    ...options
  };

  if (options.body && typeof options.body === "object") {
    fetchOptions.body = JSON.stringify(options.body);
  }

  const response = await fetch(url, fetchOptions);

  if (!response.ok) {
    let errorMessage = "Request failed";
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

export async function fetchAudits({ limit = 20, offset = 0, entity = null, action = null, token } = {}) {
  const params = { limit, offset };
  if (entity) params.entity = entity;
  if (action) params.action = action;

  const queryString = buildQueryParams(params);
  const url = `${API_BASE_URL}${AUDIT_BASE_PATH}?${queryString}`;

  return await request(url, { token });
}

export async function fetchAuditById(auditId, token) {
  if (!auditId) {
    throw new Error("auditId is required");
  }

  const url = `${API_BASE_URL}${AUDIT_BASE_PATH}/${auditId}`;
  return await request(url, { token });
}

export async function fetchAuditsForEntity(entity, entityId, { limit = 20, offset = 0, token } = {}) {
  if (!entity) {
    throw new Error("entity is required");
  }
  if (!entityId) {
    throw new Error("entityId is required");
  }

  const params = {
    entity,
    entity_id: entityId,
    limit,
    offset
  };

  const queryString = buildQueryParams(params);
  const url = `${API_BASE_URL}${AUDIT_BASE_PATH}?${queryString}`;

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
  const url = `${API_BASE_URL}/search?${queryString}`;

  return await request(url, { token });
}