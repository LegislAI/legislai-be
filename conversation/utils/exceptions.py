class ConversationNotFound(Exception):
    def __init__(self, message="Conversation not found"):
        self.message = message
        super().__init__(self.message)
