import React from "react";
import { NavLink, useNavigate } from "react-router-dom";

export default function Navbar({ user = null, onLogout = () => {} }) {
  const navigate = useNavigate();

  function handleLogout() {
    onLogout();
    navigate("/login");
  }

  const navLinkClass = ({ isActive }) =>
    isActive ? "nav-link active" : "nav-link";

  return (
    <header className="app-navbar">
      <div className="navbar-left">
        <div className="navbar-brand">
          <NavLink to="/" className="brand-link">
            Public Subsidy Transparency Ledger
          </NavLink>
        </div>

        <nav className="navbar-nav">
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
      </div>

      <div className="navbar-right">
        {user ? (
          <div className="navbar-user">
            <span className="navbar-username">
              {user.username}
            </span>
            <button type="button" onClick={handleLogout}>
              Logout
            </button>
          </div>
        ) : (
          <div className="navbar-user">
            <NavLink to="/login" className={navLinkClass}>
              Login
            </NavLink>
          </div>
        )}
      </div>
    </header>
  );
}
