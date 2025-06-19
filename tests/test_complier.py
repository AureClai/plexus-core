# tests/test_compiler.py

import pytest
from plexus_core import build_ast_from_json
import textwrap


def test_simple_program_compilation():
    graph_data = {
        "nodes": [
            {"id": "node1", "type": "variable_assign", "value": "message",
                "inputs": [{"name": "value", "value": "'Hello, Plexus!'"}]},
            {"id": "node2", "type": "print", "inputs": [
                {"name": "target", "link": "node1"}]}
        ]
    }
    expected_code = "message = 'Hello, Plexus!'\nprint(message)"
    generated_code = build_ast_from_json(graph_data)
    assert generated_code.strip() == expected_code.strip()


def test_binary_op_compilation():
    graph_data = {
        "nodes": [
            {"id": "node_add", "type": "binary_op", "value": "+",
                "inputs": [{"name": "left", "value": "5"}, {"name": "right", "value": "10"}]},
            {"id": "node_assign", "type": "variable_assign", "value": "result",
             "inputs": [{"name": "value", "link": "node_add"}]}
        ]
    }
    expected_code = "result = 5 + 10"
    generated_code = build_ast_from_json(graph_data)
    assert generated_code.strip() == expected_code.strip()


def test_if_else_statement_compilation():
    graph_data = {
        "nodes": [
            {"id": "node_assign_age", "type": "variable_assign",
                "value": "age", "inputs": [{"name": "value", "value": "21"}]},
            {"id": "node_compare", "type": "binary_op", "value": ">=", "inputs": [
                {"name": "left", "link": "node_assign_age"}, {"name": "right", "value": "18"}]},
            {"id": "node_if", "type": "if_statement", "inputs": [{"name": "test", "link": "node_compare"}],
             "body": [{"id": "node_print_welcome", "type": "print", "inputs": [{"name": "target", "value": "'Welcome'"}]}],
             "orelse": [{"id": "node_print_too_young", "type": "print", "inputs": [{"name": "target", "value": "'Too young'"}]}]
             }
        ]
    }
    expected_code = """
    age = 21
    if age >= 18:
        print('Welcome')
    else:
        print('Too young')
    """
    generated_code = build_ast_from_json(graph_data)
    assert generated_code.strip() == textwrap.dedent(expected_code).strip()


def test_unlinked_node_error():
    """Tests that a clear ValueError is raised for an invalid link."""
    graph_data_with_error = {
        "nodes": [
            {"id": "node2", "type": "print", "inputs": [
                {"name": "target", "link": "node1"}]}
        ]
    }
    with pytest.raises(ValueError) as excinfo:
        build_ast_from_json(graph_data_with_error)

    # UPDATED ASSERTION: We now check for the exact error message.
    assert str(excinfo.value) == "Node link 'node1' not found in graph."
