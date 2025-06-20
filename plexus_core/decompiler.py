# plexus_core/decompiler.py

import ast
import json

REVERSE_BINOP_MAP = {
    ast.Add: "+", ast.Sub: "-", ast.Mult: "*", ast.Div: "/",
}
REVERSE_CMPOP_MAP = {
    ast.Eq: "==", ast.NotEq: "!=", ast.Lt: "<",
    ast.LtE: "<=", ast.Gt: ">", ast.GtE: ">=",
}


class JSONDecompiler(ast.NodeVisitor):
    """Walks a Python AST and converts it into a Plexus JSON graph representation."""

    def __init__(self):
        self.nodes = []
        self.connections = []
        self.variable_providers = {}
        self.expression_map = {}
        self._node_count = 0

    def _get_unique_id(self, prefix='node'):
        self._node_count += 1
        return f"{prefix}-{self._node_count}"

    def _get_input_data_from_ast(self, value_node: ast.AST) -> dict:
        """Analyzes an AST value node and returns the core of an input dict."""
        if isinstance(value_node, ast.Constant):
            return {"value": repr(value_node.value)}
        elif isinstance(value_node, ast.Name):
            var_name = value_node.id
            if var_name in self.variable_providers:
                return {"link": self.variable_providers[var_name]}
            else:
                raise NameError(
                    f"Variable '{var_name}' used before assignment.")
        # FIX: Explicitly handle collection literals by unparsing them.
        elif isinstance(value_node, (ast.List, ast.Tuple, ast.Set, ast.Dict)):
            return {"value": ast.unparse(value_node)}
        else:
            if value_node not in self.expression_map:
                self.visit(value_node)
            return {"link": self.expression_map.get(value_node)}

    def _decompile_body(self, body_nodes: list) -> list:
        original_nodes_list = self.nodes
        self.nodes = []
        for stmt in body_nodes:
            self.visit(stmt)
        newly_added_nodes = self.nodes
        self.nodes = original_nodes_list
        return newly_added_nodes

    def visit(self, node):
        method = 'visit_' + node.__class__.__name__
        visitor = getattr(self, method, self.generic_visit)
        return visitor(node)

    def generic_visit(self, node):
        super().generic_visit(node)

    def visit_Assign(self, node: ast.Assign):
        if len(node.targets) != 1:
            raise NotImplementedError(
                "Unsupported syntax: Assignment to multiple targets is not supported.")
        target = node.targets[0]
        if isinstance(target, (ast.Tuple, ast.List)):
            raise NotImplementedError(
                "Unsupported syntax: Assignment to multiple targets is not supported.")
        if not isinstance(target, ast.Name):
            raise NotImplementedError(
                "Unsupported syntax: Assignment to non-variable targets is not supported.")
        var_name = target.id
        node_id = self._get_unique_id("assign")
        input_data = self._get_input_data_from_ast(node.value)
        input_data['name'] = 'value'
        plexus_node = {"id": node_id, "type": "variable_assign",
                       "value": var_name, "inputs": [input_data]}
        self.nodes.append(plexus_node)
        self.variable_providers[var_name] = node_id

    def visit_Expr(self, node: ast.Expr):
        if isinstance(node.value, ast.Call) and isinstance(node.value.func, ast.Name) and node.value.func.id == 'print':
            self.visit_Print(node.value)
        else:
            self.generic_visit(node)

    def visit_If(self, node: ast.If):
        node_id = self._get_unique_id("if")
        self.visit(node.test)
        test_input = self._get_input_data_from_ast(node.test)
        test_input['name'] = 'test'
        body_plexus_nodes = self._decompile_body(node.body)
        orelse_plexus_nodes = self._decompile_body(node.orelse)
        plexus_node = {"id": node_id, "type": "if_statement", "inputs": [
            test_input], "body": body_plexus_nodes, "orelse": orelse_plexus_nodes}
        self.nodes.append(plexus_node)

    def visit_For(self, node: ast.For):
        if node.orelse:
            raise NotImplementedError("For/else loops are not supported.")
        if not isinstance(node.target, ast.Name):
            raise NotImplementedError(
                "Looping with complex targets (e.g., for x, y in ...)")

        node_id = self._get_unique_id("for_loop")
        target_var_name = node.target.id
        self.visit(node.iter)
        iter_input = self._get_input_data_from_ast(node.iter)
        iter_input['name'] = 'iter'
        previous_provider = self.variable_providers.get(target_var_name)
        self.variable_providers[target_var_name] = node_id
        body_plexus_nodes = self._decompile_body(node.body)
        if previous_provider:
            self.variable_providers[target_var_name] = previous_provider
        else:
            del self.variable_providers[target_var_name]
        plexus_node = {
            "id": node_id, "type": "for_loop", "target_variable": target_var_name,
            "inputs": [iter_input], "body": body_plexus_nodes
        }
        self.nodes.append(plexus_node)

    def visit_Print(self, node: ast.Call):
        if len(node.args) != 1:
            raise NotImplementedError(
                f"Unsupported syntax: print() calls with {len(node.args)} arguments are not supported.")
        node_id = self._get_unique_id("print")
        input_data = self._get_input_data_from_ast(node.args[0])
        input_data['name'] = 'target'
        plexus_node = {"id": node_id, "type": "print", "inputs": [input_data]}
        self.nodes.append(plexus_node)

    def visit_BinOp(self, node: ast.BinOp):
        self.visit(node.left)
        self.visit(node.right)
        node_id = self._get_unique_id("op")
        op_class = type(node.op)
        if op_class not in REVERSE_BINOP_MAP:
            return self.generic_visit(node)
        op_str = REVERSE_BINOP_MAP[op_class]
        left_input = self._get_input_data_from_ast(node.left)
        left_input['name'] = 'left'
        right_input = self._get_input_data_from_ast(node.right)
        right_input['name'] = 'right'
        plexus_node = {"id": node_id, "type": "binary_op",
                       "value": op_str, "inputs": [left_input, right_input]}
        self.nodes.append(plexus_node)
        self.expression_map[node] = node_id

    def visit_Compare(self, node: ast.Compare):
        self.visit(node.left)
        self.visit(node.comparators[0])
        if len(node.ops) != 1:
            return self.generic_visit(node)
        node_id = self._get_unique_id("op")
        op_class = type(node.ops[0])
        if op_class not in REVERSE_CMPOP_MAP:
            return self.generic_visit(node)
        op_str = REVERSE_CMPOP_MAP[op_class]
        left_input = self._get_input_data_from_ast(node.left)
        left_input['name'] = 'left'
        right_input = self._get_input_data_from_ast(node.comparators[0])
        right_input['name'] = 'right'
        plexus_node = {"id": node_id, "type": "binary_op",
                       "value": op_str, "inputs": [left_input, right_input]}
        self.nodes.append(plexus_node)
        self.expression_map[node] = node_id

    def get_graph(self) -> dict:
        return {"nodes": self.nodes, "connections": self.connections}


def decompile_python_to_json(python_code: str) -> dict:
    try:
        ast_tree = ast.parse(python_code)
    except SyntaxError as e:
        raise ValueError(f"Invalid Python code provided: {e}") from e

    decompiler = JSONDecompiler()
    decompiler.visit(ast_tree)
    return decompiler.get_graph()
