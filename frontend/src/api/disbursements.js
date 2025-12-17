const API_BASE_URL = import.meta?.env?.VITE_API_BASE_URL || "http://localhost:8000";
const DISBURSEMENT_BASE_PATH = "/disbursements";

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
    let errorMessage = "Disbursement request failed";
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

export async function fetchDisbursements({ subsidyId = null, limit = 20, offset = 0, token } = {}) {
  const params = { limit, offset };
  if (subsidyId) {
    params.subsidy_id = subsidyId;
  }

  const queryString = buildQueryParams(params);
  const url = `${API_BASE_URL}${DISBURSEMENT_BASE_PATH}?${queryString}`;

  return await request(url, { token });
}

export async function fetchDisbursementById(disbursementId, token) {
  if (!disbursementId) {
    throw new Error("disbursementId is required");
  }

  const url = `${API_BASE_URL}${DISBURSEMENT_BASE_PATH}/${disbursementId}`;
  return await request(url, { token });
}

export async function createDisbursement(payload, token) {
  if (!payload) {
    throw new Error("payload is required");
  }

  const url = `${API_BASE_URL}${DISBURSEMENT_BASE_PATH}`;
  return await request(url, { method: "POST", body: payload, token });
}

export async function updateDisbursement(disbursementId, payload, token) {
  if (!disbursementId) {
    throw new Error("disbursementId is required");
  }
  if (!payload) {
    throw new Error("payload is required");
  }

  const url = `${API_BASE_URL}${DISBURSEMENT_BASE_PATH}/${disbursementId}`;
  return await request(url, { method: "PUT", body: payload, token });
}

export async function deleteDisbursement(disbursementId, token) {
  if (!disbursementId) {
    throw new Error("disbursementId is required");
  }

  const url = `${API_BASE_URL}${DISBURSEMENT_BASE_PATH}/${disbursementId}`;
  return await request(url, { method: "DELETE", token });
}