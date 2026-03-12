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
from backend.models.project import Project


class AnomalyType:
    """Anomaly classification constants"""
    OVER_DISBURSEMENT = "over_disbursement"
    SPIKE_DETECTION = "spike_detection"
    TIMING_ANOMALY = "timing_anomaly"
    UNUSUAL_PATTERN = "unusual_pattern"
    CORRELATION_FLAG = "correlation_flag"
    RAPID_SUCCESSION = "rapid_succession"
    SUSPICIOUS_AMOUNT = "suspicious_amount"
    CIRCULAR_FUND_FLOW = "circular_fund_flow"
    SHELL_ENTITY = "shell_entity"
    DUPLICATE_PAYMENT = "duplicate_payment"
    HIGH_RISK_CLUSTER = "high_risk_cluster"
    VELOCITY_ANOMALY = "velocity_anomaly"
    SEASONAL_DEVIATION = "seasonal_deviation"


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
        
        # 7. Shell entity detection
        shell_alerts = self._detect_shell_entity(subsidy, disbursements)
        alerts.extend(shell_alerts)
        
        # 8. Duplicate payment detection
        duplicate_alerts = self._detect_duplicate_payment(subsidy, disbursements)
        alerts.extend(duplicate_alerts)
        
        # 9. High-risk cluster detection
        cluster_alerts = self._detect_high_risk_cluster(subsidy, disbursements)
        alerts.extend(cluster_alerts)
        
        # 10. Velocity anomaly detection
        velocity_alerts = self._detect_velocity_anomaly(subsidy, disbursements)
        alerts.extend(velocity_alerts)
        
        # 11. Seasonal deviation detection
        seasonal_alerts = self._detect_seasonal_deviation(subsidy, disbursements)
        alerts.extend(seasonal_alerts)
        
        # 12. Circular fund flow detection
        circular_alerts = self._detect_circular_fund_flow(subsidy, disbursements)
        alerts.extend(circular_alerts)
        
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
    
    def _detect_shell_entity(
        self,
        subsidy: Subsidy,
        disbursements: List[Disbursement]
    ) -> List[AnomalyAlert]:
        """Detect potential shell entities with minimal activity but high funding"""
        alerts = []
        
        total_allocation = float(subsidy.total_allocation or 0)
        
        if total_allocation < 1000000:  # Only check large subsidies
            return alerts
        
        # Shell entity indicators: high allocation, few projects, missing audit trail
        projects_count = self.db.query(Project).filter(
            Project.subsidy_id == subsidy.id
        ).count()
        
        if projects_count <= 1 and total_allocation > 5000000:
            alert = AnomalyAlert(
                anomaly_type=AnomalyType.SHELL_ENTITY,
                severity=AnomalySeverity.HIGH,
                message=f"Potential shell entity: High allocation ({total_allocation:,.0f}) with minimal projects",
                subsidy_id=subsidy.id,
                details={
                    "total_allocation": total_allocation,
                    "projects_count": projects_count,
                    "recipient": subsidy.recipient
                },
                confidence=0.75
            )
            alerts.append(alert)
        
        return alerts
    
    def _detect_duplicate_payment(
        self,
        subsidy: Subsidy,
        disbursements: List[Disbursement]
    ) -> List[AnomalyAlert]:
        """Detect duplicate payment patterns"""
        alerts = []
        
        amount_map = {}
        for d in disbursements:
            amount_key = (str(d.amount), d.date.isoformat() if d.date else None)
            if amount_key in amount_map:
                alert = AnomalyAlert(
                    anomaly_type=AnomalyType.DUPLICATE_PAYMENT,
                    severity=AnomalySeverity.CRITICAL,
                    message=f"Duplicate payment detected: {d.amount} on same date",
                    subsidy_id=subsidy.id,
                    details={
                        "disbursement_ids": [amount_map[amount_key], d.id],
                        "amount": str(d.amount),
                        "date": str(d.date)
                    },
                    confidence=0.95
                )
                alerts.append(alert)
            else:
                amount_map[amount_key] = d.id
        
        return alerts
    
    def _detect_high_risk_cluster(
        self,
        subsidy: Subsidy,
        disbursements: List[Disbursement]
    ) -> List[AnomalyAlert]:
        """Detect high-risk clusters within sectors"""
        alerts = []
        
        if not subsidy.sector:
            return alerts
        
        # Get all subsidies in same sector
        sector_subsidies = self.db.query(Subsidy).filter(
            Subsidy.sector == subsidy.sector,
            Subsidy.id != subsidy.id
        ).all()
        
        if len(sector_subsidies) < 3:
            return alerts
        
        # Calculate sector risk average
        risk_scores = [float(s.risk_score or 0) for s in sector_subsidies]
        avg_risk = sum(risk_scores) / len(risk_scores) if risk_scores else 0
        
        current_risk = float(subsidy.risk_score or 0)
        if current_risk > avg_risk * 1.5 and current_risk > 70:
            alert = AnomalyAlert(
                anomaly_type=AnomalyType.HIGH_RISK_CLUSTER,
                severity=AnomalySeverity.HIGH,
                message=f"High-risk cluster in {subsidy.sector} sector (avg: {avg_risk:.0f}, this: {current_risk:.0f})",
                subsidy_id=subsidy.id,
                details={
                    "sector": subsidy.sector,
                    "sector_avg_risk": avg_risk,
                    "current_risk": current_risk,
                    "sector_subsidy_count": len(sector_subsidies)
                },
                confidence=0.8
            )
            alerts.append(alert)
        
        return alerts
    
    def _detect_velocity_anomaly(
        self,
        subsidy: Subsidy,
        disbursements: List[Disbursement]
    ) -> List[AnomalyAlert]:
        """Detect unusual payment velocity patterns"""
        alerts = []
        
        if len(disbursements) < 3:
            return alerts
        
        sorted_disb = sorted(disbursements, key=lambda d: d.date or datetime.min)
        
        # Check for concentration of payments in short time
        if len(sorted_disb) >= 3:
            first_date = sorted_disb[0].date
            last_date = sorted_disb[-1].date
            
            if first_date and last_date:
                total_days = (last_date - first_date).days
                
                # If more than 50% of disbursements happen in first 20% of time
                if total_days > 30:
                    cutoff_date = first_date + timedelta(days=int(total_days * 0.2))
                    early_disb = [d for d in sorted_disb if d.date and d.date <= cutoff_date]
                    
                    if len(early_disb) >= len(sorted_disb) * 0.5:
                        total_early = sum(float(d.amount) for d in early_disb)
                        total_all = sum(float(d.amount) for d in sorted_disb)
                        
                        alert = AnomalyAlert(
                            anomaly_type=AnomalyType.VELOCITY_ANOMALY,
                            severity=AnomalySeverity.MEDIUM,
                            message=f"Unusual payment velocity: {len(early_disb)}/{len(sorted_disb)} payments in first 20% of period",
                            subsidy_id=subsidy.id,
                            details={
                                "early_payment_count": len(early_disb),
                                "total_payment_count": len(sorted_disb),
                                "early_amount_pct": round((total_early/total_all)*100, 1) if total_all > 0 else 0,
                                "total_days": total_days
                            },
                            confidence=0.7
                        )
                        alerts.append(alert)
        
        return alerts
    
    def _detect_seasonal_deviation(
        self,
        subsidy: Subsidy,
        disbursements: List[Disbursement]
    ) -> List[AnomalyAlert]:
        """Detect unusual seasonal patterns in disbursements"""
        alerts = []
        
        if len(disbursements) < 5:
            return alerts
        
        # Group by month
        monthly_amounts = {}
        for d in disbursements:
            if d.date:
                month_key = d.date.month
                if month_key not in monthly_amounts:
                    monthly_amounts[month_key] = []
                monthly_amounts[month_key].append(float(d.amount))
        
        if not monthly_amounts:
            return alerts
        
        # Calculate average for each month
        monthly_avg = {
            m: sum(amounts) / len(amounts) 
            for m, amounts in monthly_amounts.items()
        }
        
        overall_avg = sum(monthly_avg.values()) / len(monthly_avg)
        
        # Find months with significantly higher/lower amounts
        for month, avg in monthly_avg.items():
            if overall_avg > 0 and abs(avg - overall_avg) / overall_avg > 0.5:
                month_name = ["", "Jan", "Feb", "Mar", "Apr", "May", "Jun",
                              "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"][month]
                direction = "above" if avg > overall_avg else "below"
                
                alert = AnomalyAlert(
                    anomaly_type=AnomalyType.SEASONAL_DEVIATION,
                    severity=AnomalySeverity.LOW,
                    message=f"Seasonal deviation: {month_name} average {direction} normal ({abs(avg-overall_avg)/overall_avg*100:.0f}%)",
                    subsidy_id=subsidy.id,
                    details={
                        "month": month_name,
                        "monthly_avg": avg,
                        "overall_avg": overall_avg,
                        "deviation_pct": round(abs(avg-overall_avg)/overall_avg*100, 1)
                    },
                    confidence=0.5
                )
                alerts.append(alert)
        
        return alerts
    
    def _detect_circular_fund_flow(
        self,
        subsidy: Subsidy,
        disbursements: List[Disbursement]
    ) -> List[AnomalyAlert]:
        """Detect suspicious circular fund flow patterns between entities"""
        alerts = []
        
        # Check if recipient appears as contractor in other subsidies
        recipient = subsidy.recipient
        if not recipient:
            return alerts
        
        # Look for the recipient in projects where they might be contractors
        # This requires checking across subsidies
        all_projects = self.db.query(Project).filter(
            Project.contractor_name.ilike(f"%{recipient}%")
        ).all()
        
        if len(all_projects) >= 3:
            # Get unique subsidies funding these projects
            linked_subsidy_ids = list(set(p.subsidy_id for p in all_projects))
            
            if len(linked_subsidy_ids) >= 2:
                total_linked = sum(float(p.budget or 0) for p in all_projects)
                
                alert = AnomalyAlert(
                    anomaly_type=AnomalyType.CIRCULAR_FUND_FLOW,
                    severity=AnomalySeverity.CRITICAL,
                    message=f"Potential circular flow: {recipient} linked to {len(linked_subsidy_ids)} subsidies as contractor",
                    subsidy_id=subsidy.id,
                    details={
                        "recipient": recipient,
                        "linked_subsidy_count": len(linked_subsidy_ids),
                        "linked_projects": len(all_projects),
                        "total_linked_budget": total_linked
                    },
                    confidence=0.85
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