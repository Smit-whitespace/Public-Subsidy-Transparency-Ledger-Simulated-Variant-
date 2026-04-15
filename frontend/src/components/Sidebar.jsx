import React from "react";
import { NavLink, useNavigate } from "react-router-dom";
import {
  LayoutDashboard,
  FolderKanban,
  Wallet,
  ArrowRightLeft,
  FileSearch,
  Search,
  Shield,
  FileCheck,
  Newspaper,
  Landmark,
  Users
} from "lucide-react";

import { useAuth } from "../context/AuthContext";

/* ----------------------------------
   Navigation Items
---------------------------------- */

const NAV_ITEMS = [
  { to: "/dashboard", label: "Dashboard", icon: LayoutDashboard, roles: null },
  { to: "/projects", label: "Projects", icon: FolderKanban, roles: null },
  { to: "/subsidies", label: "Subsidies", icon: Wallet, roles: null },
  { to: "/disbursements", label: "Disbursements", icon: ArrowRightLeft, roles: null },
  { to: "/audits", label: "Audits", icon: FileSearch, roles: null },
  {
    to: "/investigation",
    label: "Investigation",
    icon: Search,
    roles: ["admin", "auditor", "media"]
  }
];

/* ----------------------------------
   Role Icons
---------------------------------- */

const ROLE_ICONS = {
  admin: Shield,
  auditor: FileCheck,
  media: Newspaper,
  government_official: Landmark,
  public: Users
};

/* ----------------------------------
   Sidebar Component
---------------------------------- */

export default function Sidebar() {

  const { user, isAuthenticated } = useAuth();
  const navigate = useNavigate();

  const userRole = user?.role || "public";

  const RoleIcon = ROLE_ICONS[userRole] || Users;

  const navClass = ({ isActive }) =>
    isActive ? "sidebar-link active" : "sidebar-link";

  const visibleItems = NAV_ITEMS.filter(item => {
    if (!item.roles) return true;
    if (!isAuthenticated) return false;
    return item.roles.includes(userRole);
  });

  return (
    <aside className="sidebar">

      <div
        className="sidebar-logo"
        style={{ cursor: "pointer" }}
        onClick={() => navigate("/dashboard")}
      >
        PSTL
      </div>

      <nav className="sidebar-nav">
        {visibleItems.map(({ to, label, icon: Icon }) => (
          <NavLink key={to} to={to} className={navClass}>
            <Icon size={16} />
            <span>{label}</span>
          </NavLink>
        ))}
      </nav>

      {isAuthenticated && (
        <div className="sidebar-footer">
          <div className="sidebar-role-badge">
            <RoleIcon size={14} style={{ marginRight: 6 }} />
            {userRole.replace("_", " ").toUpperCase()}
          </div>
        </div>
      )}

    </aside>
  );
}