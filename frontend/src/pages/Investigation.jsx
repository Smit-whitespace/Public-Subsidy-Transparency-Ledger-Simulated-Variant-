import { useState, useEffect, useRef, useCallback } from "react";
import ForceGraph2D from "react-force-graph-2d";
import { Search, X, ZoomIn, ZoomOut, Maximize2, Clock, AlertTriangle } from "lucide-react";

import Loader from "../components/Loader";
import Navbar from "../components/Navbar";
import Sidebar from "../components/Sidebar";
import KpiCard from "../components/Analytics/KpiCard";

import useAuth from "../hooks/useAuth";

import {
  getFraudNetwork,
  getFundFlowTimeline,
  getAnomalySummary
} from "../services/analyticsService";


/* =========================================================
   FRAUD GRAPH COMPONENT
========================================================= */

function FraudGraph({ graphData, onNodeClick }) {

  const containerRef = useRef(null);
  const graphRef = useRef(null);

  const [dimensions, setDimensions] = useState({
    width: 800,
    height: 450
  });

  const [zoom, setZoom] = useState(1);

  useEffect(() => {

    function updateSize() {

      if (containerRef.current) {

        setDimensions({
          width: containerRef.current.offsetWidth,
          height: 450
        });

      }

    }

    updateSize();

    window.addEventListener("resize", updateSize);

    return () => window.removeEventListener("resize", updateSize);

  }, []);


  const handleZoomIn = () => {

    if (!graphRef.current) return;

    const newZoom = Math.min(zoom * 1.5, 4);

    graphRef.current.zoom(graphRef.current.zoom() * 1.5, 400);

    setZoom(newZoom);

  };


  const handleZoomOut = () => {

    if (!graphRef.current) return;

    graphRef.current.zoom(graphRef.current.zoom() / 1.5, 400);

    setZoom(Math.max(zoom / 1.5, 0.5));

  };


  const handleReset = () => {

    if (!graphRef.current) return;

    graphRef.current.zoomToFit(400);

    setZoom(1);

  };


  return (

    <div
      ref={containerRef}
      style={{
        height: 450,
        background: "#0f172a",
        borderRadius: 12,
        overflow: "hidden",
        position: "relative"
      }}
    >

      {/* GRAPH CONTROLS */}

      <div
        style={{
          position: "absolute",
          top: 12,
          right: 12,
          zIndex: 10,
          display: "flex",
          gap: 6
        }}
      >

        <button onClick={handleZoomIn}>
          <ZoomIn size={16} />
        </button>

        <button onClick={handleZoomOut}>
          <ZoomOut size={16} />
        </button>

        <button onClick={handleReset}>
          <Maximize2 size={16} />
        </button>

      </div>


      {/* LEGEND */}

      <div
        style={{
          position: "absolute",
          bottom: 12,
          left: 12,
          display: "flex",
          gap: 16,
          background: "rgba(30,41,59,0.85)",
          padding: "8px 14px",
          borderRadius: 8,
          fontSize: 12
        }}
      >

        <Legend color="#ef4444" label="High Risk" />
        <Legend color="#f59e0b" label="Medium Risk" />
        <Legend color="#22c55e" label="Low Risk" />

      </div>


      {graphData.nodes.length > 0 ? (

        <ForceGraph2D
          ref={graphRef}
          graphData={graphData}
          nodeLabel="name"
          nodeColor={(node) =>
            node.risk > 70
              ? "#ef4444"
              : node.risk > 40
              ? "#f59e0b"
              : "#22c55e"
          }
          nodeRelSize={6}
          linkColor={() => "rgba(255,255,255,0.15)"}
          linkWidth={1.5}
          backgroundColor="#0f172a"
          width={dimensions.width}
          height={dimensions.height}
          onNodeClick={onNodeClick}
        />

      ) : (

        <div style={{ color: "white", paddingTop: 180 }}>
          No investigation data available
        </div>

      )}

    </div>

  );

}


/* =========================================================
   LEGEND COMPONENT
========================================================= */

function Legend({ color, label }) {

  return (
    <div style={{ display: "flex", alignItems: "center", gap: 6 }}>
      <span
        style={{
          width: 10,
          height: 10,
          borderRadius: "50%",
          background: color
        }}
      />
      <span style={{ color: "#cbd5e1" }}>{label}</span>
    </div>
  );

}


/* =========================================================
   INVESTIGATION PAGE
========================================================= */

export default function Investigation() {

  const { user, isAuthenticated } = useAuth();

  const [loading, setLoading] = useState(true);
  const [fraudNetwork, setFraudNetwork] = useState(null);
  const [timeline, setTimeline] = useState([]);
  const [anomalies, setAnomalies] = useState(null);
  const [selectedNode, setSelectedNode] = useState(null);
  const [searchTerm, setSearchTerm] = useState("");


  const handleNodeClick = useCallback((node) => {

    setSelectedNode(node);

  }, []);


  const closeNodeDetail = useCallback(() => {

    setSelectedNode(null);

  }, []);


  useEffect(() => {

    if (!isAuthenticated) return;

    async function loadData() {

      try {

        const [networkRes, timelineRes, anomalyRes] =
          await Promise.all([
            getFraudNetwork(),
            getFundFlowTimeline(),
            getAnomalySummary()
          ]);

        setFraudNetwork(networkRes);
        setTimeline(timelineRes || []);
        setAnomalies(anomalyRes);

      } catch (err) {

        console.error("Failed to load investigation data:", err);

      } finally {

        setLoading(false);

      }

    }

    loadData();

  }, [isAuthenticated]);


  if (!isAuthenticated || !user) {

    return (
      <div className="admin-dashboard unauthorized">
        Access denied
      </div>
    );

  }


  if (loading) {

    return <Loader message="Loading investigation data..." />;

  }


  const graphData = fraudNetwork?.graph || { nodes: [], links: [] };


  return (

    <div className="admin-dashboard">

      <Navbar />

      <div className="admin-layout">

        <Sidebar />

        <main className="admin-content">

          <header className="dashboard-header">

            <h1>Fraud Investigation Center</h1>

            <p>
              Visual analysis of suspicious relationships and anomalies
            </p>

          </header>


          {/* KPI CARDS */}

          <section className="dashboard-kpis">

            <KpiCard
              title="Connected Entities"
              value={fraudNetwork?.flagged_entities?.length || 0}
            />

            <KpiCard
              title="High Risk Links"
              value={fraudNetwork?.payment_clusters?.cluster_count || 0}
            />

            <KpiCard
              title="Active Alerts"
              value={anomalies?.total_anomalies || 0}
            />

          </section>


          {/* FRAUD GRAPH */}

          <section className="chart-card">

            <FraudGraph
              graphData={graphData}
              onNodeClick={handleNodeClick}
            />

          </section>


          {/* NODE DETAIL */}

          {selectedNode && (

            <div className="node-detail-panel">

              <h3>{selectedNode.name}</h3>

              <p>Risk Score: {selectedNode.risk}/100</p>

              <button onClick={closeNodeDetail}>
                Close
              </button>

            </div>

          )}

        </main>

      </div>

    </div>

  );

}