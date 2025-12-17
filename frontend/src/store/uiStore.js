let sidebarCollapsed = false;
let globalLoading = false;
let activePage = null;
let toast = null;

const listeners = new Set();

function notify() {
  const state = {
    sidebarCollapsed,
    globalLoading,
    activePage,
    toast
  };
  listeners.forEach(listener => listener(state));
}

function subscribe(listener) {
  listeners.add(listener);
  return () => {
    listeners.delete(listener);
  };
}

function getState() {
  return {
    sidebarCollapsed,
    globalLoading,
    activePage,
    toast
  };
}

function isSidebarCollapsed() {
  return sidebarCollapsed;
}

function isGlobalLoading() {
  return globalLoading;
}

function getActivePage() {
  return activePage;
}

function getToast() {
  return toast;
}

function toggleSidebar() {
  sidebarCollapsed = !sidebarCollapsed;
  notify();
}

function setSidebarCollapsed(value) {
  sidebarCollapsed = value;
  notify();
}

function setGlobalLoading(value) {
  globalLoading = value;
  notify();
}

function setActivePage(page) {
  activePage = page;
  notify();
}

function showToast(toastData) {
  toast = toastData;
  notify();
}

function clearToast() {
  toast = null;
  notify();
}

function resetUI() {
  sidebarCollapsed = false;
  globalLoading = false;
  activePage = null;
  toast = null;
  notify();
}

export {
  subscribe,
  getState,
  isSidebarCollapsed,
  isGlobalLoading,
  getActivePage,
  getToast,
  toggleSidebar,
  setSidebarCollapsed,
  setGlobalLoading,
  setActivePage,
  showToast,
  clearToast,
  resetUI
};