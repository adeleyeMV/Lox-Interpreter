from typing import cast; import time
from environment import Environment
from errors import InterpretationError,runtime_error
from AstPrinter import *
from tokens import *


class ReturnException(Exception):
    def __init__(self, value):
        self.value = value

def is_truthy(value):
    if (value is None) or (value is False):
        return False

    return True

def check_operand_int(value):
    return isinstance(value, int)

def check_operant_float(value):
    return isinstance(value, float)

def is_number(value):
    return check_operand_int(value) or check_operant_float(value)


def stringify(value):
    if value is None:
        return "nil"
    elif isinstance(value, bool):
        return str(value).lower()
    elif is_number(value):
        return str(value)
    else:
        return str(value)


def is_equal(left, right):
    return left == right


def check_number_operand(token, op):
    if is_number(op):
        return
    raise InterpretationError(token, "Operand must be a number")


def check_both_number_operands(token, left, right):
    if is_number(left) and is_number(right):
        return
    raise InterpretationError(token, "Operands must be numbers")


class LoxFunction(LoxCallable):
    def __init__(
        self, declaration: Function, closure: Environment, is_initializer: bool
    ):
        self.declaration = declaration
        self.closure = closure
        self.is_initializer = is_initializer

    @property
    def arity(self) -> int:
        return len(self.declaration.params)

    def call(self, interpreter: AbstractInterpreter[Any], arguments: List[Any]) -> Any:
        local = Environment(self.closure)
        for (param, arg) in zip(self.declaration.params, arguments):
            local[param.lexeme] = arg
        try:
            interpreter.visit_statements(self.declaration.body, local)
        except ReturnException as ret:
            if self.is_initializer:
                return self.closure.get_at(0, "this")

            return ret.value

        if self.is_initializer:
            return self.closure.get_at(0, "this")

        return None

    def bind(self, instance: "LoxInstance"):
        env = Environment(self.closure)
        env["this"] = instance
        return LoxFunction(self.declaration, env, self.is_initializer)


class LoxClass(LoxCallable):
    def __init__(self, name: str, superclass: Optional["LoxClass"], methods):
        self.name = name
        self.superclass = superclass
        self.methods = methods

    def find_method(self, name: str) -> Optional[LoxFunction]:
        if name in self.methods:
            return self.methods[name]

        if self.superclass:
            return self.superclass.find_method(name)

    def __str__(self):
        return f"<class {self.name}>"

    def call(self, interpreter: AbstractInterpreter[Any], arguments: List[Any]) -> Any:
        instance = LoxInstance(self)
        initializer = self.find_method("init")
        if initializer:
            initializer.bind(instance).call(interpreter, arguments)
        return instance

    @property
    def arity(self) -> int:
        initializer = self.find_method("init")
        if initializer:
            return initializer.arity
        return 0


class LoxInstance:
    def __init__(self, klass: LoxClass):
        self.klass = klass
        self.fields = {}

    def __getitem__(self, key: Token):
        if key.lexeme in self.fields:
            return self.fields[key.lexeme]

        method = self.klass.find_method(key.lexeme)

        if method:
            return method.bind(self)

        raise InterpretationError(key, f"Undefined property '{key.lexeme}'.")

    def __setitem__(self, key: Token, value: Any):
        self.fields[key.lexeme] = value

    def __str__(self):
        return f"<instance of {self.klass.name}>"

class NativeFunction(LoxCallable):
    def __init__(self, arity, f):
        self._arity = arity
        self._f = f

    @property
    def arity(self) -> int:
        return self._arity

    def call(self, _: AbstractInterpreter[Any], arguments: List[Any]) -> Any:
        return self._f(*arguments)


def gen_globals():
    env = Environment()
    env["clock"] = NativeFunction(0, lambda: time.time())
    return env


class Interpreter(StmtVisitor[None], ExprVisitor[Any], AbstractInterpreter[Any]):
    def __init__(self):
        self.globals = gen_globals()
        self.environment = self.globals
        self.local_vars = {}
        self.breaks = False

    def visit_statements(self, stmts: List[Stmt], env: Optional[Environment] = None):
        if env is None:
            env = self.environment

        previous = self.environment

        try:
            self.environment = env
            for stmt in stmts:
                self.visit_stmt(stmt)
        except InterpretationError as err:
            runtime_error(err)
        finally:
            self.environment = previous

    def visit_stmt(self, stmt: Stmt):
        stmt.accept(self)

    def visit_expr(self, expr: Expr):
        return expr.accept(self)

    def visit_block(self, block: Block):
        self.visit_statements(block.statements, Environment(self.environment))

    def visit_print(self, print_stmt: Print):
        value = self.visit_expr(print_stmt.expression)
        print(stringify(value))

    def visit_expression(self, expr: Expression):
        return self.visit_expr(expr.expression)

    def visit_if(self, if_stmt: If):
        if is_truthy(self.visit_expr(if_stmt.condition)):
            self.visit_stmt(if_stmt.then_branch)
        elif if_stmt.else_branch:
            self.visit_stmt(if_stmt.else_branch)

    def visit_while(self, while_stmt: While):
        while is_truthy(self.visit_expr(while_stmt.condition)):
            if self.breaks:
                break
            self.visit_stmt(while_stmt.body)

    def visit_var(self, var_stmt: Var):
        value = None
        if var_stmt.initializer is not None:
            value = self.visit_expr(var_stmt.initializer)
        self.environment[var_stmt.name.lexeme] = value

    def visit_function(self, func_stmt: Function):
        self.environment[func_stmt.name.lexeme] = LoxFunction(
            func_stmt, self.environment, False
        )

    def visit_variable(self, expr: Variable) -> Any:
        return self.lookup_variable(expr.name, expr)

    def lookup_variable(self, name: Token, expr: Expr) -> Any:
        distance = self.local_vars.get(id(expr), None)
        if distance is not None:
            return self.environment.get_at(distance, name.lexeme)
        else:
            return self.globals[name]

    def visit_assign(self, expr: Assign):
        value = self.visit_expr(expr.value)
        distance = self.local_vars.get(id(expr), None)

        if distance is not None:
            self.environment.assign_at(distance, expr.name.lexeme, value)
        else:
            self.globals[expr.name.lexeme] = value
        return value

    def visit_return(self, return_stmt: Return):
        value = None
        if return_stmt.value is not None:
            value = self.visit_expr(return_stmt.value)
        raise ReturnException(value)
    
    def visit_break(self, break_stmt: Break):
        if break_stmt.loop_depth == 0:
            raise Exception("Break cannot outside loop!")
        else:
            self.breaks = True

    def visit_call(self, call_expr: Call):
        callee = self.visit_expr(call_expr.callee)
        arguments = [self.visit_expr(arg) for arg in call_expr.arguments]

        if not isinstance(callee, LoxCallable):
            raise InterpretationError(call_expr.token, f"{callee} is not callable")

        if len(arguments) != callee.arity:
            raise InterpretationError(
                call_expr.token,
                f"Expected {callee.arity} arguments, but got {len(arguments)}.",
            )

        return callee.call(self, arguments)

    def visit_literal(self, literal: Literal):
        return literal.value

    def visit_grouping(self, grouping: Grouping):
        return self.visit_expr(grouping.expression)

    def visit_unary(self, unary: Unary):
        right = self.visit_expr(unary.right)
        if unary.operator.ttype == TokenType.MINUS:
            return -right
        elif unary.operator.ttype == TokenType.BANG:
            return not is_truthy(right)
        else:
            raise InterpretationError(unary.operator, "Invalid unary operator")

    def visit_binary(self, binary: Binary):
        left = self.visit_expr(binary.left)
        right = self.visit_expr(binary.right)

        if binary.operator.ttype == TokenType.MINUS:
            check_both_number_operands(binary.operator, left, right)
            return left - right
        elif binary.operator.ttype == TokenType.SLASH:
            check_both_number_operands(binary.operator, left, right)
            if right == 0:
                raise InterpretationError(binary.operator, "Division by zero")
            return left / right
        elif binary.operator.ttype == TokenType.STAR:
            check_both_number_operands(binary.operator, left, right)
            return left * right
        elif binary.operator.ttype == TokenType.PLUS:
            if isinstance(left, str) and isinstance(right, str):
                return left + right
            check_both_number_operands(binary.operator, left, right)
            return left + right
        elif binary.operator.ttype == TokenType.GREATER:
            check_both_number_operands(binary.operator, left, right)
            return left > right
        elif binary.operator.ttype == TokenType.GREATER_EQUAL:
            check_both_number_operands(binary.operator, left, right)
            return left >= right
        elif binary.operator.ttype == TokenType.LESS:
            check_both_number_operands(binary.operator, left, right)
            return left < right
        elif binary.operator.ttype == TokenType.LESS_EQUAL:
            check_both_number_operands(binary.operator, left, right)
            return left <= right
        elif binary.operator.ttype == TokenType.BANG_EQUAL:
            return not is_equal(left, right)
        elif binary.operator.ttype == TokenType.EQUAL_EQUAL:
            return is_equal(left, right)
        else:
            raise InterpretationError(binary.operator, "Unsupported binary operator")

    def visit_logical(self, logical: Logical):
        if logical.operator.ttype == TokenType.OR:
            left = self.visit_expr(logical.left)
            if is_truthy(left):
                return left
            return self.visit_expr(logical.right)
        elif logical.operator.ttype == TokenType.AND:
            left = self.visit_expr(logical.left)
            if is_truthy(left):
                return self.visit_expr(logical.right)
            return left
        else:
            raise InterpretationError(logical.operator, "Invalid logical operator")

    def visit_class(self, stmt: Class) -> Any:
        superclass: Optional[LoxClass] = None
        if stmt.superclass:
            superclass = self.visit_expr(stmt.superclass)
            if not isinstance(superclass, LoxClass):
                raise InterpretationError(
                    stmt.superclass.name, "Superclass must be a class."
                )

        self.environment[stmt.name.lexeme] = None

        if stmt.superclass:
            self.environment = Environment(self.environment)
            self.environment["super"] = superclass

        klass = LoxClass(
            stmt.name.lexeme,
            superclass,
            {
                f.name.lexeme: LoxFunction(f, self.environment, f.name.lexeme == "init")
                for f in stmt.methods
            },
        )

        if stmt.superclass and self.environment.enclosing:
            self.environment = self.environment.enclosing

        self.environment[stmt.name.lexeme] = klass

    def visit_get(self, expr: Get) -> Any:
        instance = self.visit_expr(expr.object)

        if not isinstance(instance, LoxInstance):
            raise InterpretationError(expr.name, "Only instances have properties")

        return instance[expr.name]

    def visit_set(self, expr: Set) -> Any:
        object = self.visit_expr(expr.object)
        value = self.visit_expr(expr.value)

        if not isinstance(object, LoxInstance):
            raise InterpretationError(expr.name, "Only instances have fields")

        object[expr.name] = value
        return value

    def visit_this(self, expr: This) -> Any:
        return self.lookup_variable(expr.keyword, expr)

    def visit_super(self, expr: Super) -> Any:
        distance = self.local_vars[id(expr)]
        superclass = cast(LoxClass, self.environment.get_at(distance, "super"))
        object = cast(LoxInstance, self.environment.get_at(distance - 1, "this"))

        method = superclass.find_method(expr.method.lexeme)

        if not method:
            raise InterpretationError(
                expr.method, f"Undefined property '{expr.method.lexeme}'."
            )

        return method.bind(object)
