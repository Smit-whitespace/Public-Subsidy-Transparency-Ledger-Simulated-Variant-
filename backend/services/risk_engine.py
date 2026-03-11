# backend/services/risk_engine.py

from decimal import Decimal
from sqlalchemy.orm import Session

from backend.models.subsidy import Subsidy
from backend.models.project import Project
from backend.models.disbursement import Disbursement
from backend.models.risk_event import RiskEvent
from backend.models.scoring_history import ScoringHistory


# ==========================================================
# CORE RISK CALCULATION ENGINE
# ==========================================================

def compute_risk_breakdown(db: Session, subsidy: Subsidy, explain: bool = False) -> dict:
    """
    Compute full risk breakdown for a subsidy.
    Returns risk_score, transparency_score, and component breakdown.
    
    Args:
        db: Database session
        subsidy: Subsidy model instance
        explain: If True, includes detailed reasoning factors
    """

    allocation = Decimal(subsidy.total_allocation or 0)

    disbursements = (
        db.query(Disbursement)
        .filter(Disbursement.subsidy_id == subsidy.id)
        .all()
    )

    total_disbursed = sum(
        (Decimal(d.amount) for d in disbursements),
        Decimal("0")
    )

    breakdown = {
        "over_utilization": Decimal("0"),
        "missing_proof": Decimal("0"),
        "late_ratio": Decimal("0"),
        "spike": Decimal("0"),
        "severity_events": Decimal("0"),
        "expired_penalty": Decimal("0"),
    }

    risk = Decimal("0")

    # ---------------------------------------------------------
    # 1️⃣ Over utilization
    # ---------------------------------------------------------
    if allocation > 0:
        utilization_ratio = total_disbursed / allocation

        if utilization_ratio > Decimal("1.25"):
            breakdown["over_utilization"] = Decimal("50")
        elif utilization_ratio > Decimal("1.10"):
            breakdown["over_utilization"] = Decimal("40")
        elif utilization_ratio > Decimal("1.00"):
            breakdown["over_utilization"] = Decimal("30")
        elif utilization_ratio > Decimal("0.90"):
            breakdown["over_utilization"] = Decimal("10")

    risk += breakdown["over_utilization"]

    # ---------------------------------------------------------
    # 2️⃣ Missing proof
    # ---------------------------------------------------------
    if disbursements:
        missing_count = sum(
            1 for d in disbursements if not d.proof_document_url
        )
        missing_ratio = Decimal(missing_count) / Decimal(len(disbursements))
    else:
        missing_ratio = Decimal("0")

    if missing_ratio > Decimal("0.30"):
        breakdown["missing_proof"] = Decimal("20")
    elif missing_ratio > Decimal("0.10"):
        breakdown["missing_proof"] = Decimal("12")

    risk += breakdown["missing_proof"]

    # ---------------------------------------------------------
    # 3️⃣ Late ratio
    # ---------------------------------------------------------
    if disbursements:
        late_count = sum(1 for d in disbursements if d.is_late)
        late_ratio = Decimal(late_count) / Decimal(len(disbursements))
    else:
        late_ratio = Decimal("0")

    if late_ratio > Decimal("0.30"):
        breakdown["late_ratio"] = Decimal("20")
    elif late_ratio > Decimal("0.10"):
        breakdown["late_ratio"] = Decimal("10")

    risk += breakdown["late_ratio"]

    # ---------------------------------------------------------
    # 4️⃣ Spike detection
    # ---------------------------------------------------------
    if disbursements:
        avg = total_disbursed / Decimal(len(disbursements))

        for d in disbursements:
            if avg > 0 and Decimal(d.amount) > avg * Decimal("2"):
                breakdown["spike"] = Decimal("12")
                break

    risk += breakdown["spike"]

    # ---------------------------------------------------------
    # 5️⃣ Risk events severity
    # ---------------------------------------------------------
    events = (
        db.query(RiskEvent)
        .filter(RiskEvent.subsidy_id == subsidy.id)
        .all()
    )

    severity_total = Decimal("0")

    for e in events:
        if e.severity == "high":
            severity_total += Decimal("20")
        elif e.severity == "medium":
            severity_total += Decimal("10")
        elif e.severity == "low":
            severity_total += Decimal("4")

    severity_total = min(severity_total, Decimal("30"))
    breakdown["severity_events"] = severity_total

    risk += severity_total

    # ---------------------------------------------------------
    # 6️⃣ Expired incomplete penalty
    # ---------------------------------------------------------
    if subsidy.status == "expired" and allocation > 0:
        completion_ratio = total_disbursed / allocation
        if completion_ratio < Decimal("0.50"):
            breakdown["expired_penalty"] = Decimal("12")

    risk += breakdown["expired_penalty"]

    final_risk = min(risk.quantize(Decimal("0.01")), Decimal("100"))
    transparency = max(Decimal("0"), Decimal("100") - final_risk)

    # Build explanation factors if requested
    reasoning = []
    if breakdown["over_utilization"] > 0:
        utilization = float(total_disbursed / allocation * 100) if allocation > 0 else 0
        reasoning.append(f"Over-disbursement: {utilization:.0f}% of allocation")
    
    if breakdown["missing_proof"] > 0:
        reasoning.append(f"Missing proof documents: {missing_count} disbursements")
    
    if breakdown["late_ratio"] > 0:
        reasoning.append(f"Late payments: {late_count} of {len(disbursements)} disbursements")
    
    if breakdown["spike"] > 0:
        reasoning.append("Unusual spike in payment amounts detected")
    
    if breakdown["severity_events"] > 0:
        reasoning.append(f"Risk events logged: {len(events)} events")
    
    if breakdown["expired_penalty"] > 0:
        completion = float(total_disbursed / allocation * 100) if allocation > 0 else 0
        reasoning.append(f"Expired with low completion: {completion:.0f}%")
    
    if not reasoning:
        reasoning.append("No risk factors identified")

    result = {
        "risk_score": final_risk,
        "transparency_score": transparency,
        "breakdown": breakdown,
    }
    
    # Add explainability if requested
    if explain:
        result["reasoning"] = reasoning
        result["factors"] = {
            "total_allocation": float(allocation),
            "total_disbursed": float(total_disbursed),
            "disbursement_count": len(disbursements),
            "project_count": db.query(Project).filter(Project.subsidy_id == subsidy.id).count(),
            "risk_event_count": len(events),
            "is_expired": subsidy.status == "expired",
            "is_flagged": subsidy.is_flagged,
        }
    
    return result


# ==========================================================
# SINGLE SUBSIDY RECALCULATION (NO COMMIT)
# ==========================================================

def recalculate_subsidy_score(db: Session, subsidy_id: int):
    """
    Recalculate risk & transparency for a single subsidy.
    DOES NOT COMMIT.
    Calling service is responsible for commit().
    """

    subsidy = (
        db.query(Subsidy)
        .filter(Subsidy.id == subsidy_id)
        .first()
    )

    if not subsidy:
        return

    result = compute_risk_breakdown(db, subsidy)

    risk_score = result["risk_score"]
    transparency_score = result["transparency_score"]

    subsidy.risk_score = risk_score
    subsidy.transparency_score = transparency_score
    subsidy.is_flagged = risk_score >= 70

    db.add(
        ScoringHistory(
            subsidy_id=subsidy.id,
            risk_score=risk_score,
            transparency_score=transparency_score
        )
    )


# ==========================================================
# FULL SYSTEM RECALCULATION
# ==========================================================

def recalculate_all_scores(db: Session):
    """
    Batch recalculation for all subsidies.
    Does single commit at end.
    """

    subsidies = db.query(Subsidy).all()

    for subsidy in subsidies:
        result = compute_risk_breakdown(db, subsidy)

        risk_score = result["risk_score"]
        transparency_score = result["transparency_score"]

        subsidy.risk_score = risk_score
        subsidy.transparency_score = transparency_score
        subsidy.is_flagged = risk_score >= 70

        db.add(
            ScoringHistory(
                subsidy_id=subsidy.id,
                risk_score=risk_score,
                transparency_score=transparency_score
            )
        )

    db.commit()