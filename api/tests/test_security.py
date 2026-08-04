from app.core.security import hash_password, verify_password


def test_hash_password_creates_argon2id_hash() -> None:
    hashed = hash_password("FamilyCollection-teszt-123")

    assert hashed.startswith("$argon2id$")
    assert hashed != "FamilyCollection-teszt-123"


def test_verify_password_accepts_correct_password() -> None:
    plain_password = "FamilyCollection-teszt-123"
    hashed = hash_password(plain_password)

    assert verify_password(
        plain_password,
        hashed,
    ) is True


def test_verify_password_rejects_wrong_password() -> None:
    hashed = hash_password("FamilyCollection-teszt-123")

    assert verify_password(
        "rossz-jelszo",
        hashed,
    ) is False


def test_verify_password_rejects_empty_values() -> None:
    assert verify_password("", "valamilyen-hash") is False
    assert verify_password("jelszo", "") is False
