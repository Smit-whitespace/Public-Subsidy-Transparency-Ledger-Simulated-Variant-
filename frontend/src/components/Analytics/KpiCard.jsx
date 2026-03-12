import React, { useEffect, useState } from "react";
import CountUp from "react-countup";
import { 
  TrendingUp, 
  TrendingDown, 
  AlertTriangle, 
  Shield, 
  DollarSign, 
  FileText, 
  Activity,
  Eye,
  CheckCircle,
  XCircle,
  Info,
  Users
} from "lucide-react";

const iconMap = {
  subsidies: FileText,
  allocation: DollarSign,
  disbursed: DollarSign,
  flagged: AlertTriangle,
  risk: Shield,
  transparency: Eye,
  active: Activity,
  completion: CheckCircle,
  projects: FileText,
  anomalies: XCircle,
  users: Users,
  alert: AlertTriangle,
  shield: Shield,
  activity: Activity,
};

const colorMap = {
  primary: "kpi-card--primary",
  success: "kpi-card--success",
  danger: "kpi-card--danger",
  warning: "kpi-card--warning",
  info: "kpi-card--info",
};

export default function KpiCard({ 
  title, 
  value, 
  icon = "activity", 
  color = "primary",
  trend = null,
  trendLabel = "",
  subtitle = "",
  tooltip = "",
  prefix = "",
  suffix = "",
  decimals = 0,
  loading = false
}) {
  const [isVisible, setIsVisible] = useState(false);
  const [showTooltip, setShowTooltip] = useState(false);
  
  const IconComponent = iconMap[icon] || Activity;
  const colorClass = colorMap[color] || "kpi-card--primary";

  useEffect(() => {
    const timer = setTimeout(() => setIsVisible(true), 100);
    return () => clearTimeout(timer);
  }, []);

  const numericValue = typeof value === 'string' 
    ? parseFloat(value.replace(/[^0-9.-]/g, '')) 
    : value;

  const isPositiveTrend = trend > 0;
  const isNegativeTrend = trend < 0;

  if (loading) {
    return (
      <div className={`kpi-card skeleton-kpi`}>
        <div className="skeleton-line skeleton-line-short"></div>
        <div className="skeleton-line skeleton-line-medium"></div>
        <div className="skeleton-line skeleton-line-short"></div>
      </div>
    );
  }

  return (
    <div 
      className={`kpi-card ${colorClass} ${isVisible ? 'visible' : ''}`}
      onMouseEnter={() => setShowTooltip(true)}
      onMouseLeave={() => setShowTooltip(false)}
    >
      {tooltip && showTooltip && (
        <div className="kpi-tooltip">
          <Info size={14} />
          <span>{tooltip}</span>
        </div>
      )}

      <div className="kpi-header">
        <span className="kpi-title">{title}</span>
        <div className="kpi-icon">
          <IconComponent size={20} />
        </div>
      </div>

      <div className="kpi-value">
        {typeof numericValue === 'number' && !isNaN(numericValue) && typeof value === 'number' ? (
          <CountUp
            end={numericValue}
            duration={1.5}
            decimals={decimals}
            separator=","
            prefix={prefix}
            suffix={suffix}
            useEasing={true}
            useGrouping={true}
          />
        ) : (
          <span>{value}</span>
        )}
      </div>

      {subtitle && (
        <div className="kpi-subtitle">{subtitle}</div>
      )}

      {trend !== null && (
        <div className={`kpi-trend ${isPositiveTrend ? 'kpi-trend--up' : isNegativeTrend ? 'kpi-trend--down' : 'kpi-trend--neutral'}`}>
          {isPositiveTrend ? <TrendingUp size={14} /> : isNegativeTrend ? <TrendingDown size={14} /> : null}
          <span>{Math.abs(trend)}%</span>
          {trendLabel && <span className="kpi-trend-label">{trendLabel}</span>}
        </div>
      )}
    </div>
  );
}