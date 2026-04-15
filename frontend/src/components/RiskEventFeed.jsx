import React from "react";
import RiskBadge from "./RiskBadge";

export default function RiskEventFeed({ events = [] }) {

  if (!events.length) {
    return <p>No risk events detected</p>;
  }

  return (
    <div className="risk-feed">

      {events.map((event) => (
        <div key={event.id} className="risk-event">

          <div className="risk-event-header">

            <span className="risk-type">
              {event.event_type}
            </span>

            <RiskBadge score={event.severity_score || 0} />

          </div>

          <div className="risk-description">
            {event.description}
          </div>

        </div>
      ))}

    </div>
  );
}