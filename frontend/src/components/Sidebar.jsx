import React from "react";
import { NavLink } from "react-router-dom";
import {
  LayoutDashboard,
  FolderKanban,
  Wallet,
  ArrowRightLeft,
  FileSearch,
  Search
} from "lucide-react";

const NAV_ITEMS = [
  { to: "/dashboard", label: "Dashboard", icon: LayoutDashboard },
  { to: "/projects", label: "Projects", icon: FolderKanban },
  { to: "/subsidies", label: "Subsidies", icon: Wallet },
  { to: "/disbursements", label: "Disbursements", icon: ArrowRightLeft },
  { to: "/audits", label: "Audits", icon: FileSearch },
  { to: "/investigation", label: "Investigation", icon: Search },
];

export default function Sidebar() {
  const navClass = ({ isActive }) =>
    isActive ? "sidebar-link active" : "sidebar-link";

  return (
    <aside className="sidebar">
      <div className="sidebar-logo">PSTL</div>
      <nav className="sidebar-nav">
        {NAV_ITEMS.map(({ to, label, icon: Icon }) => (
          <NavLink key={to} to={to} className={navClass}>
            <Icon size={16} />
            <span>{label}</span>
          </NavLink>
        ))}
      </nav>
    </aside>
  );
}
