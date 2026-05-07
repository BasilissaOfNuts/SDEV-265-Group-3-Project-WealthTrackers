from typing import Optional

class UserSession:
    # Singleton class to hold the user's session in memory.
    _instance = None

    def __new__(cls):
        # If an instance doesn't exist, create one. Otherwise, return the existing one.
        if cls._instance is None:
            cls._instance = super(UserSession, cls).__new__(cls)

            # Initialize the state variables
            cls._instance.active_user_id: Optional[str] = None
            cls._instance.session_key: Optional[bytes] = None

        return cls._instance

    def start_session(self, user_id: str, key: bytes) -> None:
        # Populate session with authenticated user's data.
        self.active_user_id = user_id
        self.session_key = key

    def clear_session(self) -> None:
        # Wipe session when logging out.
        self.active_user_id = None
        self.session_key = None

    def get_key(self) -> Optional[bytes]:
        """Retrieves the AES key for the AccountRepository to use."""
        return self.session_key