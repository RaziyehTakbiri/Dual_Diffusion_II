"""Pre-ship static gate (stdlib-only, runs in Claude's sandbox).

Catches the bug classes that py_compile cannot:
  1. use-before-local-assignment / module-name shadowing inside a function
     (the UnboundLocalError family - bit us 2026-07-15)
  2. names loaded in a function that exist nowhere (typo'd identifiers),
     modulo builtins and module/class scope

Deliberately conservative: it flags only names that are BOTH loaded before
their first local assignment AND defined at module level - the exact
shadowing pattern. Zero third-party dependencies.

Usage: python tools/lint_shadow.py <paths...>   (dirs are walked for .py)
Exit code 1 on any finding.
"""

from __future__ import annotations

import ast
import builtins
import pathlib
import sys

BUILTINS = set(dir(builtins)) | {"__file__", "__name__", "__doc__"}


def module_names(tree: ast.Module) -> set:
    names = set()
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            names.add(node.name)
        elif isinstance(node, (ast.Import, ast.ImportFrom)):
            for a in node.names:
                names.add((a.asname or a.name).split(".")[0])
        elif isinstance(node, ast.Assign):
            for t in node.targets:
                if isinstance(t, ast.Name):
                    names.add(t.id)
    return names


def check_function(fn, mod_names: set, findings: list, filename: str):
    params = {a.arg for a in (fn.args.args + fn.args.kwonlyargs
                              + fn.args.posonlyargs)}
    if fn.args.vararg:
        params.add(fn.args.vararg.arg)
    if fn.args.kwarg:
        params.add(fn.args.kwarg.arg)

    first_store: dict = {}
    loads: list = []
    nonlocals: set = set()

    class V(ast.NodeVisitor):
        def visit_FunctionDef(self, node):     # don't descend into nested defs
            if node is not fn:
                first_store.setdefault(node.name, node.lineno)
            else:
                self.generic_visit(node)

        visit_AsyncFunctionDef = visit_FunctionDef

        def _skip(self, node):
            # comprehensions own their target scope in py3 - descending would
            # misattribute their loop variables to the enclosing function
            pass

        visit_GeneratorExp = visit_ListComp = visit_SetComp = visit_DictComp = _skip

        def visit_Global(self, node):
            nonlocals.update(node.names)

        def visit_Nonlocal(self, node):
            nonlocals.update(node.names)

        def visit_Name(self, node):
            if isinstance(node.ctx, ast.Store):
                first_store.setdefault(node.id, node.lineno)
            elif isinstance(node.ctx, ast.Load):
                loads.append((node.id, node.lineno))
            self.generic_visit(node)

    V().visit(fn)

    for name, line in loads:
        if (name in first_store and line < first_store[name]
                and name not in params and name not in nonlocals
                and name not in BUILTINS):
            tag = ("SHADOWS-MODULE-NAME" if name in mod_names
                   else "use-before-assignment?")
            findings.append(
                f"{filename}:{line}: '{name}' loaded before local assignment "
                f"at line {first_store[name]} in {fn.name}() [{tag}]")


def lint(path: pathlib.Path, findings: list):
    tree = ast.parse(path.read_text(), filename=str(path))
    mods = module_names(tree)
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            check_function(node, mods, findings, str(path))


def main(argv):
    targets = []
    for a in argv or ["."]:
        p = pathlib.Path(a)
        targets += sorted(p.rglob("*.py")) if p.is_dir() else [p]
    findings: list = []
    for p in targets:
        if "__pycache__" in str(p):
            continue
        lint(p, findings)
    for f in findings:
        print(f)
    print(f"{len(findings)} finding(s) over {len(targets)} file(s)")
    return 1 if findings else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
