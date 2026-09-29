"""Create the four default demo accounts. Run once: python seed.py"""
from app.database import Base, SessionLocal, engine
from app.models import User
from app.security import hash_password

DEFAULT_USERS = [
    ("admin", "admin123", "System Admin", "admin"),
    ("officer1", "police123", "Insp. R. Deshmukh", "police"),
    ("judge1", "court123", "Judge A. Kulkarni", "court"),
    ("jailer1", "custody123", "Jailer S. Rao", "custody"),
]


def main():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        for username, pw, full_name, role in DEFAULT_USERS:
            if db.query(User).filter(User.username == username).first():
                continue
            db.add(User(username=username, full_name=full_name, role=role,
                        password_hash=hash_password(pw)))
        db.commit()
        print("Seeded default users:")
        for u, pw, name, role in DEFAULT_USERS:
            print(f"  {u} / {pw}  ({role})")
    finally:
        db.close()


if __name__ == "__main__":
    main()
