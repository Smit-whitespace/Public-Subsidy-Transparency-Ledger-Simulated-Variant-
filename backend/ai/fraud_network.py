"""
backend/ai/fraud_network.py

Fraud Network Detection - Identifies suspicious relationships between entities.

Detects patterns such as:
- Multiple subsidies linked to same recipients
- Repeated contractors across projects  
- Unusual clustering of payments

Uses graph-based analysis to identify network risk indicators.
"""

from collections import defaultdict
from typing import Dict, List, Any, Set, Tuple
from sqlalchemy.orm import Session

from backend.models.subsidy import Subsidy
from backend.models.project import Project
from backend.models.disbursement import Disbursement


class NetworkRiskLevel:
    """Risk classification for network analysis"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class FraudNetworkDetector:
    """
    Detects suspicious relationship patterns in subsidy data.
    """
    
    # Thresholds for flagging
    SAME_RECIPIENT_THRESHOLD = 3  # Same recipient across 3+ subsidies
    SAME_OWNER_THRESHOLD = 5      # Same owner across 5+ projects
    PAYMENT_CLUSTER_THRESHOLD = 4 # Payments to same recipient within period
    
    def __init__(self, db: Session):
        self.db = db
    
    def analyze_all_entities(self) -> Dict[str, Any]:
        """
        Perform comprehensive network analysis on all entities.
        
        Returns:
            Dictionary with risk indicators and flagged entities
        """
        recipient_analysis = self._analyze_recipient_patterns()
        owner_analysis = self._analyze_owner_patterns()
        payment_cluster_analysis = self._analyze_payment_clusters()
        
        # Calculate overall network risk score
        risk_score = self._calculate_network_risk_score(
            recipient_analysis,
            owner_analysis,
            payment_cluster_analysis
        )
        
        return {
            "network_risk_score": risk_score,
            "recipient_patterns": recipient_analysis,
            "owner_patterns": owner_analysis,
            "payment_clusters": payment_cluster_analysis,
            "flagged_entities": self._get_flagged_entities(
                recipient_analysis,
                owner_analysis,
                payment_cluster_analysis
            )
        }
    
    def _analyze_recipient_patterns(self) -> Dict[str, Any]:
        """
        Analyze subsidies with same recipients.
        """
        # Group subsidies by recipient
        recipient_subsidies = defaultdict(list)
        
        subsidies = self.db.query(Subsidy).all()
        for s in subsidies:
            if s.recipient:
                recipient_subsidies[s.recipient].append({
                    "id": s.id,
                    "title": s.title,
                    "sector": s.sector,
                    "total_allocation": float(s.total_allocation or 0),
                    "status": s.status.value if hasattr(s.status, 'value') else str(s.status)
                })
        
        # Find high-risk recipients
        flagged_recipients = {}
        for recipient, subsidies_list in recipient_subsidies.items():
            if len(subsidies_list) >= self.SAME_RECIPIENT_THRESHOLD:
                total_allocation = sum(s["total_allocation"] for s in subsidies_list)
                risk_level = self._calculate_recipient_risk(
                    len(subsidies_list), 
                    total_allocation
                )
                
                flagged_recipients[recipient] = {
                    "subsidy_count": len(subsidies_list),
                    "total_allocation": total_allocation,
                    "risk_level": risk_level,
                    "subsidies": subsidies_list
                }
        
        return {
            "total_recipients": len(recipient_subsidies),
            "flagged_count": len(flagged_recipients),
            "flagged_recipients": flagged_recipients
        }
    
    def _analyze_owner_patterns(self) -> Dict[str, Any]:
        """
        Analyze projects with same owners.
        """
        # Group projects by owner
        owner_projects = defaultdict(list)
        
        projects = self.db.query(Project).all()
        for p in projects:
            if p.owner:
                owner_projects[p.owner].append({
                    "id": p.id,
                    "name": p.name,
                    "subsidy_id": p.subsidy_id,
                    "status": p.status
                })
        
        # Find high-risk owners
        flagged_owners = {}
        for owner, projects_list in owner_projects.items():
            if len(projects_list) >= self.SAME_OWNER_THRESHOLD:
                risk_level = self._calculate_owner_risk(len(projects_list))
                
                flagged_owners[owner] = {
                    "project_count": len(projects_list),
                    "risk_level": risk_level,
                    "projects": projects_list
                }
        
        return {
            "total_owners": len(owner_projects),
            "flagged_count": len(flagged_owners),
            "flagged_owners": flagged_owners
        }
    
    def _analyze_payment_clusters(self) -> Dict[str, Any]:
        """
        Detect unusual clustering of payments to same recipients.
        """
        # Group disbursements by subsidy (to find clustering within subsidies)
        clusters = []
        
        subsidies = self.db.query(Subsidy).all()
        for subsidy in subsidies:
            disbursements = self.db.query(Disbursement).filter(
                Disbursement.subsidy_id == subsidy.id
            ).all()
            
            if len(disbursements) >= self.PAYMENT_CLUSTER_THRESHOLD:
                # Check for rapid succession payments
                sorted_disbursements = sorted(
                    disbursements, 
                    key=lambda d: d.date or __import__('datetime').datetime.min
                )
                
                cluster_info = self._detect_payment_cluster(
                    subsidy.id,
                    sorted_disbursements
                )
                
                if cluster_info["is_suspicious"]:
                    clusters.append(cluster_info)
        
        return {
            "suspicious_clusters": clusters,
            "cluster_count": len(clusters)
        }
    
    def _detect_payment_cluster(
        self, 
        subsidy_id: int, 
        disbursements: List[Disbursement]
    ) -> Dict[str, Any]:
        """Detect if payment cluster is suspicious."""
        if len(disbursements) < 2:
            return {"is_suspicious": False}
        
        # Calculate time gaps between payments
        from datetime import timedelta
        gaps = []
        for i in range(1, len(disbursements)):
            if disbursements[i].date and disbursements[i-1].date:
                gap = (disbursements[i].date - disbursements[i-1].date).days
                gaps.append(gap)
        
        # Check for unusual patterns
        is_suspicious = False
        reasons = []
        
        # Very short gaps (same day or consecutive)
        if any(gap <= 1 for gap in gaps):
            is_suspicious = True
            reasons.append("Very short intervals between payments")
        
        # All payments on same day
        if all(gap == 0 for gap in gaps if gap == 0):
            is_suspicious = True
            reasons.append("Multiple payments on same day")
        
        # Unusual amount distribution
        amounts = [float(d.amount) for d in disbursements]
        if amounts:
            avg = sum(amounts) / len(amounts)
            if all(a <= avg * 1.5 for a in amounts):
                is_suspicious = True
                reasons.append("Suspiciously uniform payment amounts")
        
        return {
            "subsidy_id": subsidy_id,
            "disbursement_count": len(disbursements),
            "is_suspicious": is_suspicious,
            "reasons": reasons,
            "total_amount": sum(amounts)
        }
    
    def _calculate_recipient_risk(
        self, 
        subsidy_count: int, 
        total_allocation: float
    ) -> str:
        """Calculate risk level for recipient patterns."""
        if subsidy_count >= 10 or total_allocation > 100_000_000:
            return NetworkRiskLevel.CRITICAL
        elif subsidy_count >= 7 or total_allocation > 50_000_000:
            return NetworkRiskLevel.HIGH
        elif subsidy_count >= 5 or total_allocation > 10_000_000:
            return NetworkRiskLevel.MEDIUM
        else:
            return NetworkRiskLevel.LOW
    
    def _calculate_owner_risk(self, project_count: int) -> str:
        """Calculate risk level for owner patterns."""
        if project_count >= 15:
            return NetworkRiskLevel.CRITICAL
        elif project_count >= 10:
            return NetworkRiskLevel.HIGH
        elif project_count >= 7:
            return NetworkRiskLevel.MEDIUM
        else:
            return NetworkRiskLevel.LOW
    
    def _calculate_network_risk_score(
        self,
        recipient_analysis: Dict,
        owner_analysis: Dict,
        payment_clusters: Dict
    ) -> float:
        """Calculate overall network risk score (0-100)."""
        score = 0.0
        
        # Recipient pattern contribution (max 40 points)
        recipient_flags = recipient_analysis.get("flagged_count", 0)
        score += min(40, recipient_flags * 8)
        
        # Owner pattern contribution (max 30 points)
        owner_flags = owner_analysis.get("flagged_count", 0)
        score += min(30, owner_flags * 6)
        
        # Payment cluster contribution (max 30 points)
        cluster_count = payment_clusters.get("cluster_count", 0)
        score += min(30, cluster_count * 7.5)
        
        return round(score, 2)
    
    def _get_flagged_entities(
        self,
        recipient_analysis: Dict,
        owner_analysis: Dict,
        payment_clusters: Dict
    ) -> List[Dict[str, Any]]:
        """Get list of all flagged entities."""
        flagged = []
        
        # Add flagged recipients
        for recipient, data in recipient_analysis.get("flagged_recipients", {}).items():
            flagged.append({
                "type": "recipient",
                "entity": recipient,
                "count": data["subsidy_count"],
                "risk_level": data["risk_level"],
                "total_allocation": data["total_allocation"]
            })
        
        # Add flagged owners
        for owner, data in owner_analysis.get("flagged_owners", {}).items():
            flagged.append({
                "type": "owner",
                "entity": owner,
                "count": data["project_count"],
                "risk_level": data["risk_level"]
            })
        
        return flagged


def get_fraud_network_analysis(db: Session) -> Dict[str, Any]:
    """
    Public function to get fraud network analysis.
    Can be called by API endpoints.
    """
    detector = FraudNetworkDetector(db)
    return detector.analyze_all_entities()