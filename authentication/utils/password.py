from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError
import secrets
from typing import Tuple


class SecurityUtils:
    def __init__(self):
        # Initialize Argon2 password hasher with secure defaults
        self.ph = PasswordHasher(
            time_cost=2,  # Number of iterations
            memory_cost=102400,  # Memory usage in kB (100 MB)
            parallelism=8,  # Number of parallel threads
            hash_len=32,  # Length of the hash in bytes
            salt_len=16,  # Length of the salt in bytes
        )

    def hash_password(self, password: str) -> str:
        """
        Hash a password using Argon2id.
        """
        return self.ph.hash(password)

    def verify_password(self, hashed_password: str, password: str) -> bool:
        """
        Verify a password against its hash.
        """
        try:
            self.ph.verify(hashed_password, password)
            return True
        except VerifyMismatchError:
            return False
        except Exception:
            return False

    @staticmethod
    def generate_reset_token() -> Tuple[str, str]:
        """
        Generate a secure reset token and its hash.
        """
        token = secrets.token_urlsafe(32)
        token_hash = PasswordHasher().hash(token)
        return token, token_hash
