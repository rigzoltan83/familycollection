from getpass import getpass

from app.core.database import SessionLocal
from app.services import authenticate_user


identifier = input(
    "E-mail cím vagy felhasználónév: "
).strip()

password = getpass(
    "Jelszó: "
)

with SessionLocal() as session:
    user = authenticate_user(
        session=session,
        identifier=identifier,
        password=password,
    )

print()
print(
    "Hitelesítés sikeres:",
    user is not None,
)

if user:
    print(
        "Felhasználó ID:",
        user.id,
    )

    print(
        "Felhasználónév:",
        user.username,
    )

    print(
        "E-mail:",
        user.email,
    )

    print(
        "Név:",
        user.display_name,
    )

    print(
        "Platformadmin:",
        user.is_platform_admin,
    )
