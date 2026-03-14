import React, { createContext, useContext, useState, useCallback, useEffect } from "react";
import apiClient from "../services/apiClient";

const DemoModeContext = createContext(null);

const DEMO_INSIGHTS = {
  fraudCases: [
    {
      id: 1,
      title: "Duplicate Disbursement Detected",
      severity: "high",
      description: "₹2.4Cr disbursed twice to same recipient across two subsidy programs within 48 hours.",
      sector: "Agriculture",
      recipient: "Agri Corp Holdings"
    },
    {
      id: 2,
      title: "Shell Company Pattern",
      severity: "high",
      description: "3 recipients share the same registered address and bank account, receiving ₹5.7Cr total.",
      sector: "Healthcare",
      recipient: "Multiple entities"
    },
    {
      id: 3,
      title: "Unusual Allocation Spike",
      severity: "medium",
      description: "Education sector allocation increased 340% in Q3 without corresponding policy change.",
      sector: "Education",
      recipient: "State Education Board"
    }
  ],
  suspiciousSectors: ["Agriculture", "Healthcare", "Infrastructure"],
  highlights: [
    "3 recipients flagged for overlapping fund flows",
    "Agriculture sector shows 2.4x higher anomaly rate",
    "12 disbursements exceed authorized allocation limits",
    "Blockchain verification pending for 8 high-value transactions"
  ]
};

export function DemoModeProvider({ children }) {
  const [demoMode, setDemoMode] = useState(false);
  const [loading, setLoading] = useState(true);

  // Fetch demo mode status from backend on mount
  useEffect(() => {
    async function checkDemoMode() {
      try {
        const response = await apiClient.get("/demo/status");
        if (response.data) {
          setDemoMode(response.data.demo_mode || false);
        }
      } catch (err) {
        console.log("Could not fetch demo mode status");
      } finally {
        setLoading(false);
      }
    }
    checkDemoMode();
  }, []);

  const toggleDemo = useCallback(async () => {
    try {
      const response = await apiClient.post("/demo/toggle");
      setDemoMode(response.data.demo_mode);
      // Optionally reload page to reflect data changes
      if (response.data.demo_mode) {
        window.location.reload();
      }
    } catch (err) {
      console.error("Failed to toggle demo mode:", err);
    }
  }, []);

  const seedData = useCallback(async () => {
    try {
      const response = await apiClient.post("/demo/seed");
      if (response.data.seeded) {
        window.location.reload();
      }
      return response.data;
    } catch (err) {
      console.error("Failed to seed data:", err);
      throw err;
    }
  }, []);

  const clearData = useCallback(async () => {
    try {
      const response = await apiClient.post("/demo/clear");
      window.location.reload();
      return response.data;
    } catch (err) {
      console.error("Failed to clear data:", err);
      throw err;
    }
  }, []);

  return (
    <DemoModeContext.Provider value={{ 
      demoMode, 
      toggleDemo, 
      seedData, 
      clearData,
      loading,
      demoInsights: DEMO_INSIGHTS 
    }}>
      {children}
    </DemoModeContext.Provider>
  );
}

export function useDemoMode() {
  const context = useContext(DemoModeContext);
  if (!context) {
    return { demoMode: false, toggleDemo: () => {}, seedData: () => {}, clearData: () => {}, loading: false, demoInsights: DEMO_INSIGHTS };
  }
  return context;
}
