import os
import sys
import datetime
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi.testclient import TestClient
from backend.main import app
from backend.database.connection import SessionLocal
from backend.models import User, Role, Subsidy
from backend.utils.jwt import create_token

client = TestClient(app)

def test_disbursement_crud():
    db = SessionLocal()
    admin_user = db.query(User).filter(User.username == "testadmin").first()
    token = create_token({"user_id": admin_user.id, "username": admin_user.username})
    headers = {"Authorization": f"Bearer {token}"}

    # Create a test subsidy first
    subsidy = Subsidy(
        title="Disbursement Test Subsidy",
        recipient="Test Recipient",
        sector="Education",
        total_allocation=50000,
        currency="INR"
    )
    db.add(subsidy)
    db.commit()
    db.refresh(subsidy)
    sub_id = subsidy.id

    print("Testing CREATE...")
    create_data = {
        "subsidy_id": sub_id,
        "amount": 500.50,
        "date": datetime.datetime.utcnow().isoformat(),
        "notes": "Initial disbursement"
    }
    r = client.post("/disbursements/", json=create_data, headers=headers)
    assert r.status_code == 201, f"Failed Create: {r.text}"
    disb_id = r.json()["id"]
    print(f"Created Disbursement ID: {disb_id} | approval_status: {r.json().get('approval_status')}")

    print("Testing READ LIST...")
    r = client.get(f"/disbursements/?subsidy_id={sub_id}", headers=headers)
    assert r.status_code == 200, f"Failed Get List: {r.text}"
    assert len(r.json()) > 0, "List should have at least one disbursement"

    print("Testing READ SINGLE...")
    r = client.get(f"/disbursements/{disb_id}", headers=headers)
    assert r.status_code == 200, f"Failed Get Single: {r.text}"
    assert r.json()["approval_status"] == "pending"

    print("Testing UPDATE...")
    update_data = {"amount": 999.99, "notes": "Updated note"}
    r = client.patch(f"/disbursements/{disb_id}", json=update_data, headers=headers)
    assert r.status_code == 200, f"Failed Update: {r.text}"
    assert "999" in str(r.json()["amount"]), f"Amount not updated: {r.json()}"

    print("Testing DELETE...")
    r = client.delete(f"/disbursements/{disb_id}", headers=headers)
    assert r.status_code == 204, f"Failed Delete: {r.text}"

    r = client.get(f"/disbursements/{disb_id}", headers=headers)
    assert r.status_code == 404, "Disbursement should be deleted"

    # Cleanup subsidy
    db.delete(db.get(Subsidy, sub_id))
    db.commit()
    db.close()

    print("ALL DISBURSEMENT CRUD TESTS PASSED")

if __name__ == "__main__":
    test_disbursement_crud()
