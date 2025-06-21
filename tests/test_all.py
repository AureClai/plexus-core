# tests/test_all.py

import pytest
from plexus_core import build_ast_from_json, decompile_python_to_json
import textwrap
import ast

# --- Consistency (Round-Trip) Tests ---

def run_python_round_trip(code_text):
    """Helper function to run a Python -> JSON -> Python round trip test."""
    original_code = textwrap.dedent(code_text).strip()
    intermediate_graph = decompile_python_to_json(original_code)
    recompiled_code = build_ast_from_json(intermediate_graph)
    
    original_ast = ast.parse(original_code)
    recompiled_ast = ast.parse(recompiled_code)
    # Compare ASTs without location info (lineno, col_offset) for robustness against formatting differences.
    assert ast.dump(original_ast, include_attributes=False) == ast.dump(recompiled_ast, include_attributes=False), \
        f"AST mismatch after round trip.\nOriginal code: {original_code}\nRecompiled code: {recompiled_code}\nOriginal AST: {ast.dump(original_ast)}\nRecompiled AST: {ast.dump(recompiled_ast)}"

def test_consistency_simple_assignment():
    run_python_round_trip("x = 100")

def test_consistency_simple_print():
    run_python_round_trip("print('hello')")

def test_consistency_assignment_and_print():
    run_python_round_trip("x = 100\nprint(x)")

def test_consistency_if_else():
    run_python_round_trip("""
    score = 85
    if score >= 80:
        print('B')
    else:
        print('C')
    """)

def test_consistency_if_without_else():
    run_python_round_trip("""
    x = 5
    if x > 10:
        print('no')
    """)

def test_consistency_for_loop():
    run_python_round_trip("""
    items = [1, 2]
    for i in items:
        print(i)
    """)

def test_consistency_function_call_in_assignment():
    run_python_round_trip("len('hello')")

def test_consistency_empty_if():
    run_python_round_trip("if True:\n    pass")

# --- Error Handling Tests ---

def test_compiler_raises_on_missing_id():
    graph = {"nodes": [{"type": "call_function", "func_name": "print"}]}
    with pytest.raises(ValueError, match="missing a required 'id' field"):
        build_ast_from_json(graph)

def test_compiler_raises_on_missing_type():
    graph = {"nodes": [{"id": "n1"}]}
    with pytest.raises(ValueError, match="Node 'n1' is missing a 'type' field"):
        build_ast_from_json(graph)

def test_compiler_raises_on_missing_input():
    graph = {"nodes": [{"id": "n1", "type": "if_statement"}]}
    with pytest.raises(ValueError, match="Node 'n1' of type 'if_statement' is missing required input: 'test'"):
        build_ast_from_json(graph)

def test_decompiler_raises_on_multi_assign():
    with pytest.raises(NotImplementedError, match="Assignment to non-simple targets"):
        decompile_python_to_json("x, y = 1, 2")

def test_decompiler_raises_on_keyword_args():
    with pytest.raises(NotImplementedError, match="Keyword arguments are not yet supported"):
        decompile_python_to_json("print('a', end='')")