import React, { createContext, useContext, useState, useCallback } from "react";

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

  const toggleDemo = useCallback(() => {
    setDemoMode(prev => !prev);
  }, []);

  return (
    <DemoModeContext.Provider value={{ demoMode, toggleDemo, demoInsights: DEMO_INSIGHTS }}>
      {children}
    </DemoModeContext.Provider>
  );
}

export function useDemoMode() {
  const context = useContext(DemoModeContext);
  if (!context) {
    return { demoMode: false, toggleDemo: () => {}, demoInsights: DEMO_INSIGHTS };
  }
  return context;
}
