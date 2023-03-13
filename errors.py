from tokens import Token, TokenType


def error(line, message):
    report(line, "", message)


class Globals:
    had_error = False
    had_runtime_error = False


def report(line, where, message):
    print(f"[line {line}] Error{where}: {message}")
    Globals.had_error = True


def runtime_error(error):
    print(f"[line {error.token.line}] Runtime error: {error.message}")
    Globals.had_runtime_error = True


def add_error(token: Token, msg):
    if token.ttype == TokenType.EOF:
        report(token.line, " at end", msg)
    else:
        report(token.line, f" at '{token.lexeme}'", msg)


class InterpretationError(Exception):
    def __init__(self, token, message):
        self.token = token
        self.message = message
