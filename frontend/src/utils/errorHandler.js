function normalizeError(error) {
  if (!error) {
    return { message: "Unknown error" };
  }

  if (typeof error === "string") {
    return { message: error };
  }

  if (error instanceof Error) {
    return { message: error.message };
  }

  if (typeof error === "object") {
    if (error.detail) {
      return { message: error.detail };
    }
    if (error.message) {
      return { message: error.message };
    }
    return { message: JSON.stringify(error) };
  }

  return { message: "Unknown error" };
}

function getErrorMessage(error) {
  const normalized = normalizeError(error);
  return normalized.message;
}

function isAuthError(error) {
  if (!error) {
    return false;
  }

  const message = getErrorMessage(error);
  const lowerMessage = message.toLowerCase();

  if (lowerMessage.includes("unauthorized") || lowerMessage.includes("forbidden")) {
    return true;
  }

  if (typeof error === "object" && (error.status === 401 || error.status === 403)) {
    return true;
  }

  return false;
}

export {
  normalizeError,
  getErrorMessage,
  isAuthError
};