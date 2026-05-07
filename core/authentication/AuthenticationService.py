import os

from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError

from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives import hashes

class AuthenticationService:
    def __init__(self):
        """Initializes Argon2id hasher with secure parameters """
        self.ph = PasswordHasher()

    def hash_password(self, password: str) -> bytes:
        """Hashes a password using Argon2id
           Encode argon2-cffi's string output to bytes"""
        hash_string = self.ph.hash(password)

        return hash_string.encode('utf-8')

    def verify_password(self, password: str, stored_hash: bytes) -> bool:
        # Verifies password against an Argon2 hash.
        try:
            # Decode stored bytes back to string for argon2-cffi
            self.ph.verify(stored_hash.decode('utf-8'), password)
            return True
        except VerifyMismatchError:
            return False

    @staticmethod
    def derive_aes_key(password: str, salt: bytes) -> bytes:
        """Derives a 256-bit AES key from password and salt using PBKDF2"""
        kdf = PBKDF2HMAC(
            algorithm = hashes.SHA256(),
            length = 32,  # 32 bytes = 256 bits (AES-256)
            salt = salt,
            iterations = 600000,  # High iteration count to counter brute-forcing
        )

        return kdf.derive(password.encode('utf-8'))

    @staticmethod
    def encrypt(plaintext: str, key: bytes) -> bytes:
        """Encrypts a string with AES-256-GCM"""
        aesgcm = AESGCM(key)
        # GCM needs 96-bit or 12 byte nonce for every encryption
        nonce = os.urandom(12)
        ciphertext = aesgcm.encrypt(nonce, plaintext.encode('utf-8'), associated_data = None)

        # Prepend nonce to ciphertext, needed to decrypt later
        return nonce + ciphertext

    @staticmethod
    def decrypt(ciphertext: bytes, key: bytes) -> str:
        """Decrypts AES-256-GCM ciphertext back to string"""
        aesgcm = AESGCM(key)

        # Extract 12-byte nonce
        nonce = ciphertext[:12]
        actual_ciphertext = ciphertext[12:]

        plaintext_bytes = aesgcm.decrypt(nonce, actual_ciphertext, associated_data = None)

        return plaintext_bytes.decode('utf-8')