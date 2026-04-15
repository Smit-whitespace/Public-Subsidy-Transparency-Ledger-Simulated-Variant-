# backend/seed/scenarios.py

import random
from datetime import datetime, timedelta
from decimal import Decimal

from sqlalchemy.orm import Session

from backend.models.subsidy import Subsidy
from backend.models.disbursement import Disbursement
from backend.models.risk_event import RiskEvent
from backend.seed.factories import create_disbursement, create_risk_event, create_scoring_history


def apply_scenarios(db: Session, subsidy: Subsidy):
    allocation = subsidy.total_allocation
    start_date = subsidy.start_date or datetime.utcnow()
    
    # More weighted scenario selection for variety
    scenario_weights = {
        "healthy": 40,
        "slightly_delayed": 20,
        "missing_proof": 15,
        "over_disbursed": 8,
        "spike": 7,
        "expired": 5,
        "corrupted": 5,
    }
    
    # Weighted random selection
    scenarios = list(scenario_weights.keys())
    weights = list(scenario_weights.values())
    scenario = random.choices(scenarios, weights=weights, k=1)[0]

    disbursed_total = Decimal("0")
    
    # Track dates for realistic timing
    current_date = start_date
    
    if scenario == "healthy":
        # 3-4 healthy disbursements spread over time
        num_disbursements = random.randint(3, 4)
        for i in range(num_disbursements):
            amount = allocation / Decimal(num_disbursements + 1)
            d = create_disbursement(subsidy.id, amount)
            d.date = current_date + timedelta(days=random.randint(30, 90))
            disbursed_total += amount
            db.add(d)

        subsidy.risk_score = Decimal(str(random.uniform(5, 20)))
        subsidy.transparency_score = Decimal(str(random.uniform(85, 98)))

    elif scenario == "slightly_delayed":
        # Normal with some late payments
        num_disbursements = random.randint(2, 3)
        for i in range(num_disbursements):
            amount = allocation / Decimal(num_disbursements + 1)
            d = create_disbursement(subsidy.id, amount)
            d.date = current_date + timedelta(days=random.randint(45, 120))
            if i == num_disbursements - 1:
                d.is_late = True
                db.add(create_risk_event(subsidy.id, "LateDisbursement", "low"))
            disbursed_total += amount
            db.add(d)

        subsidy.risk_score = Decimal(str(random.uniform(25, 45)))
        subsidy.transparency_score = Decimal(str(random.uniform(70, 85)))

    elif scenario == "over_disbursed":
        # Significant over-disbursement (potential fraud indicator)
        for _ in range(3):
            amount = allocation / 2
            d = create_disbursement(subsidy.id, amount)
            d.date = current_date + timedelta(days=random.randint(20, 60))
            disbursed_total += amount
            db.add(d)

        db.add(create_risk_event(subsidy.id, "OverDisbursement", "high"))
        subsidy.risk_score = Decimal(str(random.uniform(80, 95)))
        subsidy.transparency_score = Decimal(str(random.uniform(25, 45)))
        subsidy.is_flagged = True

    elif scenario == "spike":
        # Normal small payments followed by one large spike
        for _ in range(2):
            amount = allocation / 10
            d = create_disbursement(subsidy.id, amount)
            d.date = current_date + timedelta(days=random.randint(30, 60))
            disbursed_total += amount
            db.add(d)

        spike_amount = allocation * Decimal("0.8")
        d = create_disbursement(subsidy.id, spike_amount)
        d.date = current_date + timedelta(days=random.randint(90, 150))
        disbursed_total += spike_amount
        db.add(d)

        db.add(create_risk_event(subsidy.id, "DisbursementSpike", "medium"))
        subsidy.risk_score = Decimal(str(random.uniform(60, 80)))
        subsidy.transparency_score = Decimal(str(random.uniform(50, 70)))

    elif scenario == "missing_proof":
        # Missing proof documents for some disbursements
        num_disbursements = random.randint(2, 3)
        for i in range(num_disbursements):
            amount = allocation / Decimal(num_disbursements + 1)
            d = create_disbursement(subsidy.id, amount)
            d.date = current_date + timedelta(days=random.randint(30, 90))
            if i == num_disbursements - 1:
                d.proof_document_url = None
                db.add(create_risk_event(subsidy.id, "MissingProof", "medium"))
            disbursed_total += amount
            db.add(d)

        subsidy.risk_score = Decimal(str(random.uniform(50, 70)))
        subsidy.transparency_score = Decimal(str(random.uniform(45, 65)))

    elif scenario == "expired":
        # Expired with incomplete utilization
        subsidy.status = "expired"
        # Only partially disbursed
        partial = Decimal(str(random.uniform(0.3, 0.7)))
        amount = allocation * partial
        d = create_disbursement(subsidy.id, amount)
        d.date = start_date + timedelta(days=random.randint(60, 180))
        disbursed_total += amount
        db.add(d)
        
        if partial < 0.5:
            db.add(create_risk_event(subsidy.id, "LowUtilization", "medium"))
            subsidy.risk_score = Decimal(str(random.uniform(45, 65)))
        else:
            subsidy.risk_score = Decimal(str(random.uniform(15, 35)))
        
        subsidy.transparency_score = Decimal(str(random.uniform(65, 85)))

    elif scenario == "corrupted":
        # Multiple red flags - likely corruption
        for _ in range(3):
            amount = allocation * Decimal("0.6")
            d = create_disbursement(subsidy.id, amount)
            d.date = current_date + timedelta(days=random.randint(15, 45))
            d.is_late = True
            d.proof_document_url = None
            disbursed_total += amount
            db.add(d)

        db.add(create_risk_event(subsidy.id, "OverDisbursement", "high"))
        db.add(create_risk_event(subsidy.id, "MissingProof", "high"))
        db.add(create_risk_event(subsidy.id, "LateDisbursement", "high"))

        subsidy.status = "expired"
        subsidy.is_flagged = True
        subsidy.risk_score = Decimal(str(random.uniform(85, 99)))
        subsidy.transparency_score = Decimal(str(random.uniform(10, 30)))

    # Add scoring history for trend tracking
    db.add(create_scoring_history(subsidy.id, subsidy.risk_score, subsidy.transparency_score))