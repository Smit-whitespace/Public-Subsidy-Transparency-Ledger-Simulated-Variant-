# backend/demo/demo_mode.py

"""
Demo Mode System - Automatic seed data for demonstrations.
Automatically populates the database with realistic demo data when empty.
Includes specialized investigation data for fraud network visualization.
"""

import random
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Dict, List, Any, Set, Tuple

from sqlalchemy.orm import Session
from sqlalchemy import func

from backend.database.connection import SessionLocal
from backend.models import Subsidy, Project, Disbursement, RiskEvent
from backend.models.subsidy import SubsidyStatus
from backend.seed.factories import create_subsidy, SECTORS, RECIPIENTS
from backend.seed.scenarios import apply_scenarios
from backend.services.risk_engine import recalculate_all_scores


# Demo-specific fraud scenarios
FRAUD_SCENARIOS = [
    {
        "name": "Shell Company Ring",
        "description": "Multiple entities at same address receiving funds",
        "recipients": ["Apex Holdings Ltd", "Peak Ventures Pvt Ltd", "Summit Enterprises"],
        "sector": "Infrastructure",
        "risk_score": 92,
        "flag": True,
        "pattern": "shell_entity"
    },
    {
        "name": "Duplicate Disbursement",
        "description": "Same amount paid twice to same recipient",
        "recipients": ["Rural Development Authority"],
        "sector": "Agriculture",
        "risk_score": 85,
        "flag": True,
        "pattern": "duplicate_payment"
    },
    {
        "name": "Unusual Spike",
        "description": "Large disbursement outside normal pattern",
        "recipients": ["District Administration"],
        "sector": "Healthcare",
        "risk_score": 78,
        "flag": True,
        "pattern": "rapid_disbursement"
    },
    {
        "name": "Multiple Subsidy Recipient",
        "description": "Same recipient receives subsidies from multiple programs",
        "recipients": ["State Government Department"],
        "sector": "MSME",
        "risk_score": 88,
        "flag": True,
        "pattern": "multiple_subsidy_recipient"
    },
    {
        "name": "High Risk Cluster",
        "description": "Cluster of subsidies within one sector with high risk",
        "recipients": ["District Administration"],
        "sector": "Infrastructure",
        "risk_score": 90,
        "flag": True,
        "pattern": "high_risk_cluster"
    }
]

# Suspicious recipients for fraud network (shell entities)
SHELL_ENTITIES = [
    "Apex Holdings Ltd",
    "Peak Ventures Pvt Ltd", 
    "Summit Enterprises",
    "Global Connect Services",
    "Unity Infrastructure Pvt Ltd",
    "Priority Projects Ltd",
    "Elite Development Corp",
    "Prime Ventures Group",
]

# Circular fund flow contractors
CONTRACTORS = [
    "Quick Build Contractors",
    "Fast Track Engineers",
    "Speedy Construction Co",
    "Rapid Infra Solutions",
    "Swift Projects Ltd",
]


def check_database_empty(db: Session) -> bool:
    """Check if database has any subsidies."""
    count = db.query(func.count(Subsidy.id)).scalar()
    return count == 0 or count is None


def create_demo_subsidies(db: Session, count: int = 200) -> List[Subsidy]:
    """Create demo subsidies with varied scenarios."""
    random.seed(42)
    subsidies = []
    
    for i in range(count):
        subsidy = create_subsidy(i)
        db.add(subsidy)
        db.flush()
        apply_scenarios(db, subsidy)
        subsidies.append(subsidy)
    
    db.commit()
    return subsidies


def create_fraud_network_data(db: Session, subsidies: List[Subsidy]):
    """Create suspicious relationships for fraud network visualization."""
    
    # Find high-risk subsidies
    high_risk = db.query(Subsidy).filter(
        Subsidy.risk_score > 70
    ).limit(30).all()
    
    # Create risk events for fraud network
    for scenario in FRAUD_SCENARIOS:
        # Find or create a subsidy for this scenario
        sector_subsidies = [s for s in subsidies if s.sector == scenario["sector"]]
        if sector_subsidies:
            subsidy = random.choice(sector_subsidies)
            
            # Add risk events
            risk_event = RiskEvent(
                subsidy_id=subsidy.id,
                event_type=scenario["name"],
                severity="high" if scenario["flag"] else "medium",
                description=scenario["description"],
                detected_at=datetime.utcnow() - timedelta(days=random.randint(1, 90))
            )
            db.add(risk_event)
            
            # Flag the subsidy
            subsidy.is_flagged = True
    
    db.commit()


def create_investigation_relationships(db: Session):
    """Create links between entities for fraud network graph."""
    
    # Get entities for graph visualization
    # This creates the relationships needed for the fraud network visualization
    
    # Link multiple subsidies to same recipients (suspicious pattern)
    recipients_with_multiple = db.query(
        Subsidy.recipient,
        func.count(Subsidy.id).label('count')
    ).group_by(
        Subsidy.recipient
    ).having(
        func.count(Subsidy.id) > 1
    ).limit(10).all()
    
    # Create suspicious disbursement links
    suspicious = db.query(Subsidy).filter(
        Subsidy.risk_score > 60
    ).limit(20).all()
    
    for sub in suspicious:
        # Mark as suspicious for fraud network
        pass
    
    db.commit()


def seed_demo_data(db: Session) -> Dict[str, Any]:
    """Main function to seed all demo data."""
    
    if not check_database_empty(db):
        # Database already has data
        return {
            "status": "skipped",
            "message": "Database already contains data",
            "seeded": False
        }
    
    print("Seeding demo data...")
    
    # Create subsidies with scenarios
    subsidies = create_demo_subsidies(db, 200)
    print(f"Created {len(subsidies)} subsidies")
    
    # Create projects linked to subsidies
    project_count = 0
    for subsidy in subsidies:
        if random.random() < 0.6:
            num_projects = random.randint(1, 3)
            for j in range(num_projects):
                project = Project(
                    name=f"Project for {subsidy.title[:30]}",
                    subsidy_id=subsidy.id,
                    description=f"Implementation project for {subsidy.sector}",
                    owner=random.choice([
                        "District Administration",
                        "State Government",
                        "NGO Partner"
                    ]),
                    status=random.choice(["planned", "active", "completed"]),
                    start_date=subsidy.start_date + timedelta(days=30) if subsidy.start_date else None,
                    end_date=subsidy.start_date + timedelta(days=300) if subsidy.start_date else None
                )
                db.add(project)
                project_count += 1
    
    db.commit()
    print(f"Created {project_count} projects")
    
    # Create fraud network data
    create_fraud_network_data(db, subsidies)
    print("Created fraud network relationships")
    
    # Recalculate all risk scores
    recalculate_all_scores(db)
    print("Risk scores calculated")
    
    # Get final stats
    stats = {
        "subsidies": db.query(Subsidy).count(),
        "projects": db.query(Project).count(),
        "disbursements": db.query(Disbursement).count(),
        "risk_events": db.query(RiskEvent).count(),
        "flagged": db.query(Subsidy).filter(Subsidy.is_flagged == True).count()
    }
    
    return {
        "status": "success",
        "message": "Demo data seeded successfully",
        "seeded": True,
        "stats": stats
    }


def ensure_demo_data():
    """Ensure demo data exists - call this on startup."""
    db = SessionLocal()
    try:
        result = seed_demo_data(db)
        return result
    finally:
        db.close()


if __name__ == "__main__":
    result = ensure_demo_data()
    print(f"\nResult: {result}")