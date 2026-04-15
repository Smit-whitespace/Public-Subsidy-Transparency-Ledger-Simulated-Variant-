# backend/seed/factories.py

import random
from datetime import datetime, timedelta
from decimal import Decimal

from backend.models.subsidy import Subsidy, SubsidyStatus
from backend.models.disbursement import Disbursement
from backend.models.risk_event import RiskEvent
from backend.models.scoring_history import ScoringHistory


SECTORS = [
    "Agriculture",
    "Education",
    "Healthcare",
    "Infrastructure",
    "MSME",
    "Renewable Energy",
    "Social Welfare",
]

RECIPIENTS = [
    "Rural Development Authority",
    "State Government Department",
    "District Administration",
    "National Skills Development Corp",
    "Primary Healthcare Initiative",
    "Gram Panchayat Council",
    "Urban Municipal Corporation",
    "Women & Child Welfare Dept",
    "Agricultural Cooperative Society",
    "Small Industries Development Bank",
    "Renewable Energy Consortium",
    "Public Works Department",
    "Education Reform Foundation",
    "MSME Promotion Council",
    "Social Security Board",
]

SUBSIDY_TITLES = {
    "Agriculture": [
        "Kisan Samman Yojana",
        "PM-KISAN Support",
        "Fertilizer Subsidy Program",
        "Irrigation Development Scheme",
        "Crop Insurance Initiative",
        "Farm Mechanization Grant",
    ],
    "Education": [
        "National Education Scholarship",
        "Free Textbooks Program",
        "Digital Learning Initiative",
        "Teacher Training Grant",
        "School Infrastructure Development",
        "Student Hostel Construction",
    ],
    "Healthcare": [
        "Ayushman Bharat Scheme",
        "Vaccination Program Fund",
        "Primary Health Center Upgrade",
        "Medical Equipment Grant",
        "Health Worker Training",
        "Emergency Ambulance Service",
    ],
    "Infrastructure": [
        "Rural Road Connectivity",
        "Bridge Construction Project",
        "Water Supply Scheme",
        "Street Light Installation",
        "Public Transport Enhancement",
        "Railway Station Modernization",
    ],
    "MSME": [
        "Startup Innovation Fund",
        "Skill Development Loan",
        "Technology Upgradation Grant",
        "Market Development Support",
        "Export Promotion Scheme",
        "Working Capital Assistance",
    ],
    "Renewable Energy": [
        "Solar Power Installation",
        "Wind Energy Project",
        "Biomass Energy Initiative",
        "Green Building Subsidy",
        "Electric Vehicle Promotion",
        "Energy Efficiency Grant",
    ],
    "Social Welfare": [
        "Old Age Pension Scheme",
        "Widow Support Program",
        "Disability Assistance Fund",
        "Housing for All Initiative",
        "Food Security Scheme",
        "Child Nutrition Program",
    ],
}


def random_date_within(days_back: int = 365):
    return datetime.utcnow() - timedelta(days=random.randint(0, days_back))


def create_subsidy(index: int) -> Subsidy:
    sector = random.choice(SECTORS)
    
    # More realistic allocation amounts based on sector
    sector_multipliers = {
        "Infrastructure": (5_000_000, 50_000_000),
        "Healthcare": (2_000_000, 25_000_000),
        "Education": (1_000_000, 15_000_000),
        "Renewable Energy": (3_000_000, 30_000_000),
        "MSME": (500_000, 10_000_000),
        "Agriculture": (200_000, 5_000_000),
        "Social Welfare": (100_000, 3_000_000),
    }
    min_alloc, max_alloc = sector_multipliers.get(sector, (100_000, 5_000_000))
    allocation = Decimal(random.randint(min_alloc, max_alloc))
    
    # More varied and realistic titles
    title_base = random.choice(SUBSIDY_TITLES.get(sector, [f"{sector} Program"]))
    title = f"{title_base} {2020 + (index % 5)}"
    
    recipient = random.choice(RECIPIENTS)

    return Subsidy(
        title=title,
        recipient=recipient,
        sector=sector,
        total_allocation=allocation,
        currency="INR",
        description=f"Government funded initiative for {sector.lower()} development in target areas.",
        status=SubsidyStatus.active,
        start_date=random_date_within(700),
        end_date=random_date_within(100),
    )


def create_disbursement(subsidy_id: int, amount: Decimal) -> Disbursement:
    return Disbursement(
        subsidy_id=subsidy_id,
        amount=amount,
        currency="INR",
        approval_status="approved",
        reference=f"TXN-{random.randint(100000,999999)}",
        proof_document_url="https://proof.local/doc.pdf",
    )


def create_risk_event(subsidy_id: int, event_type: str, severity: str):
    return RiskEvent(
        subsidy_id=subsidy_id,
        event_type=event_type,
        severity=severity,
        description=f"{event_type} detected with severity {severity}",
    )


def create_scoring_history(subsidy_id: int, risk: Decimal, transparency: Decimal):
    return ScoringHistory(
        subsidy_id=subsidy_id,
        risk_score=risk,
        transparency_score=transparency,
    )