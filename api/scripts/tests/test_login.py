from getpass import getpass

from app.core.database import SessionLocal
from app.services import authenticate_user

email = input("E-mail cím: ").strip()
password = getpass("Jelszó: ")

with SessionLocal() as session:
    user = authenticate_user(
        session=session,
        email=email,
        password=password,
    )

print()
print("Hitelesítés sikeres:", user is not None)

if user:
    print("Felhasználó ID:", user.id)
    print("Név:", user.display_name)
    print("Platformadmin:", user.is_platform_admin)
