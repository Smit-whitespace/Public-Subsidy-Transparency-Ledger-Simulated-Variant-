import React from "react";
import { NavLink } from "react-router-dom";

export default function Sidebar({
  collapsed = false,
  onToggle = () => {},
  user = null
}) {
  const sidebarClass = `app-sidebar${collapsed ? " collapsed" : ""}`;

  const navLinkClass = ({ isActive }) =>
    isActive ? "sidebar-link active" : "sidebar-link";

  return (
    <aside className={sidebarClass}>
      <div className="sidebar-header">
        <div className="sidebar-title">PSTL</div>
        <button type="button" onClick={onToggle}>
          ☰
        </button>
      </div>

      <nav className="sidebar-nav">
        <NavLink to="/dashboard" className={navLinkClass}>
          Dashboard
        </NavLink>

        <NavLink to="/projects" className={navLinkClass}>
          Projects
        </NavLink>

        <NavLink to="/subsidies" className={navLinkClass}>
          Subsidies
        </NavLink>

        <NavLink to="/disbursements" className={navLinkClass}>
          Disbursements
        </NavLink>

        <NavLink to="/audits" className={navLinkClass}>
          Audits
        </NavLink>
      </nav>

      <div className="sidebar-footer">
        {user ? (
          <span className="sidebar-user">{user.username}</span>
        ) : (
          <span className="sidebar-user">Guest</span>
        )}
      </div>
    </aside>
  );
}
