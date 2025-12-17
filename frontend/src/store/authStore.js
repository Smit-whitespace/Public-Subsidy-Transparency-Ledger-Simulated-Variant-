let user = null;
let token = null;
let loading = false;
let error = null;

const listeners = new Set();

function notify() {
  const state = { user, token, loading, error };
  listeners.forEach((listener) => listener(state));
}

function subscribe(listener) {
  if (typeof listener !== "function") {
    throw new Error("Listener must be a function");
  }
  listeners.add(listener);
  return function unsubscribe() {
    listeners.delete(listener);
  };
}

function getState() {
  return { user, token, loading, error };
}

function getUser() {
  return user;
}

function getToken() {
  return token;
}

function isAuthenticated() {
  return Boolean(token);
}

function setUser(newUser) {
  user = newUser;
  notify();
}

function setToken(newToken) {
  token = newToken;
  notify();
}

function setLoading(value) {
  loading = Boolean(value);
  notify();
}

function setError(value) {
  error = value;
  notify();
}

function resetAuth() {
  user = null;
  token = null;
  loading = false;
  error = null;
  notify();
}

export {
  subscribe,
  getState,
  getUser,
  getToken,
  isAuthenticated,
  setUser,
  setToken,
  setLoading,
  setError,
  resetAuth
};