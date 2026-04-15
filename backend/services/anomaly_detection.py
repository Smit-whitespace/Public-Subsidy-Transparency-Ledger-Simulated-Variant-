"""
backend/services/anomaly_detection.py

AI-powered anomaly detection service for identifying potential corruption
patterns in subsidy disbursements.
"""

from typing import List, Dict, Any
from datetime import datetime, timedelta
from sqlalchemy.orm import Session

from backend.models.subsidy import Subsidy
from backend.models.disbursement import Disbursement
from backend.models.project import Project


class AnomalyType:
    OVER_DISBURSEMENT = "over_disbursement"
    SPIKE_DETECTION = "spike_detection"
    TIMING_ANOMALY = "timing_anomaly"
    CORRELATION_FLAG = "correlation_flag"
    RAPID_SUCCESSION = "rapid_succession"
    CIRCULAR_FUND_FLOW = "circular_fund_flow"
    SHELL_ENTITY = "shell_entity"
    DUPLICATE_PAYMENT = "duplicate_payment"
    HIGH_RISK_CLUSTER = "high_risk_cluster"
    VELOCITY_ANOMALY = "velocity_anomaly"
    SEASONAL_DEVIATION = "seasonal_deviation"


class AnomalySeverity:
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class AnomalyAlert:

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

    def to_dict(self):
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

    Z_SCORE_THRESHOLD = 2.5
    SPIKE_MULTIPLIER = 2.0
    RAPID_SUCCESSION_HOURS = 24

    def __init__(self, db: Session):
        self.db = db

    # --------------------------------------------------
    # MAIN ENTRY
    # --------------------------------------------------

    def analyze_all_subsidies(self) -> List[AnomalyAlert]:

        alerts = []

        subsidies = self.db.query(Subsidy).filter(
            Subsidy.status == "active"
        ).all()

        for subsidy in subsidies:
            alerts.extend(self.analyze_subsidy(subsidy.id))

        severity_order = {
            AnomalySeverity.CRITICAL: 0,
            AnomalySeverity.HIGH: 1,
            AnomalySeverity.MEDIUM: 2,
            AnomalySeverity.LOW: 3
        }

        alerts.sort(key=lambda a: severity_order.get(a.severity, 99))

        return alerts

    # --------------------------------------------------

    def analyze_subsidy(self, subsidy_id: int) -> List[AnomalyAlert]:

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

        alerts.extend(self._detect_statistical_outliers(subsidy, disbursements))
        alerts.extend(self._detect_amount_spikes(subsidy, disbursements))
        alerts.extend(self._detect_timing_anomalies(subsidy, disbursements))
        alerts.extend(self._detect_rapid_succession(subsidy, disbursements))
        alerts.extend(self._analyze_correlations(subsidy, disbursements))
        alerts.extend(self._check_over_disbursement(subsidy, disbursements))
        alerts.extend(self._detect_shell_entity(subsidy))
        alerts.extend(self._detect_duplicate_payment(subsidy, disbursements))
        alerts.extend(self._detect_high_risk_cluster(subsidy))
        alerts.extend(self._detect_velocity_anomaly(subsidy, disbursements))
        alerts.extend(self._detect_seasonal_deviation(subsidy, disbursements))

        # circular detection must never crash analytics
        try:
            alerts.extend(
                self._detect_circular_fund_flow(subsidy)
            )
        except Exception as e:
            print("Circular detection failed:", e)

        return alerts

    # --------------------------------------------------
    # DETECTORS
    # --------------------------------------------------

    def _detect_statistical_outliers(self, subsidy, disbursements):

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

            z = abs(float(d.amount) - mean) / std_dev

            if z > self.Z_SCORE_THRESHOLD:

                alerts.append(
                    AnomalyAlert(
                        AnomalyType.SPIKE_DETECTION,
                        AnomalySeverity.HIGH,
                        f"Statistical outlier detected: {d.amount}",
                        subsidy.id,
                        {"z_score": round(z, 2)},
                        min(1.0, z / 5)
                    )
                )

        return alerts

    # --------------------------------------------------

    def _detect_amount_spikes(self, subsidy, disbursements):

        alerts = []

        avg = sum(float(d.amount) for d in disbursements) / len(disbursements)

        for d in disbursements:

            if float(d.amount) > avg * self.SPIKE_MULTIPLIER:

                alerts.append(
                    AnomalyAlert(
                        AnomalyType.SPIKE_DETECTION,
                        AnomalySeverity.MEDIUM,
                        f"Spike detected: {d.amount}",
                        subsidy.id,
                        {"average": avg}
                    )
                )

        return alerts

    # --------------------------------------------------

    def _detect_timing_anomalies(self, subsidy, disbursements):

        alerts = []

        for i in range(len(disbursements) - 1):

            d1 = disbursements[i]
            d2 = disbursements[i + 1]

            if not d1.date or not d2.date:
                continue

            if (d2.date - d1.date).days == 0:

                alerts.append(
                    AnomalyAlert(
                        AnomalyType.TIMING_ANOMALY,
                        AnomalySeverity.HIGH,
                        "Same day disbursements",
                        subsidy.id,
                        {"ids": [d1.id, d2.id]}
                    )
                )

        return alerts

    # --------------------------------------------------

    def _detect_rapid_succession(self, subsidy, disbursements):

        alerts = []

        sorted_d = sorted(disbursements, key=lambda d: d.date or datetime.min)

        for i in range(len(sorted_d) - 1):

            d1 = sorted_d[i]
            d2 = sorted_d[i + 1]

            if not d1.date or not d2.date:
                continue

            hours = (d2.date - d1.date).total_seconds() / 3600

            if hours <= self.RAPID_SUCCESSION_HOURS:

                alerts.append(
                    AnomalyAlert(
                        AnomalyType.RAPID_SUCCESSION,
                        AnomalySeverity.MEDIUM,
                        "Rapid disbursement sequence",
                        subsidy.id,
                        {"ids": [d1.id, d2.id]}
                    )
                )

        return alerts

    # --------------------------------------------------

    def _analyze_correlations(self, subsidy, disbursements):

        alerts = []

        late = any(d.is_late for d in disbursements)
        missing_proof = any(not d.proof_document_url for d in disbursements)

        if late and missing_proof:

            alerts.append(
                AnomalyAlert(
                    AnomalyType.CORRELATION_FLAG,
                    AnomalySeverity.HIGH,
                    "Late + missing proof correlation",
                    subsidy.id,
                    {}
                )
            )

        return alerts

    # --------------------------------------------------

    def _check_over_disbursement(self, subsidy, disbursements):

        alerts = []

        allocation = float(subsidy.total_allocation or 0)

        total = sum(float(d.amount) for d in disbursements)

        if allocation and total > allocation:

            alerts.append(
                AnomalyAlert(
                    AnomalyType.OVER_DISBURSEMENT,
                    AnomalySeverity.CRITICAL,
                    "Total disbursement exceeds allocation",
                    subsidy.id,
                    {"allocation": allocation, "total": total}
                )
            )

        return alerts

    # --------------------------------------------------

    def _detect_shell_entity(self, subsidy):

        alerts = []

        projects = self.db.query(Project).filter(
            Project.subsidy_id == subsidy.id
        ).count()

        if projects <= 1 and float(subsidy.total_allocation or 0) > 5_000_000:

            alerts.append(
                AnomalyAlert(
                    AnomalyType.SHELL_ENTITY,
                    AnomalySeverity.HIGH,
                    "High allocation with minimal projects",
                    subsidy.id,
                    {"project_count": projects}
                )
            )

        return alerts

    # --------------------------------------------------

    def _detect_duplicate_payment(self, subsidy, disbursements):

        alerts = []

        seen = {}

        for d in disbursements:

            key = (str(d.amount), d.date)

            if key in seen:

                alerts.append(
                    AnomalyAlert(
                        AnomalyType.DUPLICATE_PAYMENT,
                        AnomalySeverity.CRITICAL,
                        "Duplicate payment detected",
                        subsidy.id,
                        {"ids": [seen[key], d.id]}
                    )
                )

            else:
                seen[key] = d.id

        return alerts

    # --------------------------------------------------

    def _detect_high_risk_cluster(self, subsidy):

        alerts = []

        sector = subsidy.sector

        if not sector:
            return alerts

        others = self.db.query(Subsidy).filter(
            Subsidy.sector == sector,
            Subsidy.id != subsidy.id
        ).all()

        if len(others) < 3:
            return alerts

        avg = sum(float(s.risk_score or 0) for s in others) / len(others)

        if float(subsidy.risk_score or 0) > avg * 1.5:

            alerts.append(
                AnomalyAlert(
                    AnomalyType.HIGH_RISK_CLUSTER,
                    AnomalySeverity.HIGH,
                    "Sector risk cluster detected",
                    subsidy.id,
                    {"sector": sector}
                )
            )

        return alerts

    # --------------------------------------------------

    def _detect_velocity_anomaly(self, subsidy, disbursements):

        alerts = []

        if len(disbursements) < 3:
            return alerts

        sorted_d = sorted(disbursements, key=lambda d: d.date or datetime.min)

        first = sorted_d[0].date
        last = sorted_d[-1].date

        if not first or not last:
            return alerts

        total_days = (last - first).days

        if total_days < 30:
            return alerts

        cutoff = first + timedelta(days=int(total_days * 0.2))

        early = [d for d in sorted_d if d.date and d.date <= cutoff]

        if len(early) >= len(sorted_d) * 0.5:

            alerts.append(
                AnomalyAlert(
                    AnomalyType.VELOCITY_ANOMALY,
                    AnomalySeverity.MEDIUM,
                    "Unusual payment velocity",
                    subsidy.id,
                    {"early_count": len(early)}
                )
            )

        return alerts

    # --------------------------------------------------

    def _detect_seasonal_deviation(self, subsidy, disbursements):

        alerts = []

        months = {}

        for d in disbursements:
            if not d.date:
                continue

            m = d.date.month
            months.setdefault(m, []).append(float(d.amount))

        if not months:
            return alerts

        avg = sum(sum(v) / len(v) for v in months.values()) / len(months)

        for m, values in months.items():

            m_avg = sum(values) / len(values)

            if abs(m_avg - avg) / avg > 0.5:

                alerts.append(
                    AnomalyAlert(
                        AnomalyType.SEASONAL_DEVIATION,
                        AnomalySeverity.LOW,
                        "Seasonal deviation detected",
                        subsidy.id,
                        {"month": m}
                    )
                )

        return alerts

    # --------------------------------------------------

    def _detect_circular_fund_flow(self, subsidy):

        alerts = []

        recipient = subsidy.recipient

        if not recipient:
            return alerts

        linked_projects = self.db.query(Project).filter(
            Project.name.ilike(f"%{recipient}%")
        ).all()

        linked_subsidy_ids = list(
            set(p.subsidy_id for p in linked_projects if p.subsidy_id)
        )

        if len(linked_subsidy_ids) >= 2:

            alerts.append(
                AnomalyAlert(
                    AnomalyType.CIRCULAR_FUND_FLOW,
                    AnomalySeverity.CRITICAL,
                    f"Circular flow detected involving {recipient}",
                    subsidy.id,
                    {
                        "linked_projects": len(linked_projects),
                        "linked_subsidies": linked_subsidy_ids
                    }
                )
            )

        return alerts

    # --------------------------------------------------

    def get_alert_summary(self):

        alerts = self.analyze_all_subsidies()

        summary = {
            "total_alerts": len(alerts),
            "by_severity": {
                "critical": 0,
                "high": 0,
                "medium": 0,
                "low": 0
            },
            "recent_alerts": [a.to_dict() for a in alerts[:5]]
        }

        for a in alerts:
            summary["by_severity"][a.severity] += 1

        return summary


def get_anomaly_summary(db: Session):

    return AnomalyDetectionService(db).get_alert_summary()


def check_subsidy_anomalies(db: Session, subsidy_id: int):

    service = AnomalyDetectionService(db)

    return [a.to_dict() for a in service.analyze_subsidy(subsidy_id)]