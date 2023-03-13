from typing import List

from AstPrinter import *
from tokens import Token, TokenType
from errors import add_error, error


class ParseError(Exception):
    pass


class Parser:
    def __init__(self, tokens: List[Token]) -> None:
        self.tokens = tokens
        self.current = 0
        self.loop_depth = 0

    def parse(self):
        statements = []
        while not self.is_at_end():
            statements.append(self.declaration())
        return statements

    def declaration(self):
        try:
            if self.match(TokenType.CLASS):
                return self.class_declaration()
            if self.match(TokenType.FUN):
                return self.function("function")
            if self.match(TokenType.VAR):
                return self.var_declaration()

            return self.statement()
        except ParseError:
            self.synchronize()
            return None

    def class_declaration(self):
        name = self.consume(TokenType.IDENTIFIER, "Expect class name.")

        superclass = None
        if self.match(TokenType.LESS):
            self.consume(TokenType.IDENTIFIER, "Expect superclass name")
            superclass = Variable(self.previous())

        self.consume(TokenType.LEFT_BRACE, "Expect '{' before class body.")
        methods = []
        while not self.check(TokenType.RIGHT_BRACE) and not self.is_at_end():
            methods.append(self.function("method"))
        self.consume(TokenType.RIGHT_BRACE, "Expect '}' after class body.")

        return Class(name, superclass, methods)

    def var_declaration(self):
        name = self.consume(TokenType.IDENTIFIER, "Expect variable name.")
        initializer = None

        if self.match(TokenType.EQUAL):
            initializer = self.expression()

        self.consume(TokenType.SEMICOLON, "Expect ';' after variable declaration.")
        return Var(name, initializer)

    def function(self, kind):
        name = self.consume(TokenType.IDENTIFIER, f"Expect {kind} name.")
        self.consume(TokenType.LEFT_PAREN, f"Expect '(' after {kind} name.")
        params = []
        if not self.check(TokenType.RIGHT_PAREN):
            params.append(self.consume(TokenType.IDENTIFIER, "Expect parameter name."))

            while self.match(TokenType.COMMA):
                if len(params) >= 255:
                    self.error(self.peek(), "Can't have more than 255 parameters.")
                params.append(
                    self.consume(TokenType.IDENTIFIER, "Expect parameter name.")
                )
        self.consume(TokenType.RIGHT_PAREN, f"Expect ')' after {kind} parameters.")
        self.consume(TokenType.LEFT_BRACE, "Expect '{' before the " f"{kind} body.")
        body = self.block()
        return Function(name, params, body)

    def parameters(self):
        return []

    def statement(self):
        if self.match(TokenType.RETURN):
            return self.return_statement()
        if self.match(TokenType.PRINT):
            return self.print_statement()
        if self.match(TokenType.IF):
            return self.if_statement()
        if self.match(TokenType.WHILE):
            return self.while_statement()
        if self.match(TokenType.FOR):
            return self.for_statement()
        if self.match(TokenType.LEFT_BRACE):
            return Block(self.block())

        return self.expression_statement()

    def return_statement(self):
        keyword = self.previous()
        value = None
        if not self.check(TokenType.SEMICOLON):
            value = self.expression()
        self.consume(TokenType.SEMICOLON, "Expect ';' after return value.")
        return Return(keyword, value)

    def break_statement(self):
        # print(self.loop_depth)
        keyword = self.previous()
        if self.loop_depth == 0:
            self.error(TokenType.BREAK, "Must be inside loop")
        self.consume(TokenType.SEMICOLON, "Expect ';' after break.")
        return Break(keyword, self.loop_depth)
    
    def if_statement(self):
        self.consume(TokenType.LEFT_PAREN, "Expect '(' after 'if'")
        condition = self.expression()
        self.consume(TokenType.RIGHT_PAREN, "Expect ')' after if condition.")
        then_branch = self.statement()
        else_branch = None
        if self.match(TokenType.ELSE):
            else_branch = self.statement()
        return If(condition, then_branch, else_branch)

    def print_statement(self):
        expr = self.expression()
        self.consume(TokenType.SEMICOLON, "Expect ';' after value.")
        return Print(expr)

    def while_statement(self):
        self.consume(TokenType.LEFT_PAREN, "Expect '(' after 'while'")
        condition = self.expression()
        self.consume(TokenType.RIGHT_PAREN, "Expect ')' after while condition.")
        try:
            self.loop_depth += 1
            return While(condition, self.statement())
        finally:
            self.loop_depth -= 1
            
    def for_statement(self):
        self.consume(TokenType.LEFT_PAREN, "Expect '(' after 'for'")

        if self.match(TokenType.SEMICOLON):
            initializer = None
        elif self.match(TokenType.VAR):
            initializer = self.var_declaration()
        else:
            initializer = self.expression_statement()

        if self.check(TokenType.SEMICOLON):
            condition = None
        else:
            condition = self.expression()
        self.consume(TokenType.SEMICOLON, "Expect ';' after for condition.")

        if self.check(TokenType.RIGHT_PAREN):
            increment = None
        else:
            increment = self.expression()
        self.consume(TokenType.RIGHT_PAREN, "Expect ')' after for clauses.")
        try:
            self.loop_depth += 1
            body = self.statement()

            initializer_list: List[Stmt] = [] if initializer is None else [initializer]
            condition_expr = Literal(True) if condition is None else condition
            increment_list: List[Stmt] = (
                [] if increment is None else [Expression(increment)]
            )

            return Block(
                initializer_list + [While(condition_expr, Block([body] + increment_list))]
            )
        finally:
            self.loop_depth -= 1

    def block(self):
        statements = []

        while not self.check(TokenType.RIGHT_BRACE) and not self.is_at_end():
            statements.append(self.declaration())

        self.consume(TokenType.RIGHT_BRACE, "Expect '}' after block.")

        return statements

    def expression_statement(self):
        expr = self.expression()
        self.consume(TokenType.SEMICOLON, "Expect ';' after expression.")
        return Expression(expr)

    def expression(self):
        return self.assignment()

    def assignment(self):
        expr = self.logical_or()

        if self.match(TokenType.EQUAL):
            equals = self.previous()
            value = self.assignment()

            if isinstance(expr, Variable):
                return Assign(expr.name, value)
            elif isinstance(expr, Get):
                return Set(expr.object, expr.name, value)

            raise self.error(equals, "Invalid assignment target.")

        return expr

    def logical_or(self):
        expr = self.logical_and()

        while self.match(TokenType.OR):
            expr = Logical(expr, self.previous(), self.logical_and())

        return expr

    def logical_and(self):
        expr = self.equality()

        while self.match(TokenType.AND):
            expr = Logical(expr, self.previous(), self.equality())

        return expr

    def equality(self):
        left = self.comparison()

        while self.match(TokenType.BANG_EQUAL, TokenType.EQUAL_EQUAL):
            left = Binary(left, self.previous(), self.comparison())

        return left

    def comparison(self):
        left = self.term()

        while self.match(
            TokenType.GREATER,
            TokenType.GREATER_EQUAL,
            TokenType.LESS,
            TokenType.LESS_EQUAL,
        ):
            left = Binary(left, self.previous(), self.term())

        return left

    def term(self):
        left = self.factor()

        while self.match(TokenType.MINUS, TokenType.PLUS):
            left = Binary(left, self.previous(), self.factor())

        return left

    def factor(self):
        left = self.unary()

        while self.match(TokenType.SLASH, TokenType.STAR):
            left = Binary(left, self.previous(), self.unary())

        return left

    def unary(self) -> Expr:
        if self.match(TokenType.MINUS, TokenType.BANG):
            return Unary(self.previous(), self.unary())
        else:
            return self.call()

    def call(self):
        expr = self.primary()

        while True:
            if self.match(TokenType.LEFT_PAREN):
                expr = self.finish_call(expr)
            if self.match(TokenType.DOT):
                name = self.consume(
                    TokenType.IDENTIFIER, "Expect property name after '.'."
                )
                expr = Get(expr, name)
            else:
                break

        return expr

    def finish_call(self, expr):
        arguments = []
        if not self.check(TokenType.RIGHT_PAREN):
            arguments.append(self.expression())
            while self.match(TokenType.COMMA):
                if len(arguments) >= 255:
                    error(self.peek(), "Can't have more than 255 arguments.")
                arguments.append(self.expression())
        paren = self.consume(TokenType.RIGHT_PAREN, "Expect ')' after arguments.")
        return Call(expr, paren, arguments)

    def primary(self) -> Expr:
        if self.match(TokenType.FALSE):
            return Literal(False)
        elif self.match(TokenType.TRUE):
            return Literal(True)
        elif self.match(TokenType.NIL):
            return Literal(None)
        elif self.match(TokenType.NUMBER, TokenType.STRING):
            return Literal(self.previous().literal)
        elif self.match(TokenType.THIS):
            return This(self.previous())
        elif self.match(TokenType.BREAK):
            return Break(self.previous(), self.loop_depth)
        elif self.match(TokenType.SUPER):
            keyword = self.previous()
            self.consume(TokenType.DOT, "Expect '.' after 'super'")
            method = self.consume(TokenType.IDENTIFIER, "Expect superclass method name")
            return Super(keyword, method)
        elif self.match(TokenType.IDENTIFIER):
            return Variable(self.previous())
        elif self.match(TokenType.LEFT_PAREN):
            expr = self.expression()
            self.consume(TokenType.RIGHT_PAREN, "Expect ')' after expression")
            return Grouping(expr)
        else:
            raise self.error(self.peek(), "Expect expression")

    def error(self, token: Token, msg: str):
        add_error(token, msg)
        return ParseError()

    def consume(self, ttype: TokenType, msg: str):
        if self.check(ttype):
            return self.advance()

        raise self.error(self.peek(), msg)

    def match(self, *tys):
        for ttype in tys:
            if self.check(ttype):
                self.advance()
                return True
        return False

    def check(self, ttype: TokenType):
        if self.is_at_end():
            return False
        else:
            return self.peek().ttype == ttype

    def advance(self):
        if not self.is_at_end():
            self.current += 1

        return self.previous()

    def is_at_end(self):
        return self.peek().ttype == TokenType.EOF

    def previous(self):
        return self.tokens[self.current - 1]

    def peek(self):
        return self.tokens[self.current]

    def synchronize(self):
        self.advance()

        while not self.is_at_end():
            if self.previous().ttype == TokenType.SEMICOLON:
                return

            if self.peek().ttype in {
                TokenType.CLASS,
                TokenType.FUN,
                TokenType.VAR,
                TokenType.FOR,
                TokenType.IF,
                TokenType.WHILE,
                TokenType.PRINT,
                TokenType.RETURN,
            }:
                return

            self.advance()
