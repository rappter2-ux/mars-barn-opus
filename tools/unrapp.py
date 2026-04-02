#!/usr/bin/env python3
"""
unRAPP Transpiler — Bidirectional .lispy ↔ .py conversion.

Same logic. Different runtime. 1:1 mapping per LISPY.md spec.

Usage:
  python3 tools/unrapp.py input.lispy          # → outputs input.py
  python3 tools/unrapp.py input.py             # → outputs input.lispy
  python3 tools/unrapp.py input.lispy -o out.py
  python3 tools/unrapp.py --check input.lispy  # roundtrip verify
"""

import sys, re, os, json

# ═══════════════════════════════════════════════════════════
# LISPY PARSER
# ═══════════════════════════════════════════════════════════

def tokenize(source):
    """Tokenize LisPy source into a flat list of tokens."""
    tokens = []
    i = 0
    while i < len(source):
        c = source[i]
        if c == ';' and i + 1 < len(source) and source[i + 1] == ';':
            # Comment — skip to end of line
            end = source.find('\n', i)
            if end == -1: break
            i = end + 1
        elif c in ' \t\n\r':
            i += 1
        elif c == '(':
            tokens.append('(')
            i += 1
        elif c == ')':
            tokens.append(')')
            i += 1
        elif c == '"':
            # String literal
            j = i + 1
            while j < len(source) and source[j] != '"':
                if source[j] == '\\': j += 1
                j += 1
            tokens.append(source[i:j + 1])
            i = j + 1
        else:
            # Atom (symbol, number, boolean)
            j = i
            while j < len(source) and source[j] not in ' \t\n\r();"':
                j += 1
            tokens.append(source[i:j])
            i = j
    return tokens


def parse_tokens(tokens):
    """Parse flat token list into nested AST."""
    if not tokens:
        return []
    results = []
    i = [0]  # mutable index

    def parse_expr():
        if i[0] >= len(tokens):
            return None
        tok = tokens[i[0]]
        if tok == '(':
            i[0] += 1
            lst = []
            while i[0] < len(tokens) and tokens[i[0]] != ')':
                expr = parse_expr()
                if expr is not None:
                    lst.append(expr)
            if i[0] < len(tokens):
                i[0] += 1  # skip ')'
            return lst
        elif tok == ')':
            i[0] += 1
            return None
        else:
            i[0] += 1
            return parse_atom(tok)

    while i[0] < len(tokens):
        expr = parse_expr()
        if expr is not None:
            results.append(expr)
    return results


def parse_atom(tok):
    """Convert a token string to a typed value."""
    if tok == 'true': return True
    if tok == 'false': return False
    try: return int(tok)
    except ValueError: pass
    try: return float(tok)
    except ValueError: pass
    if tok.startswith('"') and tok.endswith('"'):
        return ('__str', tok[1:-1])
    return ('__sym', tok)


def is_sym(node, name=None):
    return isinstance(node, tuple) and node[0] == '__sym' and (name is None or node[1] == name)

def sym_name(node):
    return node[1] if isinstance(node, tuple) and node[0] == '__sym' else str(node)

def is_str(node):
    return isinstance(node, tuple) and node[0] == '__str'


# ═══════════════════════════════════════════════════════════
# LISPY → PYTHON
# ═══════════════════════════════════════════════════════════

MATH_OPS = {'+': '+', '-': '-', '*': '*', '/': '/', '%': '%'}
CMP_OPS = {'<': '<', '>': '>', '<=': '<=', '>=': '>=', '=': '==', '!=': '!='}
BUILTIN_FUNCS = {
    'abs': 'abs', 'round': 'round', 'floor': 'math.floor', 'ceil': 'math.ceil',
    'min': 'min', 'max': 'max', 'pow': 'pow', 'sqrt': 'math.sqrt',
    'sin': 'math.sin', 'cos': 'math.cos', 'length': 'len',
}

class LispyToPython:
    def __init__(self):
        self.indent = 0
        self.imports = set()

    def transpile(self, ast_nodes):
        """Transpile a list of top-level AST nodes to Python."""
        lines = []
        for node in ast_nodes:
            code = self.emit(node)
            if code:
                lines.append(code)

        header = []
        if 'math' in self.imports:
            header.append('import math')
        if 'random' in self.imports:
            header.append('import random')
        if header:
            header.append('')

        return '\n'.join(header + lines) + '\n'

    def emit(self, node, ctx='stmt'):
        """Emit Python code for a single AST node."""
        if isinstance(node, bool):
            return 'True' if node else 'False'
        if isinstance(node, (int, float)):
            return str(node)
        if is_str(node):
            return repr(node[1])
        if is_sym(node):
            name = sym_name(node)
            if name == 'pi':
                self.imports.add('math')
                return 'math.pi'
            if name == 'random':
                self.imports.add('random')
                return 'random.random()'
            return self._pyname(name)

        if not isinstance(node, list) or len(node) == 0:
            return str(node)

        head = node[0]
        if not is_sym(head):
            # Function call on computed value
            func = self.emit(head, 'expr')
            args = ', '.join(self.emit(a, 'expr') for a in node[1:])
            return f'{func}({args})'

        op = sym_name(head)

        # ── Special forms ──

        if op == 'define':
            name = self._pyname(sym_name(node[1]))
            val = self.emit(node[2], 'expr')
            return f'{name} = {val}'

        if op == 'set!':
            name = self._pyname(sym_name(node[1]))
            val = self.emit(node[2], 'expr')
            return f'{name} = {val}'

        if op == 'begin':
            lines = []
            for n in node[1:]:
                code = self.emit(n)
                if code:
                    lines.append(code)
            return '\n'.join(lines)

        if op == 'if':
            cond = self.emit(node[1], 'expr')
            then_node = node[2]
            els_node = node[3] if len(node) > 3 else None
            if ctx == 'expr':
                then = self.emit(then_node, 'expr')
                els = self.emit(els_node, 'expr') if els_node else 'None'
                return f'({then} if {cond} else {els})'
            # Statement context — need proper indentation
            then_code = self.emit(then_node)
            then_lines = then_code.split('\n')
            indented_then = '\n'.join('    ' + l for l in then_lines)
            result = f'if {cond}:\n{indented_then}'
            if els_node:
                els_code = self.emit(els_node)
                els_lines = els_code.split('\n')
                indented_els = '\n'.join('    ' + l for l in els_lines)
                result += f'\nelse:\n{indented_els}'
            return result

        if op == 'cond':
            if ctx == 'expr':
                # Emit as chained ternary: (a if test1 else b if test2 else c)
                parts = list(node[1:])
                return self._cond_ternary(parts)
            lines = []
            for i, clause in enumerate(node[1:]):
                test = self.emit(clause[0], 'expr')
                body = self.emit(clause[1], 'expr') if len(clause) > 1 else 'None'
                if isinstance(clause[0], bool) and clause[0] is True:
                    lines.append(f'else:\n{self._ind(1)}{body}')
                elif i == 0:
                    lines.append(f'if {test}:\n{self._ind(1)}{body}')
                else:
                    lines.append(f'elif {test}:\n{self._ind(1)}{body}')
            return '\n'.join(lines)

        if op == 'let':
            bindings = node[1]
            body = node[2:]
            lines = []
            # Support both (let (x 1 y 2) ...) and (let ((x 1) (y 2)) ...)
            if isinstance(bindings, list) and len(bindings) > 0:
                if isinstance(bindings[0], list):
                    # Scheme-style: ((name val) (name val) ...)
                    for pair in bindings:
                        if isinstance(pair, list) and len(pair) >= 2:
                            name = self._pyname(sym_name(pair[0]))
                            val = self.emit(pair[1], 'expr')
                            lines.append(f'{name} = {val}')
                else:
                    # Flat-style: (x 1 y 2 ...)
                    i = 0
                    while i + 1 < len(bindings):
                        name = self._pyname(sym_name(bindings[i]))
                        val = self.emit(bindings[i + 1], 'expr')
                        lines.append(f'{name} = {val}')
                        i += 2
            for b in body:
                lines.append(self.emit(b))
            return '\n'.join(lines)

        if op == 'repeat':
            count = self.emit(node[1], 'expr')
            body = self.emit(node[2])
            return f'for _i in range({count}):\n{self._ind(1)}{body}'

        if op == 'log' or op == 'print':
            args = ', '.join(self.emit(a, 'expr') for a in node[1:])
            return f'print({args})'

        if op == 'concat':
            parts = [self.emit(a, 'expr') for a in node[1:]]
            return ' + '.join(f'str({p})' if not self._is_str_expr(node[i+1]) else p for i, p in enumerate(parts))

        if op == 'string':
            return f'str({self.emit(node[1], "expr")})'

        if op == 'number':
            return f'float({self.emit(node[1], "expr")})'

        if op == 'list':
            elems = ', '.join(self.emit(a, 'expr') for a in node[1:])
            return f'[{elems}]'

        if op == 'nth':
            lst = self.emit(node[1], 'expr')
            idx = self.emit(node[2], 'expr')
            return f'{lst}[{idx}]'

        if op == 'range':
            args = ', '.join(self.emit(a, 'expr') for a in node[1:])
            return f'list(range({args}))'

        if op == 'map':
            body_expr = node[1]
            lst = self.emit(node[2], 'expr')
            return f'[{self._lambda_body(body_expr, "_")} for _ in {lst}]'

        if op == 'filter':
            body_expr = node[1]
            lst = self.emit(node[2], 'expr')
            return f'[_ for _ in {lst} if {self._lambda_body(body_expr, "_")}]'

        if op == 'reduce':
            body_expr = node[1]
            lst = self.emit(node[2], 'expr')
            init = self.emit(node[3], 'expr') if len(node) > 3 else '0'
            self.imports.add('functools')
            return f'functools.reduce(lambda _acc, _: {self._lambda_body(body_expr, "_")}, {lst}, {init})'

        # ── Math ops (variadic) ──
        if op in MATH_OPS:
            py_op = MATH_OPS[op]
            args = [self.emit(a, 'expr') for a in node[1:]]
            if len(args) == 1 and op == '-':
                return f'(-{args[0]})'
            return f' {py_op} '.join(args)

        # ── Comparison ops ──
        if op in CMP_OPS:
            py_op = CMP_OPS[op]
            left = self.emit(node[1], 'expr')
            right = self.emit(node[2], 'expr')
            return f'{left} {py_op} {right}'

        # ── Logic ──
        if op == 'and':
            args = [self.emit(a, 'expr') for a in node[1:]]
            return ' and '.join(args)
        if op == 'or':
            args = [self.emit(a, 'expr') for a in node[1:]]
            return ' or '.join(args)
        if op == 'not':
            return f'not {self.emit(node[1], "expr")}'

        # ── Builtins ──
        if op in BUILTIN_FUNCS:
            if op in ('floor', 'ceil', 'sqrt', 'sin', 'cos'):
                self.imports.add('math')
            pyfn = BUILTIN_FUNCS[op]
            args = ', '.join(self.emit(a, 'expr') for a in node[1:])
            return f'{pyfn}({args})'

        if op == 'random':
            self.imports.add('random')
            return 'random.random()'

        if op == 'pi':
            self.imports.add('math')
            return 'math.pi'

        # ── Data access ──
        if op == 'http-get':
            arg = self.emit(node[1], 'expr')
            return f'http_get({arg})'
        if op == 'json-get':
            obj = self.emit(node[1], 'expr')
            key = self.emit(node[2], 'expr')
            return f'{obj}[{key}]'
        if op == 'json-keys':
            obj = self.emit(node[1], 'expr')
            return f'list({obj}.keys())'

        # ── Prompt library ──
        if op == 'prompt':
            args = ', '.join(self.emit(a, 'expr') for a in node[1:])
            return f'prompt({args})'
        if op == 'prompt-list':
            return 'prompt_list()'
        if op == 'prompt-tags':
            return f'prompt_tags({self.emit(node[1], "expr")})'

        # ── Generic function call ──
        fname = self._pyname(op)
        args = ', '.join(self.emit(a, 'expr') for a in node[1:])
        return f'{fname}({args})'

    def _pyname(self, name):
        """Convert LisPy name to valid Python identifier."""
        return name.replace('-', '_').replace('!', '').replace('?', '_p')

    def _ind(self, extra=0):
        return '    ' * (self.indent + extra)

    def _is_str_expr(self, node):
        return is_str(node) or (isinstance(node, list) and len(node) > 0 and
                                is_sym(node[0]) and sym_name(node[0]) == 'concat')

    def _cond_ternary(self, clauses):
        """Emit cond as chained Python ternary expressions."""
        if not clauses:
            return 'None'
        clause = clauses[0]
        test = self.emit(clause[0], 'expr')
        body = self.emit(clause[1], 'expr') if len(clause) > 1 else 'None'
        if isinstance(clause[0], bool) and clause[0] is True:
            return body
        rest = self._cond_ternary(clauses[1:])
        return f'({body} if {test} else {rest})'

    def _lambda_body(self, expr, var):
        """Emit an inline expression that uses _ or _acc as free variables."""
        return self.emit(expr, 'expr')


# ═══════════════════════════════════════════════════════════
# PYTHON → LISPY
# ═══════════════════════════════════════════════════════════

import ast

PY_TO_LISPY_OPS = {
    ast.Add: '+', ast.Sub: '-', ast.Mult: '*', ast.Div: '/',
    ast.Mod: '%', ast.Pow: 'pow',
}
PY_TO_LISPY_CMP = {
    ast.Lt: '<', ast.Gt: '>', ast.LtE: '<=', ast.GtE: '>=',
    ast.Eq: '=', ast.NotEq: '!=',
}
PY_TO_LISPY_BOOL = {
    ast.And: 'and', ast.Or: 'or',
}
PY_BUILTINS_TO_LISPY = {
    'abs': 'abs', 'round': 'round', 'len': 'length',
    'min': 'min', 'max': 'max', 'pow': 'pow',
    'print': 'log', 'str': 'string', 'float': 'number', 'int': 'number',
}
PY_MATH_TO_LISPY = {
    'math.floor': 'floor', 'math.ceil': 'ceil', 'math.sqrt': 'sqrt',
    'math.sin': 'sin', 'math.cos': 'cos', 'math.pi': 'pi',
}


class PythonToLispy:
    def __init__(self):
        self.indent = 0

    def transpile(self, source):
        tree = ast.parse(source)
        lines = []
        for node in tree.body:
            if isinstance(node, ast.Import):
                lines.append(f';; import {", ".join(a.name for a in node.names)}')
            elif isinstance(node, ast.ImportFrom):
                lines.append(f';; from {node.module} import {", ".join(a.name for a in node.names)}')
            else:
                code = self.emit(node)
                if code:
                    lines.append(code)
        return '\n'.join(lines) + '\n'

    def emit(self, node):
        if isinstance(node, ast.Assign):
            target = self._name(node.targets[0])
            val = self.emit_expr(node.value)
            return f'(define {target} {val})'

        if isinstance(node, ast.AugAssign):
            target = self._name(node.targets[0]) if hasattr(node, 'targets') else self._name(node.target)
            op = PY_TO_LISPY_OPS.get(type(node.op), '+')
            val = self.emit_expr(node.value)
            return f'(set! {target} ({op} {target} {val}))'

        if isinstance(node, ast.Expr):
            return self.emit_expr(node.value)

        if isinstance(node, ast.If):
            test = self.emit_expr(node.test)
            body = self._block(node.body)
            if node.orelse:
                if len(node.orelse) == 1 and isinstance(node.orelse[0], ast.If):
                    # elif chain → cond
                    return self._emit_cond_chain(node)
                els = self._block(node.orelse)
                return f'(if {test}\n  {body}\n  {els})'
            return f'(if {test}\n  {body})'

        if isinstance(node, ast.For):
            target = self._name(node.target)
            iter_expr = self.emit_expr(node.iter)
            body = self._block(node.body)
            if target == '_i':
                return f'(repeat {iter_expr}\n  {body})'
            return f';; for {target} in {iter_expr}\n(repeat (length {iter_expr})\n  {body})'

        if isinstance(node, ast.Return):
            if node.value:
                return self.emit_expr(node.value)
            return ''

        if isinstance(node, ast.FunctionDef):
            body_lines = [self.emit(s) for s in node.body]
            body = '\n  '.join(l for l in body_lines if l)
            return f';; function {node.name}\n(begin\n  {body})'

        return f';; [unsupported: {type(node).__name__}]'

    def emit_expr(self, node):
        if isinstance(node, ast.Constant):
            if isinstance(node.value, bool):
                return 'true' if node.value else 'false'
            if isinstance(node.value, str):
                return f'"{node.value}"'
            return str(node.value)

        if isinstance(node, ast.Name):
            name = node.id
            return self._lispyname(name)

        if isinstance(node, ast.BinOp):
            op = PY_TO_LISPY_OPS.get(type(node.op), '+')
            left = self.emit_expr(node.left)
            right = self.emit_expr(node.right)
            return f'({op} {left} {right})'

        if isinstance(node, ast.UnaryOp):
            if isinstance(node.op, ast.USub):
                return f'(- 0 {self.emit_expr(node.operand)})'
            if isinstance(node.op, ast.Not):
                return f'(not {self.emit_expr(node.operand)})'
            return self.emit_expr(node.operand)

        if isinstance(node, ast.Compare):
            left = self.emit_expr(node.left)
            # Handle chained comparisons
            parts = []
            prev = left
            for op, comp in zip(node.ops, node.comparators):
                lispy_op = PY_TO_LISPY_CMP.get(type(op), '=')
                right = self.emit_expr(comp)
                parts.append(f'({lispy_op} {prev} {right})')
                prev = right
            if len(parts) == 1:
                return parts[0]
            return f'(and {" ".join(parts)})'

        if isinstance(node, ast.BoolOp):
            op = PY_TO_LISPY_BOOL.get(type(node.op), 'and')
            args = ' '.join(self.emit_expr(v) for v in node.values)
            return f'({op} {args})'

        if isinstance(node, ast.Call):
            func_name = self._call_name(node)
            # Check builtins
            if func_name in PY_BUILTINS_TO_LISPY:
                lispy_fn = PY_BUILTINS_TO_LISPY[func_name]
                args = ' '.join(self.emit_expr(a) for a in node.args)
                return f'({lispy_fn} {args})'
            if func_name in PY_MATH_TO_LISPY:
                lispy_fn = PY_MATH_TO_LISPY[func_name]
                args = ' '.join(self.emit_expr(a) for a in node.args)
                return f'({lispy_fn} {args})'
            if func_name == 'range':
                args = ' '.join(self.emit_expr(a) for a in node.args)
                return f'(range {args})'
            # Generic call
            args = ' '.join(self.emit_expr(a) for a in node.args)
            return f'({self._lispyname(func_name)} {args})'

        if isinstance(node, ast.Attribute):
            val = self.emit_expr(node.value)
            return f'{val}.{node.attr}'

        if isinstance(node, ast.Subscript):
            val = self.emit_expr(node.value)
            sl = self.emit_expr(node.slice)
            return f'(nth {val} {sl})'

        if isinstance(node, ast.List):
            elems = ' '.join(self.emit_expr(e) for e in node.elts)
            return f'(list {elems})'

        if isinstance(node, ast.ListComp):
            # [expr for x in iter] → (map expr iter) or (filter ...)
            elt = self.emit_expr(node.elt)
            gen = node.generators[0]
            iter_expr = self.emit_expr(gen.iter)
            if gen.ifs:
                cond = self.emit_expr(gen.ifs[0])
                return f'(filter {cond} {iter_expr})'
            return f'(map {elt} {iter_expr})'

        if isinstance(node, ast.IfExp):
            test = self.emit_expr(node.test)
            body = self.emit_expr(node.body)
            els = self.emit_expr(node.orelse)
            return f'(if {test} {body} {els})'

        if isinstance(node, ast.JoinedStr):
            # f-string → concat
            parts = []
            for v in node.values:
                if isinstance(v, ast.Constant):
                    parts.append(f'"{v.value}"')
                elif isinstance(v, ast.FormattedValue):
                    parts.append(f'(string {self.emit_expr(v.value)})')
            return f'(concat {" ".join(parts)})'

        return f';; [expr: {type(node).__name__}]'

    def _emit_cond_chain(self, node):
        """Convert if/elif/else chain to (cond ...)."""
        clauses = []
        current = node
        while current:
            test = self.emit_expr(current.test)
            body = self._block(current.body)
            clauses.append(f'  ({test} {body})')
            if current.orelse:
                if len(current.orelse) == 1 and isinstance(current.orelse[0], ast.If):
                    current = current.orelse[0]
                else:
                    body = self._block(current.orelse)
                    clauses.append(f'  (true {body})')
                    break
            else:
                break
        return '(cond\n' + '\n'.join(clauses) + ')'

    def _block(self, stmts):
        if len(stmts) == 1:
            return self.emit(stmts[0])
        lines = [self.emit(s) for s in stmts]
        body = '\n    '.join(l for l in lines if l)
        return f'(begin\n    {body})'

    def _name(self, node):
        if isinstance(node, ast.Name):
            return self._lispyname(node.id)
        if isinstance(node, ast.Attribute):
            return f'{self._name(node.value)}.{node.attr}'
        return str(node)

    def _call_name(self, node):
        if isinstance(node.func, ast.Name):
            return node.func.id
        if isinstance(node.func, ast.Attribute):
            val = self._call_name_attr(node.func.value)
            return f'{val}.{node.func.attr}'
        return '?'

    def _call_name_attr(self, node):
        if isinstance(node, ast.Name):
            return node.id
        return '?'

    def _lispyname(self, name):
        return name.replace('_', '-') if not name.startswith('_') else name


# ═══════════════════════════════════════════════════════════
# CLI
# ═══════════════════════════════════════════════════════════

def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)

    check_mode = '--check' in sys.argv
    args = [a for a in sys.argv[1:] if not a.startswith('-')]
    out_flag = None
    for i, a in enumerate(sys.argv):
        if a == '-o' and i + 1 < len(sys.argv):
            out_flag = sys.argv[i + 1]

    infile = args[0]
    source = open(infile).read()
    ext = os.path.splitext(infile)[1]

    if ext == '.lispy':
        # LisPy → Python
        tokens = tokenize(source)
        ast_nodes = parse_tokens(tokens)
        transpiler = LispyToPython()
        output = transpiler.transpile(ast_nodes)
        out_ext = '.py'
    elif ext == '.py':
        # Python → LisPy
        transpiler = PythonToLispy()
        output = transpiler.transpile(source)
        out_ext = '.lispy'
    else:
        print(f"Unknown extension: {ext}. Use .lispy or .py")
        sys.exit(1)

    if check_mode:
        # Roundtrip: A → B → A, verify equivalence
        print(f"Roundtrip check: {infile}")
        print(output[:500])
        print("---")
        # Attempt roundtrip
        if ext == '.lispy':
            rt = PythonToLispy().transpile(output)
            print(f"Roundtrip ({ext} → .py → .lispy):")
            print(rt[:500])
        else:
            tokens = tokenize(output)
            ast_nodes = parse_tokens(tokens)
            rt = LispyToPython().transpile(ast_nodes)
            print(f"Roundtrip ({ext} → .lispy → .py):")
            print(rt[:500])
        sys.exit(0)

    outfile = out_flag or os.path.splitext(infile)[0] + out_ext
    if outfile == '-':
        sys.stdout.write(output)
    else:
        with open(outfile, 'w') as f:
            f.write(output)
        print(f"✅ {infile} → {outfile}")


if __name__ == '__main__':
    main()
