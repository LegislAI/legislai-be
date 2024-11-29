class UserNotFoundException(Exception):
    def __init__(self, message="User not found"):
        self.message = message
        super().__init__(self.message)


class TokenRevokedException(Exception):
    def __init__(self, message="Token has been revoked"):
        self.message = message
        super().__init__(self.message)


class LimitExceededException(Exception):
    def __init__(self, message="Query limit exceeded"):
        self.message = message
        super().__init__(self.message)
