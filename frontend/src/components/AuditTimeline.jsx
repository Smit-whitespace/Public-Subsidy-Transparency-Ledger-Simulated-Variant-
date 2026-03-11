import React from "react";

export default function AuditTimeline({ audits = [], loading = false, error = null }) {
  if (loading) {
    return <div className="audit-timeline loading">Loading audit trail...</div>;
  }

  if (error) {
    return <div className="audit-timeline error">Failed to load audit trail</div>;
  }

  if (!audits || audits.length === 0) {
    return <div className="audit-timeline empty">No audit events found</div>;
  }

  function formatTimestamp(timestamp) {
    // Backend sends created_at, not timestamp
    const ts = timestamp || timestamp?.created_at;
    try {
      return new Date(ts).toLocaleString();
    } catch (_) {
      return ts || "N/A";
    }
  }

  function formatDetails(details) {
    if (!details) return null;
    if (typeof details === "string") return details;
    try {
      return JSON.stringify(details, null, 2);
    } catch (_) {
      return String(details);
    }
  }

  return (
    <div className="audit-timeline">
      {audits.map((audit, index) => {
        const action = audit?.action || "unknown";
        const entity = audit?.entity || "unknown";
        const entityId = audit?.entity_id || "N/A";
        // Backend field is created_at, not timestamp
        const timestamp = audit?.created_at || audit?.timestamp;
        const actor = audit?.performed_by || "system";
        const details = audit?.details;
        const itemKey = audit?.id || index;

        return (
          <div className="audit-item" key={itemKey}>
            <div className="audit-marker"></div>
            <div className="audit-content">
              <div className="audit-action">{action}</div>
              <div className="audit-meta">
                {entity} • {entityId}
              </div>
              <div className="audit-time">{formatTimestamp(timestamp)}</div>
              <div className="audit-actor">by {actor}</div>
              {details && (
                <pre className="audit-details">{formatDetails(details)}</pre>
              )}
            </div>
          </div>
        );
      })}
    </div>
  );
}