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

def test_project_crud():
    db = SessionLocal()
    admin_role = db.query(Role).filter(Role.name == "admin").first()
    admin_user = db.query(User).filter(User.username == "testadmin").first()
    token = create_token({"user_id": admin_user.id, "username": admin_user.username})
    headers = {"Authorization": f"Bearer {token}"}
    
    print("Testing CREATE...")
    create_data = {
        "name": "Test Project",
        "owner": "Test Owner",
        "status": "planned"
    }
    r = client.post("/projects/", json=create_data, headers=headers)
    assert r.status_code == 201, f"Failed Create: {r.text}"
    proj_id = r.json()["id"]
    print(f"Created Project ID: {proj_id}")
    
    print("Testing READ LIST...")
    r = client.get("/projects/", headers=headers)
    assert r.status_code == 200, f"Failed Get List: {r.text}"
    
    print("Testing READ SINGLE...")
    r = client.get(f"/projects/{proj_id}", headers=headers)
    assert r.status_code == 200, f"Failed Get Specific: {r.text}"
    assert r.json()["name"] == "Test Project"
    
    print("Testing UPDATE...")
    update_data = {
        "name": "Updated Test Project",
        "status": "active"
    }
    r = client.patch(f"/projects/{proj_id}", json=update_data, headers=headers)
    # Wait, the Project route doesn't require auth?! 
    # Ah, the admin requirement might be missing from the project_routes.py
    assert r.status_code == 200, f"Failed Update: {r.text}"
    assert r.json()["name"] == "Updated Test Project"
    
    print("Testing DELETE...")
    r = client.delete(f"/projects/{proj_id}", headers=headers)
    assert r.status_code == 204, f"Failed Delete: {r.text}"
    
    r = client.get(f"/projects/{proj_id}", headers=headers)
    assert r.status_code == 404, "Project should be deleted"
    
    print("ALL PROJECT CRUD TESTS PASSED")

if __name__ == "__main__":
    test_project_crud()
