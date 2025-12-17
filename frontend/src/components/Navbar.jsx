import React from "react";

export default function Navbar({ user = null, onLogout = () => {} }) {
  return (
    <header className="app-navbar">
      <div className="navbar-left">
        <div className="navbar-brand">Public Subsidy Transparency Ledger</div>
        <nav className="navbar-nav">
          <a href="#">Dashboard</a>
          <a href="#">Projects</a>
          <a href="#">Subsidies</a>
          <a href="#">Disbursements</a>
          <a href="#">Audits</a>
        </nav>
      </div>
      <div className="navbar-right">
        {user ? (
          <div className="navbar-user">
            <span className="navbar-username">{user.username}</span>
            <button type="button" onClick={onLogout}>
              Logout
            </button>
          </div>
        ) : (
          <div className="navbar-user">
            <a href="#">Login</a>
          </div>
        )}
      </div>
    </header>
  );
}