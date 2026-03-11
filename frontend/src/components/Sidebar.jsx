import React from "react";
import { NavLink } from "react-router-dom";

export default function Sidebar() {

  const navClass = ({ isActive }) =>
    isActive ? "sidebar-link active" : "sidebar-link";

  return (
    <aside className="sidebar">

      <div className="sidebar-logo">
        PSTL
      </div>

      <nav className="sidebar-nav">

        <NavLink to="/dashboard" className={navClass}>
          Dashboard
        </NavLink>

        <NavLink to="/projects" className={navClass}>
          Projects
        </NavLink>

        <NavLink to="/subsidies" className={navClass}>
          Subsidies
        </NavLink>

        <NavLink to="/disbursements" className={navClass}>
          Disbursements
        </NavLink>

        <NavLink to="/audits" className={navClass}>
          Audits
        </NavLink>

      </nav>

    </aside>
  );
}