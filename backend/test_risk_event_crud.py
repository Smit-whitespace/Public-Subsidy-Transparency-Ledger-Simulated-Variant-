import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi.testclient import TestClient
from backend.main import app
from backend.database.connection import SessionLocal
from backend.models import User, Subsidy
from backend.utils.jwt import create_token

client = TestClient(app)

def test_risk_event_crud():
    db = SessionLocal()
    admin_user = db.query(User).filter(User.username == "testadmin").first()
    token = create_token({"user_id": admin_user.id, "username": admin_user.username})
    headers = {"Authorization": f"Bearer {token}"}

    # Create a subsidy to attach the risk event to
    subsidy = Subsidy(
        title="Risk Event Test Subsidy",
        recipient="Test Recipient",
        sector="Healthcare",
        total_allocation=25000,
        currency="INR"
    )
    db.add(subsidy)
    db.commit()
    db.refresh(subsidy)
    sub_id = subsidy.id

    print("Testing CREATE...")
    create_data = {
        "subsidy_id": sub_id,
        "event_type": "anomaly",
        "severity": "high",
        "description": "Suspicious withdrawal pattern detected"
    }
    r = client.post("/risk-events/", json=create_data, headers=headers)
    assert r.status_code == 201, f"Failed Create: {r.text}"
    event_id = r.json()["id"]
    print(f"Created Risk Event ID: {event_id}")

    print("Testing READ LIST...")
    r = client.get(f"/risk-events/?subsidy_id={sub_id}", headers=headers)
    assert r.status_code == 200, f"Failed Get List: {r.text}"
    assert len(r.json()) > 0

    print("Testing READ SINGLE...")
    r = client.get(f"/risk-events/{event_id}", headers=headers)
    assert r.status_code == 200, f"Failed Get Single: {r.text}"
    assert r.json()["severity"] == "high"

    print("Testing UPDATE...")
    update_data = {"severity": "medium", "description": "Reviewed by auditor"}
    r = client.patch(f"/risk-events/{event_id}", json=update_data, headers=headers)
    assert r.status_code == 200, f"Failed Update: {r.text}"
    assert r.json()["severity"] == "medium"
    print("Update result:", r.json()["description"])

    print("Testing Invalid Severity validation...")
    bad_data = {"severity": "extreme"}
    r = client.patch(f"/risk-events/{event_id}", json=bad_data, headers=headers)
    assert r.status_code == 400, f"Should have rejected invalid severity: {r.text}"

    print("Testing DELETE...")
    r = client.delete(f"/risk-events/{event_id}", headers=headers)
    assert r.status_code == 200, f"Failed Delete: {r.text}"

    r = client.get(f"/risk-events/{event_id}", headers=headers)
    assert r.status_code == 404, "Event should be deleted"

    # Cleanup
    db.delete(db.get(Subsidy, sub_id))
    db.commit()
    db.close()

    print("ALL RISK EVENT CRUD TESTS PASSED")

if __name__ == "__main__":
    test_risk_event_crud()
