from AstPrinter import *
from collections import deque
from errors import add_error, error
from enum import Enum, auto


class FunctionType(Enum):
    NONE = auto()
    FUNCTION = auto()
    METHOD = auto()
    INITIALIZER = auto()


class ClassType(Enum):
    NONE = auto()
    CLASS = auto()
    SUBCLASS = auto()


class Resolver(StmtVisitor[None], ExprVisitor[None]):
    def __init__(self, interpreter):
        self.scopes = deque()
        self.interpreter = interpreter
        self.current_function = FunctionType.NONE
        self.current_class = ClassType.NONE

    def begin_scope(self):
        self.scopes.append({})

    def end_scope(self):
        self.scopes.pop()

    def declare(self, name: Token) -> None:
        if len(self.scopes) == 0:
            return
        scope = self.scopes[-1]

        if name.lexeme in scope:
            add_error(name, "Variable with this name already declared in this scope.")

        scope[name.lexeme] = False

    def define(self, name: Token) -> None:
        if len(self.scopes) == 0:
            return
        self.scopes[-1][name.lexeme] = True

    def resolve_local(self, expr: Expr, name: Token) -> None:
        for i, scope in enumerate(reversed(self.scopes)):
            if name.lexeme in scope:
                self.interpreter.local_vars[id(expr)] = i
                return

    def resolve_list(self, statements: List[Stmt]):
        for statement in statements:
            statement.accept(self)

    def resolve_function(self, func: Function, function_type: FunctionType) -> None:
        enclosing_function = self.current_function
        self.current_function = function_type

        self.begin_scope()
        for param in func.params:
            self.declare(param)
            self.define(param)
        self.resolve_list(func.body)
        self.end_scope()

        self.current_function = enclosing_function

    def visit_block(self, stmt: Block) -> None:
        self.begin_scope()
        self.resolve_list(stmt.statements)
        self.end_scope()

    def resolve_stmt(self, stmt: Stmt) -> None:
        stmt.accept(self)

    def resolve_expr(self, expr: Expr) -> None:
        expr.accept(self)

    def visit_var(self, stmt: Var) -> None:
        self.declare(stmt.name)
        if stmt.initializer:
            self.resolve_expr(stmt.initializer)
        self.define(stmt.name)

    def visit_variable(self, expr: Variable) -> None:
        if self.scopes and self.scopes[-1].get(expr.name.lexeme) is False:
            add_error(expr.name, "Cannot read local variable in its own initializer.")
        self.resolve_local(expr, expr.name)

    def visit_assign(self, expr: Assign) -> None:
        self.resolve_expr(expr.value)
        self.resolve_local(expr, expr.name)

    def visit_function(self, func: Function) -> None:
        self.declare(func.name)
        self.define(func.name)

        self.resolve_function(func, FunctionType.FUNCTION)

    def visit_expression(self, expr: Expression) -> None:
        self.resolve_expr(expr.expression)

    def visit_if(self, stmt: If) -> None:
        self.resolve_expr(stmt.condition)
        self.resolve_stmt(stmt.then_branch)
        if stmt.else_branch:
            self.resolve_stmt(stmt.else_branch)

    def visit_print(self, stmt: Print) -> None:
        self.resolve_expr(stmt.expression)

    def visit_return(self, stmt: Return) -> None:
        if self.current_function == FunctionType.NONE:
            add_error(stmt.keyword, "Cannot return from top-level code.")

        if stmt.value:
            if self.current_function == FunctionType.INITIALIZER:
                add_error(stmt.keyword, "Can't return a value from an initializer.")

            self.resolve_expr(stmt.value)
            
    def visit_break(self, stmt: Break) -> None:
        if stmt.loop_depth == 0:
            add_error(stmt.keyword, "Break statement must be inside loop!")
        else:
            pass

    def visit_while(self, stmt: While) -> None:
        self.resolve_expr(stmt.condition)
        self.resolve_stmt(stmt.body)

    def visit_binary(self, expr: Binary) -> None:
        self.resolve_expr(expr.left)
        self.resolve_expr(expr.right)

    def visit_call(self, expr: Call) -> None:
        self.resolve_expr(expr.callee)
        for arg in expr.arguments:
            self.resolve_expr(arg)

    def visit_grouping(self, expr: Grouping) -> None:
        self.resolve_expr(expr.expression)

    def visit_literal(self, _: Literal) -> None:
        pass

    def visit_logical(self, expr: Logical) -> None:
        self.resolve_expr(expr.left)
        self.resolve_expr(expr.right)

    def visit_unary(self, expr: Unary) -> None:
        self.resolve_expr(expr.right)

    def visit_class(self, stmt: Class) -> None:
        enclosing = self.current_class
        self.current_class = ClassType.CLASS

        self.declare(stmt.name)
        self.define(stmt.name)

        if stmt.superclass:
            self.current_class = ClassType.SUBCLASS
            self.resolve_expr(stmt.superclass)
            if stmt.superclass.name.lexeme == stmt.name.lexeme:
                add_error(stmt.superclass.name, "A class can't inherit from itself")

            self.begin_scope()
            self.scopes[-1]["super"] = True

        self.begin_scope()
        self.scopes[-1]["this"] = True

        for method in stmt.methods:
            declaration = FunctionType.METHOD
            if method.name.lexeme == "init":
                declaration = FunctionType.INITIALIZER
            self.resolve_function(method, declaration)

        if stmt.superclass:
            self.end_scope()

        self.end_scope()
        self.current_class = enclosing

    def visit_get(self, expr: Get) -> None:
        self.resolve_expr(expr.object)

    def visit_set(self, expr: Set) -> None:
        self.resolve_expr(expr.object)
        self.resolve_expr(expr.value)

    def visit_this(self, expr: This) -> None:
        if self.current_class == ClassType.NONE:
            add_error(expr.keyword, "Can't use 'this' outside of a class.")

        self.resolve_local(expr, expr.keyword)

    def visit_super(self, expr: Super) -> None:
        if self.current_class == ClassType.NONE:
            add_error(expr.keyword, "Can't use 'super' outside of a class.")
        elif self.current_class != ClassType.SUBCLASS:
            add_error(expr.keyword, "Can't use 'super' in a class with no superclass.")

        self.resolve_local(expr, expr.keyword)
