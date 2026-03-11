import React from "react";
import { NavLink, useNavigate, useLocation } from "react-router-dom";
import { useAuth } from "../context/AuthContext";

export default function Navbar() {

  const { user, isAuthenticated, logout } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();

  // hide navbar on login page
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
        )}

      </div>

      <div className="topbar-right">

        {isAuthenticated && (
          <>
            <span className="user-name">
              {user?.username}
            </span>

            <button
              className="logout-btn"
              onClick={handleLogout}
            >
              Logout
            </button>
          </>
        )}

      </div>

    </header>
  );
}