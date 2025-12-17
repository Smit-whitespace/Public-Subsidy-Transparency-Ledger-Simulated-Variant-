import React from "react";

export default function Sidebar({
  collapsed = false,
  onToggle = () => {},
  user = null
}) {
  const sidebarClass = `app-sidebar${collapsed ? " collapsed" : ""}`;

  return (
    <aside className={sidebarClass}>
      <div className="sidebar-header">
        <div className="sidebar-title">PSTL</div>
        <button type="button" onClick={onToggle}>
          ☰
        </button>
      </div>
      <nav className="sidebar-nav">
        <a href="#">Dashboard</a>
        <a href="#">Projects</a>
        <a href="#">Subsidies</a>
        <a href="#">Disbursements</a>
        <a href="#">Audits</a>
        <a href="#">Search</a>
      </nav>
      <div className="sidebar-footer">
        {user ? <span>{user.username}</span> : <span>Guest</span>}
      </div>
    </aside>
  );
}