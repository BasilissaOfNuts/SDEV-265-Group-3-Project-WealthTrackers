import pytest

from core.authentication.UserSession import UserSession
from core.authentication.AuthenticationService import AuthenticationService

def test_singleton_identity():
    # Verify UserSession is a strict singleton
    s1 = UserSession()
    s2 = UserSession()
    assert s1 is s2

def test_password_hashing():
    auth = AuthenticationService()
    password = "IvyTechSDEV265Project!"
    hashed = auth.hash_password(password)

    # Verify it's hashed and verifiable
    assert auth.verify_password(password, hashed) is True
    assert auth.verify_password("wrong_password", hashed) is False

def test_encryption_decryption():
    auth = AuthenticationService()
    key = auth.derive_aes_key("master_password", b"static_salt_for_test")
    original_text = "Secret Account 12345"

    encrypted = auth.encrypt(original_text, key)
    decrypted = auth.decrypt(encrypted, key)

    assert decrypted == original_text
    assert encrypted != original_text.encode()

if __name__ == "__main__":
    pytest.main([__file__])