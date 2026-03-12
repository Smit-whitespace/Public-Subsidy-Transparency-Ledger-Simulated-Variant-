import { useState, useEffect, useRef, useCallback } from 'react';
import ForceGraph2D from 'react-force-graph-2d';
import { Search, X, ZoomIn, ZoomOut, Maximize2, Clock, AlertTriangle } from 'lucide-react';
import Loader from '../components/Loader';
import Navbar from '../components/Navbar';
import Sidebar from '../components/Sidebar';
import KpiCard from '../components/Analytics/KpiCard';
import useAuth from '../hooks/useAuth';
import { getFraudNetwork, getFundFlowTimeline, getAnomalySummary } from '../services/analyticsService';

function FraudGraph({ graphData, onNodeClick }) {
  const containerRef = useRef(null);
  const graphRef = useRef(null);
  const [dimensions, setDimensions] = useState({ width: 800, height: 450 });
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
    window.addEventListener('resize', updateSize);
    return () => window.removeEventListener('resize', updateSize);
  }, []);

  const handleZoomIn = () => {
    if (graphRef.current) {
      const newZoom = Math.min(zoom * 1.5, 4);
      graphRef.current.zoom(graphRef.current.zoom() * 1.5, 400);
      setZoom(newZoom);
    }
  };

  const handleZoomOut = () => {
    if (graphRef.current) {
      graphRef.current.zoom(graphRef.current.zoom() / 1.5, 400);
      setZoom(Math.max(zoom / 1.5, 0.5));
    }
  };

  const handleReset = () => {
    if (graphRef.current) {
      graphRef.current.zoomToFit(400);
      setZoom(1);
    }
  };

  return (
    <div ref={containerRef} className="fraud-graph-container" style={{ height: 450, background: "#0f172a", borderRadius: 12, overflow: "hidden", position: "relative" }}>
      {/* Graph Controls */}
      <div className="graph-controls" style={{ position: "absolute", top: 12, right: 12, zIndex: 10, display: "flex", gap: 6 }}>
        <button onClick={handleZoomIn} className="graph-control-btn" title="Zoom In" style={{ background: "rgba(30,41,59,0.9)", border: "1px solid #334155", borderRadius: 6, padding: "6px 10px", color: "white", cursor: "pointer", display: "flex", alignItems: "center", justifyContent: "center" }}>
          <ZoomIn size={16} />
        </button>
        <button onClick={handleZoomOut} className="graph-control-btn" title="Zoom Out" style={{ background: "rgba(30,41,59,0.9)", border: "1px solid #334155", borderRadius: 6, padding: "6px 10px", color: "white", cursor: "pointer", display: "flex", alignItems: "center", justifyContent: "center" }}>
          <ZoomOut size={16} />
        </button>
        <button onClick={handleReset} className="graph-control-btn" title="Reset View" style={{ background: "rgba(30,41,59,0.9)", border: "1px solid #334155", borderRadius: 6, padding: "6px 10px", color: "white", cursor: "pointer", display: "flex", alignItems: "center", justifyContent: "center" }}>
          <Maximize2 size={16} />
        </button>
      </div>
      
      {/* Legend */}
      <div className="graph-legend" style={{ position: "absolute", bottom: 12, left: 12, zIndex: 10, display: "flex", gap: 16, background: "rgba(30,41,59,0.85)", padding: "8px 14px", borderRadius: 8, fontSize: 12 }}>
        <div style={{ display: "flex", alignItems: "center", gap: 6 }}>
          <span style={{ width: 10, height: 10, borderRadius: "50%", background: "#ef4444" }}></span>
          <span style={{ color: "#cbd5e1" }}>High Risk</span>
        </div>
        <div style={{ display: "flex", alignItems: "center", gap: 6 }}>
          <span style={{ width: 10, height: 10, borderRadius: "50%", background: "#f59e0b" }}></span>
          <span style={{ color: "#cbd5e1" }}>Medium Risk</span>
        </div>
        <div style={{ display: "flex", alignItems: "center", gap: 6 }}>
          <span style={{ width: 10, height: 10, borderRadius: "50%", background: "#22c55e" }}></span>
          <span style={{ color: "#cbd5e1" }}>Low Risk</span>
        </div>
      </div>

      {graphData.nodes.length > 0 ? (
        <ForceGraph2D
          ref={graphRef}
          graphData={graphData}
          nodeLabel="name"
          nodeColor={node => node.risk > 70 ? '#ef4444' : node.risk > 40 ? '#f59e0b' : '#22c55e'}
          nodeRelSize={6}
          linkColor={() => 'rgba(255,255,255,0.15)'}
          linkWidth={1.5}
          backgroundColor="#0f172a"
          width={dimensions.width}
          height={dimensions.height}
          onNodeClick={onNodeClick}
          cooldownTicks={100}
          d3AlphaDecay={0.02}
          d3VelocityDecay={0.3}
        />
      ) : (
        <div className="chart-empty" style={{ color: "white", paddingTop: 180 }}>No network data available — fraud analysis requires sufficient transaction data</div>
      )}
    </div>
  );
}

export default function Investigation() {
  const { user, isAuthenticated } = useAuth();
  const [loading, setLoading] = useState(true);
  const [fraudNetwork, setFraudNetwork] = useState(null);
  const [timeline, setTimeline] = useState([]);
  const [anomalies, setAnomalies] = useState(null);
  const [selectedNode, setSelectedNode] = useState(null);
  const [searchTerm, setSearchTerm] = useState("");

  useEffect(() => {
    async function loadData() {
      try {
        const [networkRes, timelineRes, anomalyRes] = await Promise.all([
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
  }, []);

  if (!isAuthenticated || !user) {
    return <div className="admin-dashboard unauthorized">Access denied</div>;
  }

  if (loading) {
    return <Loader message="Loading investigation data..." />;
  }

  // Transform fraud network data for visualization
  const graphData = (() => {
    if (!fraudNetwork) return { nodes: [], links: [] };
    
    const nodes = [];
    const links = [];
    const nodeMap = new Map();
    
    // Add flagged recipients as nodes
    const flaggedRecipients = fraudNetwork.recipient_patterns?.flagged_recipients || {};
    Object.entries(flaggedRecipients).forEach(([name, data]) => {
      if (!searchTerm || name.toLowerCase().includes(searchTerm.toLowerCase())) {
        const nodeId = `recipient_${name}`;
        nodes.push({ 
          id: nodeId, 
          name: name, 
          type: 'recipient', 
          risk: data.risk_level === 'critical' ? 90 : data.risk_level === 'high' ? 75 : data.risk_level === 'medium' ? 50 : 25
        });
        nodeMap.set(name, nodeId);
      }
    });
    
    // Add flagged owners as nodes
    const flaggedOwners = fraudNetwork.owner_patterns?.flagged_owners || {};
    Object.entries(flaggedOwners).forEach(([name, data]) => {
      if (!searchTerm || name.toLowerCase().includes(searchTerm.toLowerCase())) {
        const nodeId = `owner_${name}`;
        nodes.push({ 
          id: nodeId, 
          name: name, 
          type: 'owner', 
          risk: data.risk_level === 'critical' ? 90 : data.risk_level === 'high' ? 75 : data.risk_level === 'medium' ? 50 : 25
        });
        nodeMap.set(name, nodeId);
      }
    });
    
    // Create links between recipients and their subsidies
    Object.entries(flaggedRecipients).forEach(([recipient, data]) => {
      const sourceId = nodeMap.get(recipient);
      if (sourceId && data.subsidies) {
        data.subsidies.forEach((sub, idx) => {
          const targetId = `subsidy_${sub.id}`;
          if (!nodeMap.has(targetId)) {
            nodes.push({ id: targetId, name: sub.title || `Subsidy ${sub.id}`, type: 'subsidy', risk: 40 });
            nodeMap.set(targetId, targetId);
          }
          links.push({ source: sourceId, target: targetId, type: 'receives' });
        });
      }
    });
    
    return { nodes, links };
  })();

  const handleNodeClick = useCallback((node) => {
    setSelectedNode(node);
  }, []);

  const closeNodeDetail = () => setSelectedNode(null);

  return (
    <div className="admin-dashboard">
      <Navbar />
      <div className="admin-layout">
        <Sidebar />
        <main className="admin-content">
          <header className="dashboard-header">
            <div className="dashboard-header-top">
              <div>
                <h1>Fraud Investigation Center</h1>
                <p>Visual analysis of suspicious relationships and anomalies</p>
              </div>
              <div className="dashboard-header-meta">
                <span className="dashboard-user-badge">AI-Powered</span>
              </div>
            </div>
          </header>

          {/* Investigation KPIs */}
          <section className="dashboard-kpis">
            <KpiCard title="Connected Entities" value={fraudNetwork?.flagged_entities?.length || 0} icon="users" color="primary" tooltip="Entities linked in fraud network" />
            <KpiCard title="High Risk Links" value={fraudNetwork?.payment_clusters?.cluster_count || 0} icon="alert" color="danger" tooltip="Suspicious relationship connections" />
            <KpiCard title="Active Alerts" value={anomalies?.total_anomalies || 0} icon="activity" color="warning" tooltip="Total anomaly alerts" />
            <KpiCard title="Flagged Recipients" value={fraudNetwork?.recipient_patterns?.flagged_count || 0} icon="shield" color="danger" tooltip="Recipients with high risk" />
            <KpiCard title="Network Risk Score" value={fraudNetwork?.network_risk_score || 0} suffix="/100" decimals={1} icon="risk" color="warning" tooltip="Average risk across network" />
          </section>

          {/* Fraud Network Graph */}
          <section className="chart-card">
            <div className="chart-card-header" style={{ justifyContent: "space-between" }}>
              <div style={{ display: "flex", alignItems: "center", gap: 12 }}>
                <h2>Fraud Network Visualization</h2>
                <span className="chart-card-badge">Interactive</span>
              </div>
              {/* Search Bar */}
              <div className="graph-search" style={{ position: "relative" }}>
                <Search size={16} style={{ position: "absolute", left: 10, top: "50%", transform: "translateY(-50%)", color: "#64748b" }} />
                <input
                  type="text"
                  placeholder="Search entities..."
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                  style={{
                    background: "#1e293b",
                    border: "1px solid #334155",
                    borderRadius: 6,
                    padding: "6px 12px 6px 34px",
                    color: "white",
                    fontSize: 13,
                    width: 200,
                    outline: "none"
                  }}
                />
                {searchTerm && (
                  <button
                    onClick={() => setSearchTerm("")}
                    style={{
                      position: "absolute",
                      right: 8,
                      top: "50%",
                      transform: "translateY(-50%)",
                      background: "none",
                      border: "none",
                      color: "#64748b",
                      cursor: "pointer"
                    }}
                  >
                    <X size={14} />
                  </button>
                )}
              </div>
            </div>
            <FraudGraph graphData={graphData} onNodeClick={handleNodeClick} />
            
            {/* Node Details Panel */}
            {selectedNode && (
              <div className="node-detail-panel" style={{
                position: "absolute",
                top: 80,
                right: 24,
                width: 280,
                background: "#1e293b",
                border: "1px solid #334155",
                borderRadius: 12,
                padding: 16,
                zIndex: 20,
                boxShadow: "0 10px 40px rgba(0,0,0,0.5)"
              }}>
                <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 12 }}>
                  <h3 style={{ margin: 0, fontSize: 14, color: "white" }}>Entity Details</h3>
                  <button onClick={closeNodeDetail} style={{ background: "none", border: "none", color: "#94a3b8", cursor: "pointer" }}>
                    <X size={18} />
                  </button>
                </div>
                <div style={{ display: "flex", flexDirection: "column", gap: 10 }}>
                  <div>
                    <span style={{ color: "#64748b", fontSize: 12 }}>Name</span>
                    <div style={{ color: "white", fontSize: 14, fontWeight: 500 }}>{selectedNode.name}</div>
                  </div>
                  <div style={{ display: "flex", gap: 16 }}>
                    <div>
                      <span style={{ color: "#64748b", fontSize: 12 }}>Type</span>
                      <div style={{ color: "#e2e8f0", fontSize: 13, textTransform: "capitalize" }}>{selectedNode.type || 'Entity'}</div>
                    </div>
                    <div>
                      <span style={{ color: "#64748b", fontSize: 12 }}>Risk Score</span>
                      <div style={{ 
                        color: selectedNode.risk > 70 ? '#ef4444' : selectedNode.risk > 40 ? '#f59e0b' : '#22c55e',
                        fontSize: 13, 
                        fontWeight: 600 
                      }}>{selectedNode.risk || 0}/100</div>
                    </div>
                  </div>
                  <div style={{ 
                    marginTop: 8, 
                    padding: "8px 12px", 
                    background: selectedNode.risk > 70 ? 'rgba(239,68,68,0.15)' : selectedNode.risk > 40 ? 'rgba(245,158,11,0.15)' : 'rgba(34,197,94,0.15)',
                    borderRadius: 6,
                    borderLeft: `3px solid ${selectedNode.risk > 70 ? '#ef4444' : selectedNode.risk > 40 ? '#f59e0b' : '#22c55e'}`
                  }}>
                    <span style={{ color: "#cbd5e1", fontSize: 12 }}>
                      {selectedNode.risk > 70 ? '⚠ High Risk Entity - Review Required' : selectedNode.risk > 40 ? '⚡ Medium Risk - Monitor' : '✓ Low Risk - Normal'}
                    </span>
                  </div>
                </div>
              </div>
            )}
          </section>

          <div className="dashboard-grid-two">
            {/* Risk Timeline */}
            <section className="chart-card">
              <div className="chart-card-header">
                <h2>Risk Timeline</h2>
                <Clock size={18} />
              </div>
              <div className="risk-timeline">
                {timeline.length > 0 ? timeline.slice(0, 8).map((item, idx) => (
                  <div key={idx} className="timeline-item">
                    <div className="timeline-marker"></div>
                    <div className="timeline-content">
                      <div className="timeline-title">{item.event || 'Transaction'}</div>
                      <div className="timeline-meta">{item.date || item.timestamp}</div>
                    </div>
                  </div>
                )) : (
                  <div className="chart-empty">No timeline events recorded yet</div>
                )}
              </div>
            </section>

            {/* Suspicious Activity Feed */}
            <section className="chart-card">
              <div className="chart-card-header">
                <h2>Suspicious Activity</h2>
                <AlertTriangle size={18} />
              </div>
              <div className="suspicious-feed">
                {(anomalies?.recent_alerts || []).length > 0 ? (
                  anomalies.recent_alerts.slice(0, 6).map((item, idx) => (
                    <div key={idx} className={`suspicious-item severity-${item.severity}`}>
                      <div className="suspicious-header">
                        <span className={`severity-badge ${item.severity}`}>{item.severity}</span>
                        <span className="suspicious-type">{item.type}</span>
                      </div>
                      <div className="suspicious-desc">{item.description}</div>
                    </div>
                  ))
                ) : (
                  <div className="anomaly-clean">
                    <span className="anomaly-clean-icon">✓</span>
                    No suspicious activity detected
                  </div>
                )}
              </div>
            </section>
          </div>
        </main>
      </div>
    </div>
  );
}
