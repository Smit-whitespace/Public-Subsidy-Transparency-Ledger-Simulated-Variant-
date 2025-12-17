import React from "react";

export default function Toast({
  message = "",
  type = "info",
  visible = false,
  onClose = () => {}
}) {
  if (!visible || !message) {
    return null;
  }

  const toastClass = `toast toast-${type}`;

  return (
    <div className={toastClass} role="alert">
      <span className="toast-message">{message}</span>
      <button type="button" className="toast-close" onClick={onClose}>
        ×
      </button>
    </div>
  );
}