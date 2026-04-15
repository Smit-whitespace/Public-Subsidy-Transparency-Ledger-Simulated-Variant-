const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL || "http://localhost:8000";

export async function getRiskEvents(token) {
  const res = await fetch(`${API_BASE_URL}/risk-events/`, {
    headers: {
      Authorization: `Bearer ${token}`
    }
  });

  if (!res.ok) {
    throw new Error("Failed to fetch risk events");
  }

  return res.json();
}