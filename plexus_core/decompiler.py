# plexus_core/decompiler.py

import ast
import json


class JSONDecompiler(ast.NodeVisitor):
    """
    Walks a Python AST and converts it into a Plexus JSON graph representation.
    """

    def __init__(self):
        # The graph structure we are building
        self.nodes = []
        self.connections = []  # Reserved for future use if needed

        # Tracks which node ID provides which variable
        # e.g., {"my_var": "node-1"}
        self.variable_providers = {}

        # Tracks which AST expression nodes correspond to which Plexus node IDs
        # This is for linking expressions (like a BinOp) to their usage
        self.expression_map = {}

        self._node_count = 0

    def _get_unique_id(self, prefix='node'):
        """
        Generates a unique ID for a new node.
        """
        self._node_count += 1
        return f"{prefix}-{self._node_count}"

    def visit(self, node):
        """Override the default visit to handle statement-level nodes."""
        # The default visit traverses the whole tree. We want to walk
        # through the body of a module statement by statement.
        if isinstance(node, ast.Module):
            for stmt in node.body:
                self.visit(stmt)
        else:
            super().visit(node)

    def _create_input_from_ast(self, value_node: ast.AST) -> dict:
        """
        Analyzes an AST value node (like a Name or Constant) and creates
        the corresponding Plexus input link or literal value.
        """
        if isinstance(value_node, ast.Constant):
            # It's a literal value like 5 or "hello"
            # We use repr() to get the source-code representation
            return {"name": "value", "value": repr(value_node.value)}

        elif isinstance(value_node, ast.Name):
            # It's a variable. We need to find who provides it.
            var_name = value_node.id
            if var_name in self.variable_providers:
                provider_node_id = self.variable_providers[var_name]
                return {"name": "target", "link": provider_node_id}
            else:
                raise NameError(
                    f"Variable '{var_name}' used before assignment.")
        else:
            # It's a more complex expression (like BinOp or Compare).
            # We need to recursively visit it to generate its node first.
            if value_node not in self.expression_map:
                self.visit(value_node)  # This will populate expression_map

            expr_node_id = self.expression_map[value_node]
            return {"name": "value", "link": expr_node_id}

    def visit_Assign(self, node: ast.Assign):
        """Called when visiting a variable assignment (e.g., x = 10)."""
        # For simplicity, we only handle single assignments like 'x = ...'
        if len(node.targets) != 1 or not isinstance(node.targets[0], ast.Name):
            return  # Skip complex assignments like x, y = 1, 2
        var_name = node.targets[0].id
        node_id = self._get_unique_id("assign")

        plexus_node = {
            "id": node_id,
            "type": "variable_assign",
            "value": var_name,
            "inputs": [self._create_input_from_ast(node.value)]
        }

        self.nodes.append(plexus_node)
        # Record that this node ID is now the provider for this variable
        self.variable_providers[var_name] = node_id

    def visit_Expr(self, node: ast.Expr):
        """Called for expressions used as statements, like a print() call."""
        # We only care if the expression is a function call to 'print'
        if isinstance(node.value, ast.Call) and isinstance(node.value.func, ast.Name):
            if node.value.func.id == 'print':
                # This is a print statement, delegate to a print visitor
                self.visit_Print(node.value)

        # Continue traversing in case there are nested expressions to handle
        self.generic_visit(node)

    def visit_Print(self, node: ast.Call):
        """A custom visitor for print() calls."""
        if len(node.args) != 1:
            return  # Skip print calls with zero or more than one argument

        node_id = self._get_unique_id("print")

        plexus_node = {
            "id": node_id,
            "type": "print",
            "inputs": [self._create_input_from_ast(node.args[0])]
        }

        self.nodes.append(plexus_node)

    def get_graph(self) -> dict:
        """Returns the final, constructed JSON graph."""
        return {
            "nodes": self.nodes,
            "connections": self.connections
        }


def decompile_python_to_json(python_code: str) -> dict:
    """
    High-level function to decompile a Python code string to a Plexus JSON graph.
    """
    try:
        ast_tree = ast.parse(python_code)
    except SyntaxError as e:
        raise ValueError(f"Invalid Python code provided: {e}") from e

    decompiler = JSONDecompiler()
    decompiler.visit(ast_tree)
    return decompiler.get_graph()
