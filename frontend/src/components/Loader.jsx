import React from "react";

export default function Loader({ message = "Loading...", inline = false }) {
  if (inline) {
    return (
      <span className="loader inline">
        <span className="loader-spinner"></span>
        <span className="loader-message">{message}</span>
      </span>
    );
  }

  return (
    <div className="loader">
      <div className="loader-spinner"></div>
      <div className="loader-message">{message}</div>
    </div>
  );
}