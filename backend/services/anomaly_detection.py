"""
backend/services/anomaly_detection.py

AI-powered anomaly detection service for identifying potential corruption patterns
in subsidy disbursements. This service analyzes financial patterns, timing anomalies,
and statistical outliers to issue real-time warnings.

Detection methods:
1. Statistical outlier detection (Z-score based)
2. Disbursement timing anomaly detection
3. Amount pattern analysis
4. Multi-indicator correlation analysis
"""

from decimal import Decimal
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import func

from backend.models.subsidy import Subsidy
from backend.models.disbursement import Disbursement
from backend.models.risk_event import RiskEvent


class AnomalyType:
    """Anomaly classification constants"""
    OVER_DISBURSEMENT = "over_disbursement"
    SPIKE_DETECTION = "spike_detection"
    TIMING_ANOMALY = "timing_anomaly"
    UNUSUAL_PATTERN = "unusual_pattern"
    CORRELATION_FLAG = "correlation_flag"
    RAPID_SUCCESSION = "rapid_succession"
    SUSPICIOUS_AMOUNT = "suspicious_amount"


class AnomalySeverity:
    """Severity levels for anomalies"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class AnomalyAlert:
    """Anomaly alert structure"""
    def __init__(
        self,
        anomaly_type: str,
        severity: str,
        message: str,
        subsidy_id: int,
        details: Dict[str, Any],
        confidence: float = 0.0
    ):
        self.anomaly_type = anomaly_type
        self.severity = severity
        self.message = message
        self.subsidy_id = subsidy_id
        self.details = details
        self.confidence = confidence
        self.timestamp = datetime.utcnow()
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "anomaly_type": self.anomaly_type,
            "severity": self.severity,
            "message": self.message,
            "subsidy_id": self.subsidy_id,
            "details": self.details,
            "confidence": self.confidence,
            "timestamp": self.timestamp.isoformat()
        }


class AnomalyDetectionService:
    """Main anomaly detection service"""
    
    # Configuration thresholds
    Z_SCORE_THRESHOLD = 2.5  # Standard deviations for outlier detection
    SPIKE_MULTIPLIER = 2.0  # Amount considered a spike vs average
    RAPID_SUCCESSION_HOURS = 24  # Disbursements within this window flagged
    CORRELATION_THRESHOLD = 0.7  # Minimum correlation for multi-indicator
    
    def __init__(self, db: Session):
        self.db = db
    
    def analyze_all_subsidies(self) -> List[AnomalyAlert]:
        """
        Analyze all active subsidies for anomalies.
        Returns list of alerts sorted by severity.
        """
        alerts = []
        
        subsidies = self.db.query(Subsidy).filter(
            Subsidy.status == "active"
        ).all()
        
        for subsidy in subsidies:
            subsidy_alerts = self.analyze_subsidy(subsidy.id)
            alerts.extend(subsidy_alerts)
        
        # Sort by severity priority
        severity_order = {
            AnomalySeverity.CRITICAL: 0,
            AnomalySeverity.HIGH: 1,
            AnomalySeverity.MEDIUM: 2,
            AnomalySeverity.LOW: 3
        }
        
        alerts.sort(key=lambda a: severity_order.get(a.severity, 99))
        
        return alerts
    
    def analyze_subsidy(self, subsidy_id: int) -> List[AnomalyAlert]:
        """
        Perform comprehensive anomaly analysis on a single subsidy.
        """
        alerts = []
        
        subsidy = self.db.query(Subsidy).filter(
            Subsidy.id == subsidy_id
        ).first()
        
        if not subsidy:
            return alerts
        
        disbursements = self.db.query(Disbursement).filter(
            Disbursement.subsidy_id == subsidy_id
        ).order_by(Disbursement.date.asc()).all()
        
        if not disbursements:
            return alerts
        
        # 1. Statistical outlier detection
        outlier_alerts = self._detect_statistical_outliers(
            subsidy, disbursements
        )
        alerts.extend(outlier_alerts)
        
        # 2. Spike detection
        spike_alerts = self._detect_amount_spikes(
            subsidy, disbursements
        )
        alerts.extend(spike_alerts)
        
        # 3. Timing anomaly detection
        timing_alerts = self._detect_timing_anomalies(
            subsidy, disbursements
        )
        alerts.extend(timing_alerts)
        
        # 4. Rapid succession detection
        rapid_alerts = self._detect_rapid_succession(
            subsidy, disbursements
        )
        alerts.extend(rapid_alerts)
        
        # 5. Correlation analysis
        correlation_alerts = self._analyze_correlations(
            subsidy, disbursements
        )
        alerts.extend(correlation_alerts)
        
        # 6. Over-disbursement check
        over_disbursement_alerts = self._check_over_disbursement(
            subsidy, disbursements
        )
        alerts.extend(over_disbursement_alerts)
        
        return alerts
    
    def _detect_statistical_outliers(
        self,
        subsidy: Subsidy,
        disbursements: List[Disbursement]
    ) -> List[AnomalyAlert]:
        """Detect statistical outliers using Z-score method"""
        alerts = []
        
        if len(disbursements) < 3:
            return alerts
        
        amounts = [float(d.amount) for d in disbursements]
        mean = sum(amounts) / len(amounts)
        variance = sum((x - mean) ** 2 for x in amounts) / len(amounts)
        std_dev = variance ** 0.5
        
        if std_dev == 0:
            return alerts
        
        for d in disbursements:
            z_score = abs(float(d.amount) - mean) / std_dev
            
            if z_score > self.Z_SCORE_THRESHOLD:
                severity = (
                    AnomalySeverity.CRITICAL if z_score > 4
                    else AnomalySeverity.HIGH if z_score > 3
                    else AnomalySeverity.MEDIUM
                )
                
                alert = AnomalyAlert(
                    anomaly_type=AnomalyType.SPIKE_DETECTION,
                    severity=severity,
                    message=f"Statistical outlier detected: {d.amount} (Z-score: {z_score:.2f})",
                    subsidy_id=subsidy.id,
                    details={
                        "disbursement_id": d.id,
                        "amount": str(d.amount),
                        "mean": mean,
                        "std_dev": std_dev,
                        "z_score": round(z_score, 2)
                    },
                    confidence=min(1.0, z_score / 5)
                )
                alerts.append(alert)
        
        return alerts
    
    def _detect_amount_spikes(
        self,
        subsidy: Subsidy,
        disbursements: List[Disbursement]
    ) -> List[AnomalyAlert]:
        """Detect sudden large disbursements compared to average"""
        alerts = []
        
        if len(disbursements) < 2:
            return alerts
        
        total = sum(float(d.amount) for d in disbursements)
        avg = total / len(disbursements)
        
        for d in disbursements:
            amount = float(d.amount)
            if amount > avg * self.SPIKE_MULTIPLIER:
                ratio = amount / avg
                severity = (
                    AnomalySeverity.CRITICAL if ratio > 5
                    else AnomalySeverity.HIGH if ratio > 3
                    else AnomalySeverity.MEDIUM
                )
                
                alert = AnomalyAlert(
                    anomaly_type=AnomalyType.SPIKE_DETECTION,
                    severity=severity,
                    message=f"Unusual spike: {d.amount} ({ratio:.1f}x average)",
                    subsidy_id=subsidy.id,
                    details={
                        "disbursement_id": d.id,
                        "amount": str(d.amount),
                        "average": avg,
                        "ratio": round(ratio, 2)
                    },
                    confidence=min(1.0, ratio / 10)
                )
                alerts.append(alert)
        
        return alerts
    
    def _detect_timing_anomalies(
        self,
        subsidy: Subsidy,
        disbursements: List[Disbursement]
    ) -> List[AnomalyAlert]:
        """Detect unusual timing patterns in disbursements"""
        alerts = []
        
        if len(disbursements) < 2:
            return alerts
        
        for i in range(len(disbursements) - 1):
            d1 = disbursements[i]
            d2 = disbursements[i + 1]
            
            if not d1.date or not d2.date:
                continue
            
            days_diff = (d2.date - d1.date).days
            
            # Flag very short intervals (potential split to avoid thresholds)
            if days_diff == 0:
                alert = AnomalyAlert(
                    anomaly_type=AnomalyType.TIMING_ANOMALY,
                    severity=AnomalySeverity.HIGH,
                    message=f"Same-day disbursements detected",
                    subsidy_id=subsidy.id,
                    details={
                        "disbursement_ids": [d1.id, d2.id],
                        "amounts": [str(d1.amount), str(d2.amount)],
                        "days_apart": days_diff
                    },
                    confidence=0.9
                )
                alerts.append(alert)
            
            # Flag very long gaps (potential delayed欺诈)
            elif days_diff > 180:
                alert = AnomalyAlert(
                    anomaly_type=AnomalyType.TIMING_ANOMALY,
                    severity=AnomalySeverity.MEDIUM,
                    message=f"Unusually long gap between disbursements",
                    subsidy_id=subsidy.id,
                    details={
                        "disbursement_ids": [d1.id, d2.id],
                        "days_apart": days_diff
                    },
                    confidence=0.6
                )
                alerts.append(alert)
        
        return alerts
    
    def _detect_rapid_succession(
        self,
        subsidy: Subsidy,
        disbursements: List[Disbursement]
    ) -> List[AnomalyAlert]:
        """Detect multiple disbursements in rapid succession"""
        alerts = []
        
        if len(disbursements) < 2:
            return alerts
        
        # Sort by date
        sorted_disbursements = sorted(
            disbursements,
            key=lambda d: d.date or datetime.min
        )
        
        rapid_count = 1
        rapid_disbursements = [sorted_disbursements[0].id]
        
        for i in range(1, len(sorted_disbursements)):
            curr = sorted_disbursements[i]
            prev = sorted_disbursements[i - 1]
            
            if not curr.date or not prev.date:
                continue
            
            hours_diff = (curr.date - prev.date).total_seconds() / 3600
            
            if hours_diff <= self.RAPID_SUCCESSION_HOURS:
                rapid_count += 1
                rapid_disbursements.append(curr.id)
            else:
                # Check if we had a rapid succession sequence
                if rapid_count >= 3:
                    total_amount = sum(
                        float(d.amount) for d in sorted_disbursements
                        if d.id in rapid_disbursements
                    )
                    
                    alert = AnomalyAlert(
                        anomaly_type=AnomalyType.RAPID_SUCCESSION,
                        severity=(
                            AnomalySeverity.CRITICAL if rapid_count >= 5
                            else AnomalySeverity.HIGH if rapid_count >= 4
                            else AnomalySeverity.MEDIUM
                        ),
                        message=f"{rapid_count} rapid successive disbursements detected",
                        subsidy_id=subsidy.id,
                        details={
                            "disbursement_ids": rapid_disbursements,
                            "count": rapid_count,
                            "total_amount": total_amount
                        },
                        confidence=0.85
                    )
                    alerts.append(alert)
                
                # Reset for new sequence
                rapid_count = 1
                rapid_disbursements = [curr.id]
        
        # Check final sequence
        if rapid_count >= 3:
            total_amount = sum(
                float(d.amount) for d in sorted_disbursements
                if d.id in rapid_disbursements
            )
            
            alert = AnomalyAlert(
                anomaly_type=AnomalyType.RAPID_SUCCESSION,
                severity=(
                    AnomalySeverity.CRITICAL if rapid_count >= 5
                    else AnomalySeverity.HIGH if rapid_count >= 4
                    else AnomalySeverity.MEDIUM
                ),
                message=f"{rapid_count} rapid successive disbursements detected",
                subsidy_id=subsidy.id,
                details={
                    "disbursement_ids": rapid_disbursements,
                    "count": rapid_count,
                    "total_amount": total_amount
                },
                confidence=0.85
            )
            alerts.append(alert)
        
        return alerts
    
    def _analyze_correlations(
        self,
        subsidy: Subsidy,
        disbursements: List[Disbursement]
    ) -> List[AnomalyAlert]:
        """Analyze multiple risk indicators for correlation patterns"""
        alerts = []
        
        # Calculate multiple risk factors
        risk_factors = {
            "has_late": False,
            "has_missing_proof": False,
            "has_high_amount": False,
            "has_unusual_timing": False
        }
        
        total_allocation = float(subsidy.total_allocation or 0)
        
        for d in disbursements:
            if d.is_late:
                risk_factors["has_late"] = True
            
            if not d.proof_document_url:
                risk_factors["has_missing_proof"] = True
            
            if total_allocation > 0 and float(d.amount) > total_allocation * 0.5:
                risk_factors["has_high_amount"] = True
        
        # Count risk factors
        risk_count = sum(risk_factors.values())
        
        if risk_count >= 3:
            severity = (
                AnomalySeverity.CRITICAL if risk_count == 4
                else AnomalySeverity.HIGH
            )
            
            alert = AnomalyAlert(
                anomaly_type=AnomalyType.CORRELATION_FLAG,
                severity=severity,
                message=f"Multiple risk indicators correlated ({risk_count}/4 factors)",
                subsidy_id=subsidy.id,
                details=risk_factors,
                confidence=0.8
            )
            alerts.append(alert)
        
        return alerts
    
    def _check_over_disbursement(
        self,
        subsidy: Subsidy,
        disbursements: List[Disbursement]
    ) -> List[AnomalyAlert]:
        """Check if total disbursed exceeds allocation"""
        alerts = []
        
        total_allocation = float(subsidy.total_allocation or 0)
        
        if total_allocation <= 0:
            return alerts
        
        total_disbursed = sum(float(d.amount) for d in disbursements)
        ratio = total_disbursed / total_allocation
        
        if ratio > 1.0:
            overage = total_disbursed - total_allocation
            severity = (
                AnomalySeverity.CRITICAL if ratio > 1.5
                else AnomalySeverity.HIGH if ratio > 1.25
                else AnomalySeverity.MEDIUM
            )
            
            alert = AnomalyAlert(
                anomaly_type=AnomalyType.OVER_DISBURSEMENT,
                severity=severity,
                message=f"Over-disbursement: {ratio*100:.0f}% of allocation",
                subsidy_id=subsidy.id,
                details={
                    "total_allocation": total_allocation,
                    "total_disbursed": total_disbursed,
                    "overage": overage,
                    "percentage": round(ratio * 100, 1)
                },
                confidence=0.95
            )
            alerts.append(alert)
        
        return alerts
    
    def get_alert_summary(self) -> Dict[str, Any]:
        """
        Get a summary of all current anomalies in the system.
        Useful for dashboard display.
        """
        all_alerts = self.analyze_all_subsidies()
        
        summary = {
            "total_alerts": len(all_alerts),
            "by_severity": {
                "critical": 0,
                "high": 0,
                "medium": 0,
                "low": 0
            },
            "by_type": {},
            "recent_alerts": [],
            "highest_risk_subsidies": []
        }
        
        # Count by severity
        for alert in all_alerts:
            summary["by_severity"][alert.severity] += 1
            
            # Count by type
            if alert.anomaly_type not in summary["by_type"]:
                summary["by_type"][alert.anomaly_type] = 0
            summary["by_type"][alert.anomaly_type] += 1
        
        # Get top 5 recent critical/high alerts
        summary["recent_alerts"] = [
            a.to_dict() for a in all_alerts[:5]
        ]
        
        # Get unique subsidy IDs with critical/high alerts
        critical_subsidy_ids = set(
            a.subsidy_id for a in all_alerts
            if a.severity in [AnomalySeverity.CRITICAL, AnomalySeverity.HIGH]
        )
        
        for sid in list(critical_subsidy_ids)[:5]:
            subsidy = self.db.query(Subsidy).filter(Subsidy.id == sid).first()
            if subsidy:
                summary["highest_risk_subsidies"].append({
                    "subsidy_id": sid,
                    "title": subsidy.title,
                    "sector": subsidy.sector,
                    "risk_score": float(subsidy.risk_score or 0)
                })
        
        return summary


def get_anomaly_summary(db: Session) -> Dict[str, Any]:
    """
    Public function to get anomaly detection summary.
    Can be called by API endpoints.
    """
    service = AnomalyDetectionService(db)
    return service.get_alert_summary()


def check_subsidy_anomalies(db: Session, subsidy_id: int) -> List[Dict[str, Any]]:
    """
    Public function to check anomalies for a specific subsidy.
    """
    service = AnomalyDetectionService(db)
    alerts = service.analyze_subsidy(subsidy_id)
    return [a.to_dict() for a in alerts]