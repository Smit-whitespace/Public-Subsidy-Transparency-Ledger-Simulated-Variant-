from backend.database.connection import SessionLocal
from backend.models.user import User
from backend.models.role import Role


def assign_role(username: str, role_name: str):
    db = SessionLocal()

    try:
        user = db.query(User).filter(User.username == username).first()
        role = db.query(Role).filter(Role.name == role_name).first()

        if not user:
            print("❌ User not found")
            return

        if not role:
            print("❌ Role not found")
            return

        user.roles.append(role)
        db.commit()

        print(f"✅ Assigned role '{role_name}' to '{username}'")

    finally:
        db.close()


if __name__ == "__main__":
    assign_role("admin", "admin")  # change username as needed