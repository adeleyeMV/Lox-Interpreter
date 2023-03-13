import sys,os
from pathlib import Path

from scanner import Scanner
from parsers import Parser
from interpret import Interpreter
from errors import *
from resolver import Resolver


def run(source):
    scanner = Scanner(source)
    tokens = scanner.scan_tokens()
    parser = Parser(tokens)
    result = parser.parse()

    if result is None or Globals.had_error:
        return

    interpreter = Interpreter()
    resolver = Resolver(interpreter)
    resolver.resolve_list(result)

    if Globals.had_error:
        return

    interpreter.visit_statements(result)


def run_file(f):
    run(Path(f).read_text(encoding="utf8"))
    if Globals.had_error:
        exit(65)
    if Globals.had_runtime_error:
        exit(70)


def run_prompt():
    while True:
        print("> ", end="", flush=True)
        inp = sys.stdin.readline()
        if len(inp) == 0:
            break
        run(inp)
        Globals.had_error = False

curr_file = os.getcwd()
file = os.path.basename(curr_file)
if len(sys.argv) > 2:
    print(f"Usage: {file} [script] or {file} rprompt")
    exit(64)
elif len(sys.argv) == 2 and sys.argv[1].endswith((".lox", ".pylox")):
    run_file(sys.argv[1])
elif sys.argv[0] == "rprompt":
    run_prompt()
else:
    print(f"Usage: {file} [script] or {file} rprompt")
    exit(64)
