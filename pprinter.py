from AstPrinter import *
from tokens import *


class LispPrinter(ExprVisitor[str], StmtVisitor[str]):
    def __init__(self):
        self.indent = 0

    def print_program(self, program: Program):
        return "\n".join([stmt.accept(self) for stmt in program])

    def print_indent(self, s):
        return " " * self.indent + s

    def visit_block(self, block: Block):
        s = "(block"
        if len(block.statements) > 0:
            self.indent += 4
            s += "\n" + "\n".join(
                [self.print_indent(stmt.accept(self)) for stmt in block.statements]
            )
            self.indent -= 4
        s += ")"
        return s

    def visit_assign(self, expr: Assign) -> str:
        return f"(assign {expr.name.lexeme} {expr.value.accept(self)})"

    def visit_binary(self, expr: Binary) -> str:
        return f"({expr.operator.lexeme} {expr.left.accept(self)} {expr.right.accept(self)})"

    def visit_grouping(self, expr: Grouping) -> str:
        return f"(grouping {expr.expression.accept(self)})"

    def visit_literal(self, expr: Literal) -> str:
        if expr.value is None:
            return "nil"
        elif expr.value is True:
            return "true"
        elif expr.value is False:
            return "false"
        elif isinstance(expr.value, str):
            return f'"{expr.value}"'
        else:
            return str(expr.value)

    def visit_unary(self, expr: Unary) -> str:
        return f"({expr.operator} {expr.right.accept(self)})"

    def visit_variable(self, expr: Variable) -> str:
        return expr.name.lexeme

    def visit_print(self, expr: Print) -> str:
        return f"(print {expr.expression.accept(self)})"

    def visit_call(self, expr: Call) -> str:
        s = f"(call {expr.callee.accept(self)}"
        if len(expr.arguments) > 0:
            self.indent += 4
            s += "\n" + "\n".join(
                [self.print_indent(arg.accept(self)) for arg in expr.arguments]
            )
            self.indent -= 4
        s += ")"
        return s

    def visit_expression(self, stmt: Expression) -> str:
        return stmt.expression.accept(self)

    def visit_function(self, stmt: Function) -> str:
        s = f'(func {stmt.name.lexeme} ({" ".join([arg.lexeme for arg in stmt.params])})'
        self.indent += 4
        s += "\n" + "\n".join([self.print_indent(s.accept(self)) for s in stmt.body])
        self.indent -= 4
        s += ")"
        return s

    def visit_if(self, stmt: If) -> str:
        s = f"(if {stmt.condition.accept(self)}"
        self.indent += 4
        s += "\n" + self.print_indent(stmt.then_branch.accept(self))
        self.indent -= 4
        if stmt.else_branch:
            s += "\n" + self.print_indent(stmt.else_branch.accept(self))
        s += ")"
        return s

    def visit_while(self, stmt: While) -> str:
        s = f"(while {stmt.condition.accept(self)}"
        self.indent += 4
        s += "\n" + self.print_indent(stmt.body.accept(self))
        self.indent -= 4
        s += ")"
        return s

    def visit_return(self, stmt: Return) -> str:
        if stmt.value:
            return f"(return {stmt.value.accept(self)})"
        else:
            return "(return)"
        
    def visit_break(self, stmt: Break):
        return "(break)"

    def visit_logical(self, expr: Logical) -> str:
        left = expr.left.accept(self)
        right = expr.right.accept(self)
        return f"({expr.operator.lexeme} {left} {right})"

    def visit_var(self, stmt: Var) -> str:
        if stmt.initializer:
            return f"(var {stmt.name.lexeme} {stmt.initializer.accept(self)})"
        else:
            return f"(var {stmt.name.lexeme})"

    def visit_class(self, stmt: Class) -> str:
        s = f"(class {stmt.name.lexeme}"

        if stmt.superclass:
            s += f" (< {stmt.superclass.name.lexeme})"

        if len(stmt.methods) > 0:
            self.indent += 4
            s += "\n" + "\n".join(
                [self.print_indent(s.accept(self)) for s in stmt.methods]
            )
            self.indent -= 4
        s += ")"
        return s

    def visit_get(self, expr: Get) -> str:
        return f"(get {expr.object.accept(self)} {expr.name.lexeme})"

    def visit_set(self, expr: Set) -> str:
        object = expr.object.accept(self)
        value = expr.value.accept(self)
        return f"(set {object} {expr.name.lexeme} {value})"

    def visit_this(self, _: This) -> str:
        return f"this"

    def visit_super(self, expr: Super) -> str:
        return f"({expr.keyword.lexeme} {expr.method.lexeme})"
