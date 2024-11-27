class ConversationNotFound(Exception):
    def __init__(self, message="Conversation not found"):
        self.message = message
        super().__init__(self.message)


class UserIDTokenNotFound(Exception):
    def __init__(self, message="User ID in token not found"):
        self.message = message
        super().__init__(self.message)


class TokenRevokedException(Exception):
    def __init__(self, message="Token has been revoked"):
        self.message = message
        super().__init__(self.message)
