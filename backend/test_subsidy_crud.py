import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi.testclient import TestClient
from backend.main import app
from backend.database.connection import SessionLocal
from backend.models import User, Role
from backend.utils.jwt import create_token
from backend.services.auth_service import get_password_hash

client = TestClient(app)

def test_subsidy_crud():
    db = SessionLocal()
    admin_role = db.query(Role).filter(Role.name == "admin").first()
    admin_user = db.query(User).filter(User.username == "testadmin").first()
    token = create_token({"user_id": admin_user.id, "username": admin_user.username})
    headers = {"Authorization": f"Bearer {token}"}
    
    # 1. CREATE
    print("Testing CREATE...")
    create_data = {
        "title": "Test Subsidy",
        "recipient": "Test Recipient",
        "sector": "Education",
        "total_allocation": 1000.50,
        "currency": "INR",
        "description": "Test Desc",
        "status": "active"
    }
    r = client.post("/subsidies/", json=create_data, headers=headers)
    assert r.status_code == 201, f"Failed Create: {r.text}"
    sub_id = r.json()["id"]
    print(f"Created Subsidy ID: {sub_id}")
    
    # 2. READ
    print("Testing READ LIST...")
    r = client.get("/subsidies/", headers=headers)
    assert r.status_code == 200, f"Failed Get List: {r.text}"
    
    print("Testing READ SINGLE...")
    r = client.get(f"/subsidies/{sub_id}", headers=headers)
    assert r.status_code == 200, f"Failed Get Specific: {r.text}"
    assert r.json()["title"] == "Test Subsidy"
    
    # 3. UPDATE
    print("Testing UPDATE...")
    update_data = {
        "title": "Updated Test Subsidy",
        "total_allocation": 2000.00
    }
    r = client.patch(f"/subsidies/{sub_id}", json=update_data, headers=headers)
    assert r.status_code == 200, f"Failed Update: {r.text}"
    assert r.json()["title"] == "Updated Test Subsidy"
    assert "2000" in str(r.json()["total_allocation"])
    
    # 4. DELETE
    print("Testing DELETE...")
    r = client.delete(f"/subsidies/{sub_id}", headers=headers)
    assert r.status_code == 204, f"Failed Delete: {r.text}"
    
    r = client.get(f"/subsidies/{sub_id}", headers=headers)
    assert r.status_code == 404, "Subsidy should be deleted"
    
    print("ALL SUBSIDY CRUD TESTS PASSED")

if __name__ == "__main__":
    test_subsidy_crud()
