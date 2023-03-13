from tokens import *
from errors import *

keywords = {
    "and": TokenType.AND,
    "class": TokenType.CLASS,
    "else": TokenType.ELSE,
    "false": TokenType.FALSE,
    "for": TokenType.FOR,
    "fun": TokenType.FUN,
    "if": TokenType.IF,
    "nil": TokenType.NIL,
    "or": TokenType.OR,
    "print": TokenType.PRINT,
    "return": TokenType.RETURN,
    "break": TokenType.BREAK,
    "super": TokenType.SUPER,
    "this": TokenType.THIS,
    "true": TokenType.TRUE,
    "var": TokenType.VAR,
    "while": TokenType.WHILE,
}


class Scanner:
    def __init__(self, source):
        self.source = source
        self.tokens = []
        self.start = 0
        self.current = 0
        self.line = 1

    def is_at_end(self):
        return self.current >= len(self.source)

    def advance(self):
        c = self.source[self.current]
        self.current += 1
        return c

    def match_c(self, expected):
        if self.is_at_end():
            return False
        elif self.source[self.current] != expected:
            return False

        self.current += 1
        return True

    def peek_next(self):
        if self.current + 1 >= len(self.source):
            return "\0"
        else:
            return self.source[self.current + 1]

    def peek(self):
        if self.is_at_end():
            return "\0"
        else:
            return self.source[self.current]

    def add_single_token(self, ttype: TokenType):
        self.add_token(ttype, None)

    def add_token(self, ttype: TokenType, literal):
        text = self.source[self.start : self.current]
        self.tokens.append(Token(ttype, text, literal, self.line))

    def string(self):
        while self.peek() != '"' and not self.is_at_end():
            if self.peek() == "\n":
                self.line += 1
            self.advance()
        if self.is_at_end():
            error(self.line, "Unterminated string.")
            return

        self.advance()

        value = self.source[self.start + 1 : self.current - 1]
        self.add_token(TokenType.STRING, value)

    def number(self):
        while self.peek().isdigit():
            self.advance()

        if self.peek() == "." and self.peek_next().isnumeric():
            self.advance()

            while self.peek().isnumeric():
                self.advance()

            value = float(self.source[self.start : self.current])
            self.add_token(TokenType.NUMBER, value)
        else:
            value = int(self.source[self.start : self.current])
            self.add_token(TokenType.NUMBER, value)

    def identifier(self):
        while self.peek().isalnum():
            self.advance()

        text = self.source[self.start : self.current]
        self.add_single_token(keywords.get(text, TokenType.IDENTIFIER))

    def scan_token(self):
        c = self.advance()

        if c == "(":
            self.add_single_token(TokenType.LEFT_PAREN)
        elif c == ")":
            self.add_single_token(TokenType.RIGHT_PAREN)
        elif c == "{":
            self.add_single_token(TokenType.LEFT_BRACE)
        elif c == "}":
            self.add_single_token(TokenType.RIGHT_BRACE)
        elif c == ".":
            self.add_single_token(TokenType.DOT)
        elif c == ",":
            self.add_single_token(TokenType.COMMA)
        elif c == "-":
            self.add_single_token(TokenType.MINUS)
        elif c == "+":
            self.add_single_token(TokenType.PLUS)
        elif c == ";":
            self.add_single_token(TokenType.SEMICOLON)
        elif c == "*":
            self.add_single_token(TokenType.STAR)
        elif c == "!":
            self.add_single_token(
                TokenType.BANG_EQUAL if self.match_c("=") else TokenType.BANG
            )
        elif c == "=":
            self.add_single_token(
                TokenType.EQUAL_EQUAL if self.match_c("=") else TokenType.EQUAL
            )
        elif c == "<":
            self.add_single_token(
                TokenType.LESS_EQUAL if self.match_c("=") else TokenType.LESS
            )
        elif c == ">":
            self.add_single_token(
                TokenType.GREATER_EQUAL if self.match_c("=") else TokenType.GREATER
            )
        elif c == "/":
            if self.match_c("/"):
                while self.peek() != "\n" and not self.is_at_end():
                    self.advance()
            else:
                self.add_single_token(TokenType.SLASH)
        elif c in " \r\t":
            pass
        elif c == "\n":
            self.line += 1
        elif c == '"':
            self.string()
        else:
            if c.isnumeric():
                self.number()
            elif c.isalpha() or c == "_":
                self.identifier()
            else:
                error(self.line, "Unexpected character.")

    def scan_tokens(self):
        while not self.is_at_end():
            self.start = self.current
            self.scan_token()
        self.tokens.append(Token(TokenType.EOF, "", None, self.line))
        return self.tokens
