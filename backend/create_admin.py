from app.database.session import SessionLocal
from app.models.user import User, UserRole
from app.core.security import hash_password

db = SessionLocal()

email = "admin@restaurant.com"
existing = db.query(User).filter(User.email == email).first()

if existing:
    print("Cet admin existe déjà.")
else:
    admin = User(
        name="Admin Principal",
        email=email,
        password_hash=hash_password("admin123"),
        role=UserRole.ADMIN,
        is_active=True,
    )
    db.add(admin)
    db.commit()
    print(f"Admin créé : {email} / mot de passe : admin123")

db.close()