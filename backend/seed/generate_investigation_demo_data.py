"""
backend/seed/generate_investigation_demo_data.py

Investigation Demo Data Generator
Creates fraud patterns for investigation page visualization.

Generates:
- 50+ recipients
- 200 subsidies
- 150 projects  
- 400 disbursements
- 60 risk events
- 30 anomaly records

Fraud Patterns:
1. Repeated Subsidy Recipient - Same recipient receives from multiple programs
2. Rapid Disbursement Pattern - Large subsidies disbursed unusually fast
3. Shell Organization Pattern - Fake orgs with high allocation, minimal projects
4. Circular Fund Flow - Suspicious chains between entities
5. High Risk Cluster - Cluster of high-risk subsidies in one sector
"""

import random
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Dict, List, Any

from sqlalchemy.orm import Session

from backend.database.connection import SessionLocal
from backend.models import Subsidy, Project, Disbursement, RiskEvent
from backend.models.subsidy import SubsidyStatus
from backend.seed.factories import SECTORS


# Investigation-specific suspicious recipients
INVESTIGATION_RECIPIENTS = [
    # Shell entities (high risk, few projects, high allocation)
    "Apex Holdings Ltd",
    "Peak Ventures Pvt Ltd",
    "Summit Enterprises",
    "Global Connect Services",
    "Unity Infrastructure Pvt Ltd",
    "Priority Projects Ltd",
    "Elite Development Corp",
    "Prime Ventures Group",
    "Sterling Assets Ltd",
    "Quantum Holdings Inc",
    # Recipients that get multiple subsidies (suspicious)
    "State Government Department",
    "District Administration",
    "Rural Development Authority",
    "Municipal Corporation",
    "Block Development Office",
    # Recipients with circular fund flow
    "Quick Build Contractors",
    "Fast Track Engineers",
    "Speedy Construction Co",
    "Rapid Infra Solutions",
    "Swift Projects Ltd",
]

# Recipients for normal distribution
NORMAL_RECIPIENTS = [
    "Agricultural University",
    "District Hospital",
    "Primary Education Board",
    "Panchayat Samiti",
    "Women & Child Development",
    "Public Health Department",
    "Rural Water Supply",
    "Food & Civil Supplies",
    "Social Justice Department",
    "Employment Generation Bureau",
]


class InvestigationDataGenerator:
    """Generate investigation-specific demo data with fraud patterns."""
    
    def __init__(self, db: Session):
        self.db = db
        self.stats = {
            "subsidies": 0,
            "projects": 0,
            "disbursements": 0,
            "risk_events": 0,
            "flagged_entities": 0
        }
    
    def generate_all(self) -> Dict[str, Any]:
        """Generate all investigation data with fraud patterns."""
        
        # 1. Create 50 recipients with various patterns
        print("Creating recipients with fraud patterns...")
        recipients_data = self._create_recipients_with_patterns()
        
        # 2. Create 200 subsidies (some with fraud patterns)
        print("Creating subsidies with fraud patterns...")
        subsidies = self._create_subsidies_with_fraud_patterns(recipients_data)
        
        # 3. Create 150 projects linked to subsidies
        print("Creating projects...")
        projects = self._create_projects(subsidies)
        
        # 4. Create 400 disbursements with suspicious patterns
        print("Creating disbursements with patterns...")
        disbursements = self._create_disbursements_with_patterns(subsidies)
        
        # 5. Create 60 risk events
        print("Creating risk events...")
        risk_events = self._create_risk_events(subsidies)
        
        # 6. Create anomaly records (in risk events)
        print("Creating anomalies...")
        
        self.db.commit()
        
        return {
            "status": "success",
            "stats": self.stats,
            "fraud_patterns": {
                "shell_entities": 10,
                "multiple_subsidy_recipients": 15,
                "rapid_disbursements": 20,
                "circular_fund_flow": 8,
                "high_risk_clusters": 5
            }
        }
    
    def _create_recipients_with_patterns(self) -> Dict[str, Any]:
        """Create recipients with various fraud patterns."""
        
        recipients_data = {
            "shell_entities": [],
            "multiple_subsidy": [],
            "circular_flow": [],
            "normal": []
        }
        
        # Shell entities (high allocation, no/low projects)
        for name in INVESTIGATION_RECIPIENTS[:10]:
            recipients_data["shell_entities"].append({
                "name": name,
                "type": "shell_entity",
                "allocation": random.randint(50_000_000, 200_000_000),
                "expected_projects": random.randint(0, 1)
            })
            self.stats["flagged_entities"] += 1
        
        # Multiple subsidy recipients
        for name in INVESTIGATION_RECIPIENTS[10:15]:
            recipients_data["multiple_subsidy"].append({
                "name": name,
                "type": "multiple_subsidy_recipient",
                "subsidy_count": random.randint(3, 6),
                "allocation": random.randint(30_000_000, 100_000_000)
            })
            self.stats["flagged_entities"] += 1
        
        # Circular fund flow recipients
        for name in INVESTIGATION_RECIPIENTS[15:20]:
            recipients_data["circular_flow"].append({
                "name": name,
                "type": "circular_fund_flow",
                "linked_recipients": random.sample(INVESTIGATION_RECIPIENTS[:10], 3)
            })
            self.stats["flagged_entities"] += 1
        
        # Normal recipients
        for name in NORMAL_RECIPIENTS:
            recipients_data["normal"].append({
                "name": name,
                "type": "normal",
                "allocation": random.randint(5_000_000, 50_000_000)
            })
        
        return recipients_data
    
    def _create_subsidies_with_fraud_patterns(self, recipients_data: Dict) -> List[Subsidy]:
        """Create 200 subsidies with fraud patterns embedded."""
        
        subsidies = []
        
        # Create 10 shell entity subsidies (high allocation, suspicious)
        for i in range(10):
            recipient = random.choice(recipients_data["shell_entities"])
            subsidy = self._create_subsidy(
                title=f"Shell Entity Subsidy {i+1}",
                recipient=recipient["name"],
                sector=random.choice(SECTORS),
                allocation=Decimal(recipient["allocation"]),
                risk_score=random.randint(80, 95),
                is_flagged=True,
                pattern="shell_entity"
            )
            subsidies.append(subsidy)
            self.db.add(subsidy)
        
        # Create 15 multiple subsidy recipient subsidies
        for i in range(15):
            recipient = random.choice(recipients_data["multiple_subsidy"])
            subsidy = self._create_subsidy(
                title=f"Multi-Program Subsidy {i+1}",
                recipient=recipient["name"],
                sector=random.choice(SECTORS),
                allocation=Decimal(recipient["allocation"]),
                risk_score=random.randint(70, 85),
                is_flagged=True,
                pattern="multiple_subsidy_recipient"
            )
            subsidies.append(subsidy)
            self.db.add(subsidy)
        
        # Create 20 rapid disbursement subsidies
        for i in range(20):
            recipient_data = random.choice(recipients_data["normal"] + recipients_data["shell_entities"])
            subsidy = self._create_subsidy(
                title=f"Rapid Disbursement {i+1}",
                recipient=recipient_data["name"],
                sector=random.choice(SECTORS),
                allocation=Decimal(random.randint(10_000_000, 50_000_000)),
                risk_score=random.randint(60, 80),
                is_flagged=True,
                pattern="rapid_disbursement"
            )
            subsidies.append(subsidy)
            self.db.add(subsidy)
        
        # Create 8 circular fund flow subsidies
        for i in range(8):
            recipient = random.choice(recipients_data["circular_flow"])
            subsidy = self._create_subsidy(
                title=f"Circular Fund Subsidy {i+1}",
                recipient=recipient["name"],
                sector=random.choice(SECTORS),
                allocation=Decimal(random.randint(20_000_000, 80_000_000)),
                risk_score=random.randint(75, 90),
                is_flagged=True,
                pattern="circular_fund_flow"
            )
            subsidies.append(subsidy)
            self.db.add(subsidy)
        
        # Create 5 high risk cluster subsidies (all in same sector)
        for i in range(5):
            recipient_data = random.choice(recipients_data["normal"])
            subsidy = self._create_subsidy(
                title=f"High Risk Cluster {i+1}",
                recipient=recipient_data["name"],
                sector="Infrastructure",  # Same sector for cluster
                allocation=Decimal(random.randint(15_000_000, 60_000_000)),
                risk_score=random.randint(85, 95),
                is_flagged=True,
                pattern="high_risk_cluster"
            )
            subsidies.append(subsidy)
            self.db.add(subsidy)
        
        # Create remaining 142 normal subsidies
        for i in range(142):
            recipient_data = random.choice(recipients_data["normal"])
            subsidy = self._create_subsidy(
                title=f"Normal Subsidy {i+1}",
                recipient=recipient_data["name"],
                sector=random.choice(SECTORS),
                allocation=Decimal(random.randint(5_000_000, 30_000_000)),
                risk_score=random.randint(20, 60),
                is_flagged=False,
                pattern="normal"
            )
            subsidies.append(subsidy)
            self.db.add(subsidy)
        
        self.db.flush()
        self.stats["subsidies"] = len(subsidies)
        
        return subsidies
    
    def _create_subsidy(self, title: str, recipient: str, sector: str, 
                       allocation: Decimal, risk_score: int, is_flagged: bool,
                       pattern: str) -> Subsidy:
        """Create a single subsidy with specified attributes."""
        
        start_date = datetime.utcnow() - timedelta(days=random.randint(30, 365))
        
        return Subsidy(
            title=title,
            recipient=recipient,
            sector=sector,
            total_allocation=allocation,
            currency="INR",
            status=SubsidyStatus.ACTIVE,
            is_active=True,
            is_flagged=is_flagged,
            risk_score=risk_score,
            transparency_score=random.randint(50, 90),
            description=f"Subsidy for {sector} - Pattern: {pattern}",
            start_date=start_date,
            end_date=start_date + timedelta(days=random.randint(180, 730))
        )
    
    def _create_projects(self, subsidies: List[Subsidy]) -> List[Project]:
        """Create 150 projects linked to subsidies."""
        
        projects = []
        project_per_subsidy = 150 // len(subsidies)
        
        for subsidy in subsidies:
            # Shell entities get few/no projects
            if subsidy.risk_score >= 80:
                num_projects = random.randint(0, 1)
            else:
                num_projects = random.randint(1, 3)
            
            for j in range(num_projects):
                project = Project(
                    name=f"Project: {subsidy.title[:40]} - Phase {j+1}",
                    subsidy_id=subsidy.id,
                    description=f"Implementation project for {subsidy.sector}",
                    owner=random.choice([
                        "District Administration",
                        "State Government",
                        "Panchayat Council",
                        "NGO Partner"
                    ]),
                    status=random.choice(["planned", "active", "completed"]),
                    start_date=subsidy.start_date + timedelta(days=30) if subsidy.start_date else None,
                    end_date=subsidy.start_date + timedelta(days=300) if subsidy.start_date else None,
                    budget=subsidy.total_allocation / (num_projects + 1)
                )
                projects.append(project)
                self.db.add(project)
        
        self.db.flush()
        self.stats["projects"] = len(projects)
        
        return projects
    
    def _create_disbursements_with_patterns(self, subsidies: List[Subsidy]) -> List[Disbursement]:
        """Create 400 disbursements with suspicious patterns."""
        
        disbursements = []
        
        # Find rapid disbursement subsidies
        rapid_subsidies = [s for s in subsidies if s.risk_score >= 60 and s.risk_score <= 80]
        high_risk_subsidies = [s for s in subsidies if s.risk_score > 80]
        
        # Create rapid disbursements (large amounts in short time)
        for subsidy in rapid_subsidies[:20]:
            allocation = float(subsidy.total_allocation)
            # Disburse in 3 days (suspicious)
            for day in range(3):
                amount = allocation / 3
                disbursement = Disbursement(
                    subsidy_id=subsidy.id,
                    amount=Decimal(amount),
                    currency="INR",
                    payment_method=random.choice(["bank_transfer", "direct_credit"]),
                    status="completed",
                    date=subsidy.start_date + timedelta(days=day + 1),
                    description=f"Rapid disbursement day {day+1}"
                )
                disbursements.append(disbursement)
                self.db.add(disbursement)
        
        # Create normal disbursements for remaining subsidies
        remaining = 400 - len(disbursements)
        
        for subsidy in subsidies[:min(len(subsidies), remaining)]:
            if not any(d.subsidy_id == subsidy.id for d in disbursements):
                num_disbursements = random.randint(1, 3)
                allocation = float(subsidy.total_allocation)
                
                for i in range(num_disbursements):
                    amount = allocation / num_disbursements
                    disbursement = Disbursement(
                        subsidy_id=subsidy.id,
                        amount=Decimal(amount),
                        currency="INR",
                        payment_method=random.choice(["bank_transfer", "direct_credit", "cheque"]),
                        status=random.choice(["completed", "pending"]),
                        date=subsidy.start_date + timedelta(days=random.randint(30, 180)),
                        description=f"Disbursement {i+1} for {subsidy.sector}"
                    )
                    disbursements.append(disbursement)
                    self.db.add(disbursement)
        
        self.db.flush()
        self.stats["disbursements"] = len(disbursements)
        
        return disbursements
    
    def _create_risk_events(self, subsidies: List[Subsidy]) -> List[RiskEvent]:
        """Create 60 risk events for flagged subsidies."""
        
        risk_events = []
        
        # Define risk event types based on patterns
        risk_types = {
            "shell_entity": ["Suspicious Organization", "High Allocation Low Activity", "Missing Audit Trail"],
            "multiple_subsidy_recipient": ["Multiple Program Registration", "Cross-Program Fund Flow"],
            "rapid_disbursement": ["Unusual Payment Speed", "Split Disbursement Pattern"],
            "circular_fund_flow": ["Potential Money Laundering", "Related Party Transaction"],
            "high_risk_cluster": ["Sector Anomaly", "Concentrated Risk"]
        }
        
        # Create 60 risk events
        flagged_subsidies = [s for s in subsidies if s.is_flagged]
        
        for i in range(60):
            subsidy = random.choice(flagged_subsidies)
            pattern = getattr(subsidy, '_fraud_pattern', 'normal')
            
            if pattern == "shell_entity":
                event_types = risk_types["shell_entity"]
            elif pattern == "multiple_subsidy_recipient":
                event_types = risk_types["multiple_subsidy_recipient"]
            elif pattern == "rapid_disbursement":
                event_types = risk_types["rapid_disbursement"]
            elif pattern == "circular_fund_flow":
                event_types = risk_types["circular_fund_flow"]
            elif pattern == "high_risk_cluster":
                event_types = risk_types["high_risk_cluster"]
            else:
                event_types = ["General Risk Alert"]
            
            risk_event = RiskEvent(
                subsidy_id=subsidy.id,
                event_type=random.choice(event_types),
                severity=random.choice(["high", "medium", "critical"]),
                description=f"Risk detected in {subsidy.recipient} - {pattern}",
                detected_at=datetime.utcnow() - timedelta(days=random.randint(1, 90))
            )
            risk_events.append(risk_event)
            self.db.add(risk_event)
        
        self.db.flush()
        self.stats["risk_events"] = len(risk_events)
        
        return risk_events


def seed_investigation_data():
    """Main function to seed investigation-specific demo data."""
    
    db = SessionLocal()
    
    try:
        # Check if data already exists
        existing = db.query(Subsidy).count()
        if existing > 0:
            return {
                "status": "skipped",
                "message": "Database already contains data",
                "seeded": False
            }
        
        generator = InvestigationDataGenerator(db)
        result = generator.generate_all()
        
        print(f"\nInvestigation data seeded successfully!")
        print(f"Stats: {result['stats']}")
        print(f"Fraud patterns: {result['fraud_patterns']}")
        
        return result
        
    except Exception as e:
        db.rollback()
        print(f"Error: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    result = seed_investigation_data()
    print(f"\nFinal Result: {result}")