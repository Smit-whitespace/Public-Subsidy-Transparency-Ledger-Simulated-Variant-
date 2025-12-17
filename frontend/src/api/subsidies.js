const API_BASE_URL = import.meta?.env?.VITE_API_BASE_URL || "http://localhost:8000";
const SUBSIDY_BASE_PATH = "/subsidies";

async function request(url, options = {}) {
  const headers = {
    "Content-Type": "application/json",
    "Accept": "application/json"
  };

  if (options.token) {
    headers["Authorization"] = `Bearer ${options.token}`;
  }

  let method = options.method || "GET";
  const fetchOptions = {
    method,
    headers
  };

  if (options.body && typeof options.body === "object") {
    fetchOptions.body = JSON.stringify(options.body);
    if (!options.method) {
      fetchOptions.method = "POST";
    }
  }

  const response = await fetch(url, fetchOptions);

  if (!response.ok) {
    let errorMessage = "Subsidy request failed";
    try {
      const errorData = await response.json();
      errorMessage = errorData.detail || errorData.message || errorMessage;
    } catch (_) {
      errorMessage = `Request failed with status ${response.status}`;
    }
    throw new Error(errorMessage);
  }

  if (response.status === 204) {
    return { success: true };
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

export async function fetchSubsidies({ projectId = null, status = null, limit = 20, offset = 0, token } = {}) {
  const params = { limit, offset };
  if (projectId) {
    params.project_id = projectId;
  }
  if (status) {
    params.status = status;
  }

  const queryString = buildQueryParams(params);
  const url = `${API_BASE_URL}${SUBSIDY_BASE_PATH}?${queryString}`;

  return await request(url, { token });
}

export async function fetchSubsidyById(subsidyId, token) {
  if (!subsidyId) {
    throw new Error("subsidyId is required");
  }

  const url = `${API_BASE_URL}${SUBSIDY_BASE_PATH}/${subsidyId}`;
  return await request(url, { token });
}

export async function createSubsidy(payload, token) {
  if (!payload) {
    throw new Error("payload is required");
  }

  const url = `${API_BASE_URL}${SUBSIDY_BASE_PATH}`;
  return await request(url, { method: "POST", body: payload, token });
}

export async function updateSubsidy(subsidyId, payload, token) {
  if (!subsidyId) {
    throw new Error("subsidyId is required");
  }
  if (!payload) {
    throw new Error("payload is required");
  }

  const url = `${API_BASE_URL}${SUBSIDY_BASE_PATH}/${subsidyId}`;
  return await request(url, { method: "PUT", body: payload, token });
}

export async function deleteSubsidy(subsidyId, token) {
  if (!subsidyId) {
    throw new Error("subsidyId is required");
  }

  const url = `${API_BASE_URL}${SUBSIDY_BASE_PATH}/${subsidyId}`;
  return await request(url, { method: "DELETE", token });
}