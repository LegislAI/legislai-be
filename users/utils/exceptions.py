class UserNotFoundException(Exception):
    def __init__(self, message="User not found"):
        self.message = message
        super().__init__(self.message)


class TokenRevokedException(Exception):
    def __init__(self, message="Revoked token"):
        self.message = message
        super().__init__(self.message)
