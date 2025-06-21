# tests/test_inspector.py

import pytest
from plexus_core import generate_nodes_from_module
import math # A standard library module for testing

# --- A dummy module for more specific testing ---
class MockOsModule:
    """A mock module to simulate os-like functions."""
    __name__ = 'os'

    def getcwd():
        """Return a string representing the current working directory."""
        return "/usr/mock"

    def path_join(path: str, *paths: str) -> str:
        """Join one or more path components intelligently."""
        # Note: *paths makes this currently unsupported by our inspector, so it should be skipped.
        return path
    
    def _private_func():
        """This function should be ignored by the inspector."""
        pass

def test_generate_nodes_from_math_module():
    """
    Tests that we can inspect a real standard library module like 'math'.
    """
    nodes = generate_nodes_from_module(math)
    
    # Find the node definition for 'sin'
    sin_node = next((n for n in nodes if n['func_name'] == 'sin'), None)
    
    assert sin_node is not None, "Node for 'sin' function was not found."
    assert sin_node['display_name'] == 'math.sin'
    assert sin_node['node_type'] == 'call_function'
    assert len(sin_node['inputs']) == 1
    assert sin_node['inputs'][0]['name'] == 'x'
    assert sin_node['inputs'][0]['required'] is True
    assert "Return the sine of x" in sin_node['doc']

def test_generate_nodes_from_mock_module():
    """
    Tests that the inspector works on a custom mock module and correctly
    handles public, private, and unsupported functions.
    """
    nodes = generate_nodes_from_module(MockOsModule)

    assert len(nodes) == 1, "Inspector should find exactly one valid public function."
    
    getcwd_node = nodes[0]
    assert getcwd_node['func_name'] == 'getcwd'
    assert getcwd_node['display_name'] == 'os.getcwd'
    assert len(getcwd_node['inputs']) == 0 # getcwd takes no arguments
    assert len(getcwd_node['outputs']) == 0 # No return type hint
    
    # Check that '_private_func' and 'path_join' were correctly ignored
    func_names = [n['func_name'] for n in nodes]
    assert '_private_func' not in func_names
    assert 'path_join' not in func_names

