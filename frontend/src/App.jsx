import { BrowserRouter, Routes, Route } from "react-router-dom";

import Home from "./pages/Home";
import Login from "./pages/Login";
import AdminDashboard from "./pages/AdminDashboard";
import ProjectList from "./pages/ProjectList";
import ProjectDetails from "./pages/ProjectDetails";
import SubsidyList from "./pages/SubsidyList";
import SubsidyDetails from "./pages/SubsidyDetails";
import DisbursementTracker from "./pages/DisbursementTracker";
import AuditTrail from "./pages/AuditTrail";

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Home />} />
        <Route path="/login" element={<Login />} />
        <Route path="/dashboard" element={<AdminDashboard />} />
        <Route path="/projects" element={<ProjectList />} />
        <Route path="/projects/:id" element={<ProjectDetails />} />
        <Route path="/subsidies" element={<SubsidyList />} />
        <Route path="/subsidies/:id" element={<SubsidyDetails />} />
        <Route path="/disbursements" element={<DisbursementTracker />} />
        <Route path="/audits" element={<AuditTrail />} />
      </Routes>
    </BrowserRouter>
  );
}

export default App;
