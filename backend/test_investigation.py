import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi.testclient import TestClient
from backend.main import app
from backend.database.connection import SessionLocal
from backend.models import User, Role, Subsidy
from backend.utils.jwt import create_token
from backend.services.auth_service import get_password_hash

client = TestClient(app)

def test_investigation():
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
    
    print("Seeding demo data...")
    client.post("/demo/seed", headers=headers)
    
    print("Getting fraud network data...")
    r = client.get("/analytics/fraud-network", headers=headers)
    if r.status_code != 200:
        print(f"Failed to get fraud network: {r.status_code} {r.text}")
        return
        
    data = r.json()
    graph = data.get("graph", {})
    nodes = graph.get("nodes", [])
    links = graph.get("links", [])
    
    print(f"Graph has {len(nodes)} nodes and {len(links)} links.")
    
    types = {}
    for n in nodes:
        types[n["type"]] = types.get(n["type"], 0) + 1
    print("Node types:", types)
    
    link_types = set([l["type"] for l in links])
    print("Link types created:", link_types)
    
    # Find specific links
    rec_to_sub = sum(1 for l in links if l["type"] == "receives")
    sub_to_proj = sum(1 for l in links if l["type"] == "funds")
    sub_to_disb = sum(1 for l in links if l["type"] == "disburses")
    
    print(f"Recipient -> Subsidy links: {rec_to_sub}")
    print(f"Subsidy -> Project links: {sub_to_proj}")
    print(f"Subsidy -> Disbursement links: {sub_to_disb}")
    
    print("Test Complete.")
    db.close()

if __name__ == "__main__":
    test_investigation()
