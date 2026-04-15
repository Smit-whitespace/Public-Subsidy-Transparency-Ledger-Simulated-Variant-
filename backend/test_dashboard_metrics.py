import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi.testclient import TestClient
from backend.main import app
from backend.database.connection import SessionLocal
from backend.models import User
from backend.utils.jwt import create_token

client = TestClient(app)

def test_dashboard_metrics_update():
    db = SessionLocal()
    admin_user = db.query(User).filter(User.username == "testadmin").first()
    token = create_token({"user_id": admin_user.id, "username": admin_user.username})
    headers = {"Authorization": f"Bearer {token}"}
    db.close()

    # Get initial dashboard summary
    r = client.get("/analytics/summary", headers=headers)
    assert r.status_code == 200, f"Failed to get summary: {r.text}"
    before = r.json()
    print(f"BEFORE: total_subsidies={before.get('total_subsidies')}, total_allocation={before.get('total_allocation')}")

    # CREATE a new subsidy
    create_data = {
        "title": "Dashboard Test Subsidy",
        "recipient": "Dashboard Recipient",
        "sector": "Education",
        "total_allocation": 99999.00,
        "currency": "INR",
        "status": "active"
    }
    r = client.post("/subsidies/", json=create_data, headers=headers)
    assert r.status_code == 201, f"Failed to create: {r.text}"
    sub_id = r.json()["id"]

    # Get dashboard summary again
    r = client.get("/analytics/summary", headers=headers)
    after = r.json()
    print(f"AFTER CREATE: total_subsidies={after.get('total_subsidies')}, total_allocation={after.get('total_allocation')}")

    assert after["total_subsidies"] > before["total_subsidies"], "Subsidy count should increase!"
    assert float(after["total_allocation"]) > float(before["total_allocation"]), "Total allocation should increase!"
    print("Dashboard metrics updated correctly after CREATE.")

    # DELETE the test subsidy
    r = client.delete(f"/subsidies/{sub_id}", headers=headers)
    assert r.status_code == 204

    # Verify metrics revert
    r = client.get("/analytics/summary", headers=headers)
    after_delete = r.json()
    print(f"AFTER DELETE: total_subsidies={after_delete.get('total_subsidies')}, total_allocation={after_delete.get('total_allocation')}")
    assert after_delete["total_subsidies"] == before["total_subsidies"], "Subsidy count should revert!"
    print("Dashboard metrics reverted correctly after DELETE.")
    print("ALL DASHBOARD METRICS TESTS PASSED")

if __name__ == "__main__":
    test_dashboard_metrics_update()
