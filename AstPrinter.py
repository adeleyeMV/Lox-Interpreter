from dataclasses import dataclass
from typing import Any, List, Generic, Optional, TypeVar, Union
import abc
from environment import Environment

from tokens import Token

Expr = Union[
    "Binary",
    "Grouping",
    "Literal",
    "Unary",
    "Call",
    "Variable",
    "Assign",
    "Logical",
    "Get",
    "Set",
    "This",
    "Super",
]

Stmt = Union[
    "Expression",
    "If",
    "Print",
    "While",
    "Var",
    "Block",
    "Function",
]

Program = List[Stmt]

T = TypeVar("T")


@dataclass
class Expression:
    expression: Expr

    def accept(self, visitor: "StmtVisitor[T]") -> T:
        return visitor.visit_expression(self)


@dataclass
class Class:
    name: Token
    superclass: Optional["Variable"]
    methods: List["Function"]

    def accept(self, visitor: "StmtVisitor[T]") -> T:
        return visitor.visit_class(self)


@dataclass
class If:
    condition: Expr
    then_branch: Stmt
    else_branch: Optional[Stmt]

    def accept(self, visitor: "StmtVisitor[T]") -> T:
        return visitor.visit_if(self)


@dataclass
class Print:
    expression: Expr

    def accept(self, visitor: "StmtVisitor[T]") -> T:
        return visitor.visit_print(self)


@dataclass
class While:
    condition: Expr
    body: Stmt

    def accept(self, visitor: "StmtVisitor[T]") -> T:
        return visitor.visit_while(self)


@dataclass
class Var:
    name: Token
    initializer: Optional[Expr]

    def accept(self, visitor: "StmtVisitor[T]") -> T:
        return visitor.visit_var(self)


@dataclass
class Block:
    statements: List[Stmt]

    def accept(self, visitor: "StmtVisitor[T]") -> T:
        return visitor.visit_block(self)


@dataclass
class Function:
    name: Token
    params: List[Token]
    body: List[Stmt]

    def accept(self, visitor: "StmtVisitor[T]") -> T:
        return visitor.visit_function(self)


@dataclass
class Return:
    keyword: Token
    value: Optional[Expr]

    def accept(self, visitor: "StmtVisitor[T]") -> T:
        return visitor.visit_return(self)
    
@dataclass
class Break:
    keyword: Token
    loop_depth: Optional[Expr]
    def accept(self, visitor: "StmtVisitor"):
        return visitor.visit_break(self)


@dataclass
class Binary:
    left: Expr
    operator: Token
    right: Expr

    def accept(self, visitor: "ExprVisitor[T]") -> T:
        return visitor.visit_binary(self)


@dataclass
class Logical:
    left: Expr
    operator: Token
    right: Expr

    def accept(self, visitor: "ExprVisitor[T]") -> T:
        return visitor.visit_logical(self)


@dataclass
class Grouping:
    expression: Expr

    def accept(self, visitor: "ExprVisitor[T]") -> T:
        return visitor.visit_grouping(self)


@dataclass
class Literal:
    value: Any

    def accept(self, visitor: "ExprVisitor[T]") -> T:
        return visitor.visit_literal(self)


@dataclass
class Variable:
    name: Token

    def accept(self, visitor: "ExprVisitor[T]") -> T:
        return visitor.visit_variable(self)


@dataclass
class Unary:
    operator: Token
    right: Expr

    def accept(self, visitor: "ExprVisitor[T]") -> T:
        return visitor.visit_unary(self)


@dataclass
class Call:
    callee: Expr
    token: Token
    arguments: List[Expr]

    def accept(self, visitor: "ExprVisitor[T]") -> T:
        return visitor.visit_call(self)


@dataclass
class Assign:
    name: Token
    value: Expr

    def accept(self, visitor: "ExprVisitor[T]") -> T:
        return visitor.visit_assign(self)


@dataclass
class Set:
    object: Expr
    name: Token
    value: Expr

    def accept(self, visitor: "ExprVisitor[T]") -> T:
        return visitor.visit_set(self)


@dataclass
class Get:
    object: Expr
    name: Token

    def accept(self, visitor: "ExprVisitor[T]") -> T:
        return visitor.visit_get(self)


@dataclass
class This:
    keyword: Token

    def accept(self, visitor: "ExprVisitor[T]") -> T:
        return visitor.visit_this(self)


@dataclass
class Super:
    keyword: Token
    method: Token

    def accept(self, visitor: "ExprVisitor[T]") -> T:
        return visitor.visit_super(self)


class AbstractInterpreter(Generic[T]):
    @abc.abstractmethod
    def visit_statements(
        self, stmts: List[Stmt], env: Optional[Environment] = None
    ) -> T:
        pass


class LoxCallable(abc.ABC):
    @abc.abstractmethod
    def call(self, interpreter: AbstractInterpreter[Any], arguments: List[Any]) -> Any:
        raise NotImplementedError

    @property
    @abc.abstractmethod
    def arity(self) -> int:
        raise NotImplementedError


class StmtVisitor(abc.ABC, Generic[T]):
    @abc.abstractmethod
    def visit_expression(self, stmt: Expression) -> T:
        pass

    @abc.abstractmethod
    def visit_if(self, stmt: If) -> T:
        pass

    @abc.abstractmethod
    def visit_print(self, stmt: Print) -> T:
        pass

    @abc.abstractmethod
    def visit_while(self, stmt: While) -> T:
        pass

    @abc.abstractmethod
    def visit_var(self, stmt: Var) -> T:
        pass

    @abc.abstractmethod
    def visit_block(self, stmt: Block) -> T:
        pass

    @abc.abstractmethod
    def visit_function(self, stmt: Function) -> T:
        pass

    @abc.abstractmethod
    def visit_return(self, stmt: Return) -> T:
        pass
    
    @abc.abstractmethod
    def visit_break(self, stmt: Break):
        pass

    @abc.abstractmethod
    def visit_class(self, stmt: Class) -> T:
        pass


class ExprVisitor(abc.ABC, Generic[T]):
    @abc.abstractmethod
    def visit_binary(self, expr: Binary) -> T:
        pass

    @abc.abstractmethod
    def visit_grouping(self, expr: Grouping) -> T:
        pass

    @abc.abstractmethod
    def visit_literal(self, expr: Literal) -> T:
        pass

    @abc.abstractmethod
    def visit_unary(self, expr: Unary) -> T:
        pass

    @abc.abstractmethod
    def visit_call(self, expr: Call) -> T:
        pass

    @abc.abstractmethod
    def visit_variable(self, expr: Variable) -> T:
        pass

    @abc.abstractmethod
    def visit_assign(self, expr: Assign) -> T:
        pass

    @abc.abstractmethod
    def visit_logical(self, expr: Logical) -> T:
        pass

    @abc.abstractmethod
    def visit_set(self, expr: Set) -> T:
        pass

    @abc.abstractmethod
    def visit_get(self, expr: Get) -> T:
        pass

    @abc.abstractmethod
    def visit_this(self, expr: This) -> T:
        pass

    @abc.abstractmethod
    def visit_super(self, expr: Super) -> T:
        pass
