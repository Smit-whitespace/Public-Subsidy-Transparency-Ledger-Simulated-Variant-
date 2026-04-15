import React from "react";
import { NavLink, useNavigate, useLocation } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import {
  LayoutDashboard,
  FolderKanban,
  Wallet,
  ArrowRightLeft,
  FileSearch,
  Search,
  Globe,
  LogOut,
  LogIn
} from "lucide-react";

const AUTH_NAV = [
  { to: "/dashboard", label: "Dashboard", icon: LayoutDashboard },
  { to: "/projects", label: "Projects", icon: FolderKanban },
  { to: "/subsidies", label: "Subsidies", icon: Wallet },
  { to: "/disbursements", label: "Disbursements", icon: ArrowRightLeft },
  { to: "/audits", label: "Audits", icon: FileSearch },
  { to: "/investigation", label: "Investigation", icon: Search },
];

export default function Navbar() {
  const { user, isAuthenticated, logout } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();

  if (location.pathname === "/login") {
    return null;
  }

  const navClass = ({ isActive }) =>
    isActive ? "nav-link active" : "nav-link";

  function handleLogout() {
    logout();
    navigate("/login");
  }

  return (
    <header className="topbar">
      <div className="topbar-left">
        <div className="logo">PSTL</div>

        {isAuthenticated && (
          <nav className="top-nav">
            {AUTH_NAV.map(({ to, label, icon: Icon }) => (
              <NavLink key={to} to={to} className={navClass}>
                <Icon size={14} style={{ marginRight: 4, verticalAlign: "middle" }} />
                {label}
              </NavLink>
            ))}
          </nav>
        )}
      </div>

      <div className="topbar-right">
        {isAuthenticated ? (
          <>
            <span className="user-name">{user?.username}</span>
            <button className="logout-btn" onClick={handleLogout}>
              <LogOut size={14} style={{ marginRight: 4, verticalAlign: "middle" }} />
              Logout
            </button>
          </>
        ) : (
          <>
            <NavLink to="/transparency" className={navClass}>
              <Globe size={14} style={{ marginRight: 4, verticalAlign: "middle" }} />
              Transparency Portal
            </NavLink>
            <NavLink to="/login" className="cta-primary" style={{ fontSize: "13px", padding: "7px 18px" }}>
              <LogIn size={14} style={{ marginRight: 4, verticalAlign: "middle" }} />
              Login
            </NavLink>
          </>
        )}
      </div>
    </header>
  );
}
