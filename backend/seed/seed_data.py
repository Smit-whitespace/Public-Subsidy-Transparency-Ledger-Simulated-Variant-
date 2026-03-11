# backend/seed/seed_data.py

import random

from sqlalchemy.orm import Session

from backend.database.connection import SessionLocal, engine, Base
from backend.models import *
from backend.seed.factories import create_subsidy
from backend.seed.scenarios import apply_scenarios
from backend.services.risk_engine import recalculate_all_scores
from backend.config import settings


PROJECT_NAMES = [
    "Rural Electrification Phase 1",
    "District Hospital Upgrade",
    "Primary School Construction",
    "Water Supply Scheme",
    "Village Road Connectivity",
    "Skill Development Center",
    "Solar Panel Installation",
    "MSME Cluster Development",
    "Cold Storage Facility",
    "Digital Library Initiative",
    "Anganwadi Center Construction",
    "Farm Pond Construction",
    "Bio-gas Plant Setup",
    "Teacher Training Program",
    "Medical Equipment Procurement",
]


def create_project_for_subsidy(subsidy, index):
    """Create a project linked to a subsidy."""
    from datetime import timedelta
    
    owners = [
        "District Administration",
        "State Government",
        "Panchayat Council",
        "NGO Partner",
        "Government Department"
    ]
    
    statuses = ["planned", "active", "completed"]
    
    start_offset = random.randint(30, 180)
    duration = random.randint(180, 540)
    
    return Project(
        name=f"{PROJECT_NAMES[index % len(PROJECT_NAMES)]} - {subsidy.sector}",
        subsidy_id=subsidy.id,
        description=f"Implementation project for {subsidy.title}. Target beneficiaries in designated areas.",
        owner=random.choice(owners),
        status=random.choice(statuses),
        start_date=subsidy.start_date + timedelta(days=start_offset) if subsidy.start_date else None,
        end_date=subsidy.start_date + timedelta(days=start_offset + duration) if subsidy.start_date else None
    )


def seed():
    if settings.ENVIRONMENT != "development":
        raise RuntimeError("Seeding allowed only in development.")

    random.seed(42)

    db: Session = SessionLocal()

    try:
        # Optional reset
        Base.metadata.drop_all(bind=engine)
        Base.metadata.create_all(bind=engine)

        subsidies = []

        # Create subsidies with scenarios
        for i in range(35):
            subsidy = create_subsidy(i)
            db.add(subsidy)
            db.flush()
            apply_scenarios(db, subsidy)
            subsidies.append(subsidy)

        db.commit()
        
        # Create projects linked to subsidies
        for i, subsidy in enumerate(subsidies):
            # 60% of subsidies have projects
            if random.random() < 0.6:
                num_projects = random.randint(1, 3)
                for j in range(num_projects):
                    project = create_project_for_subsidy(subsidy, i * 10 + j)
                    db.add(project)
        
        db.commit()
        recalculate_all_scores(db)
        print("Seed data generated successfully with projects.")

    finally:
        db.close()


if __name__ == "__main__":
    seed()