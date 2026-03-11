from backend.database.connection import SessionLocal
from backend.seed.seed_roles import seed_roles


def main():
    db = SessionLocal()
    try:
        seed_roles(db)
        print("✅ RBAC roles seeded successfully")
    finally:
        db.close()


if __name__ == "__main__":
    main()