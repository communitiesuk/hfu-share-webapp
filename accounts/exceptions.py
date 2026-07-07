class EntraAuthException(Exception):
    pass


class TokenError(EntraAuthException):
    def __init__(self, message, description):
        self.message = message if message else ""
        self.description = description if description else ""

    def __str__(self):
        return f"{self.message}\n{self.description}"


class FlowError(EntraAuthException):
    def __init__(self, message):
        self.message = message if message else ""

    def __str__(self):
        return f"{self.message}"
