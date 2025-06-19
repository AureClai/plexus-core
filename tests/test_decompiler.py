# tests/test_decompiler.py

import pytest
from plexus_core import decompile_python_to_json
import textwrap


def test_simple_program_decompilation():
    """
    Tests that a basic Python script with an assignment and a print call
    is correctly decompiled into the Plexus JSON graph format.
    """
    python_code = textwrap.dedent("""
    message = "Hello from the decompiler!"
    print(message)
    """)

    # This is the exact JSON structure we expect the decompiler to produce.
    expected_graph = {
        "nodes": [
            {
                "id": "assign-1",
                "type": "variable_assign",
                "value": "message",
                "inputs": [
                    {
                        "name": "value",
                        "value": "'Hello from the decompiler!'"
                    }
                ]
            },
            {
                "id": "print-2",
                "type": "print",
                "inputs": [
                    {
                        "name": "target",
                        "link": "assign-1"
                    }
                ]
            }
        ],
        "connections": []
    }

    # Run the decompiler and get the result
    generated_graph = decompile_python_to_json(python_code)

    # Assert that the generated graph is exactly what we expected
    assert generated_graph == expected_graph


def test_invalid_python_code_raises_error():
    """
    Tests that the decompiler raises a ValueError when given invalid syntax.
    """
    invalid_code = "message = 'missing quote"

    # pytest can check that our function correctly raises the expected error.
    with pytest.raises(ValueError, match="Invalid Python code provided"):
        decompile_python_to_json(invalid_code)
