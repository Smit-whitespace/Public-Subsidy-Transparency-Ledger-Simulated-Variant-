import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi.testclient import TestClient
from backend.main import app
from backend.database.connection import SessionLocal
from backend.models import User, Role, Subsidy
from backend.utils.jwt import create_token
from backend.services.auth_service import get_password_hash

# Set up test client
client = TestClient(app)

def test_demo_logic():
    db = SessionLocal()
    
    # Ensure an admin user exists
    admin_role = db.query(Role).filter(Role.name == "admin").first()
    if not admin_role:
        print("Admin role missing!")
        return
        
    admin_user = db.query(User).filter(User.username == "testadmin").first()
    if not admin_user:
        admin_user = User(username="testadmin", hashed_password=get_password_hash("password"))
        db.add(admin_user)
        db.commit()
        db.refresh(admin_user)
        admin_user.roles.append(admin_role)
        db.commit()
    
    token = create_token({"user_id": admin_user.id, "username": admin_user.username})
    headers = {"Authorization": f"Bearer {token}"}
    
    # 1. Check current status
    print("Checking status...")
    r = client.get("/demo/status")
    print("Status:", r.json())
    
    # 2. Test unauthorized access to toggle
    print("Testing unauthorized toggle...")
    r = client.post("/demo/toggle")
    print("Unauthorized Toggle response:", r.status_code)
    assert r.status_code == 401, f"Expected 401, got {r.status_code}"
    
    # 3. Test toggle ON with admin
    print("Toggling ON with admin...")
    r = client.post("/demo/toggle", headers=headers)
    print("Toggle ON:", r.json())
    
    # 4. Check data exists
    sub_count = db.query(Subsidy).count()
    print(f"Subsidies after toggle ON: {sub_count}")
    
    # 5. Toggle OFF (via clear or toggle again)
    print("Clearing data...")
    r = client.post("/demo/clear", headers=headers)
    print("Clear response:", r.json())
    
    # 6. Check data empty
    sub_count = db.query(Subsidy).count()
    print(f"Subsidies after clear: {sub_count}")
    
    db.close()

if __name__ == "__main__":
    test_demo_logic()
