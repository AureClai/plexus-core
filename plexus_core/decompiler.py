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
        self.statement_nodes = []
        self.expression_nodes = []
        self.variable_providers = {}
        self.expression_map = {}
        self._node_count = 0

    def _get_unique_id(self, prefix='node'):
        self._node_count += 1
        return f"{prefix}-{self._node_count}"

    def _get_input_data_from_ast(self, value_node: ast.AST) -> dict:
        if isinstance(value_node, ast.Constant):
            return {"value": repr(value_node.value)}
        elif isinstance(value_node, ast.Name):
            var_name = value_node.id
            if var_name in self.variable_providers:
                return {"link": self.variable_providers[var_name]}
            else:
                raise NameError(f"Variable '{var_name}' used before assignment.")
        elif isinstance(value_node, (ast.List, ast.Tuple, ast.Set, ast.Dict)):
            return {"value": ast.unparse(value_node)}
        else:
            if value_node not in self.expression_map:
                self.visit(value_node)
            return {"link": self.expression_map.get(value_node)}

    def _decompile_body(self, body_nodes: list) -> list:
        original_stmt_nodes = self.statement_nodes
        self.statement_nodes = []
        for stmt in body_nodes:
            self.visit(stmt)
        newly_added_nodes = self.statement_nodes
        self.statement_nodes = original_stmt_nodes
        return newly_added_nodes

    def visit(self, node):
        method = 'visit_' + node.__class__.__name__
        visitor = getattr(self, method, self.generic_visit)
        return visitor(node)
    
    def generic_visit(self, node):
        super().generic_visit(node)

    def visit_Assign(self, node: ast.Assign):
        self.visit(node.value)
        target = node.targets[0]
        if not isinstance(target, ast.Name):
            raise NotImplementedError("Unsupported syntax: Assignment to non-simple targets")
        
        var_name = target.id
        node_id = self._get_unique_id("assign")
        input_data = self._get_input_data_from_ast(node.value)
        input_data['name'] = 'value' # Ensure input has a name for the compiler
        plexus_node = {
            "id": node_id,
            "type": "variable_assign",
            "value": var_name,
            "inputs": [input_data],
            "is_intended_statement": True # Assign is always a statement
        }
        self.statement_nodes.append(plexus_node)
        self.variable_providers[var_name] = node_id

    def visit_Expr(self, node: ast.Expr):
        if isinstance(node.value, ast.Call):
            self.visit_Call(node.value, is_statement=True)
        else:
            self.generic_visit(node)
    
    def visit_If(self, node: ast.If):
        node_id = self._get_unique_id("if")
        self.visit(node.test)
        test_input = self._get_input_data_from_ast(node.test)
        test_input['name'] = 'test'
        body_plexus_nodes = self._decompile_body(node.body)
        orelse_plexus_nodes = self._decompile_body(node.orelse) if node.orelse else []
        plexus_node = {
            "id": node_id,
            "type": "if_statement",
            "inputs": [test_input],
            "body": body_plexus_nodes,
            "orelse": orelse_plexus_nodes,
            "is_intended_statement": True # If is always a statement
        }
        self.statement_nodes.append(plexus_node)

    def visit_For(self, node: ast.For):
        if node.orelse: raise NotImplementedError("For/else loops are not supported.")
        if not isinstance(node.target, ast.Name): raise NotImplementedError("Looping with complex targets is not supported.")
        
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
            "id": node_id,
            "type": "for_loop",
            "target_variable": target_var_name,
            "inputs": [iter_input],
            "body": body_plexus_nodes,
            "is_intended_statement": True # For is always a statement
        }
        self.statement_nodes.append(plexus_node)

    def visit_Call(self, node: ast.Call, is_statement=False):
        if not isinstance(node.func, ast.Name): return
        if node.keywords: raise NotImplementedError("Keyword arguments are not yet supported.")

        for arg_node in node.args: self.visit(arg_node)

        func_name = node.func.id
        node_id = self._get_unique_id("call")
        inputs = []
        for i, arg_node in enumerate(node.args):
            input_data = self._get_input_data_from_ast(arg_node)
            input_data['name'] = f'arg{i}'
            inputs.append(input_data)
        plexus_node = {
            "id": node_id,
            "type": "call_function",
            "func_name": func_name,
            "inputs": inputs,
            "is_intended_statement": is_statement # Set based on the parameter
        }
        
        if is_statement:
            self.statement_nodes.append(plexus_node)
        else:
            self.expression_nodes.append(plexus_node)
        self.expression_map[node] = node_id

    def visit_BinOp(self, node: ast.BinOp):
        self.visit(node.left); self.visit(node.right)
        node_id = self._get_unique_id("op")
        op_class = type(node.op)
        if op_class not in REVERSE_BINOP_MAP: return self.generic_visit(node)
        op_str = REVERSE_BINOP_MAP[op_class]
        left_input = self._get_input_data_from_ast(node.left); left_input['name'] = 'left'
        right_input = self._get_input_data_from_ast(node.right); right_input['name'] = 'right'
        plexus_node = {
            "id": node_id,
            "type": "binary_op",
            "value": op_str,
            "inputs": [left_input, right_input],
            "is_intended_statement": False # Binary operations are expressions
        }
        self.expression_nodes.append(plexus_node)
        self.expression_map[node] = node_id

    def visit_Compare(self, node: ast.Compare):
        self.visit(node.left); self.visit(node.comparators[0])
        if len(node.ops) != 1: return self.generic_visit(node)
        node_id = self._get_unique_id("op")
        op_class = type(node.ops[0])
        if op_class not in REVERSE_CMPOP_MAP: return self.generic_visit(node)
        op_str = REVERSE_CMPOP_MAP[op_class]
        left_input = self._get_input_data_from_ast(node.left); left_input['name'] = 'left'
        right_input = self._get_input_data_from_ast(node.comparators[0]); right_input['name'] = 'right'
        plexus_node = {
            "id": node_id,
            "type": "binary_op", # Note: Compiler handles compare_op as a binary_op type
            "value": op_str,
            "inputs": [left_input, right_input],
            "is_intended_statement": False # Comparisons are expressions
        }
        self.expression_nodes.append(plexus_node)
        self.expression_map[node] = node_id

    def get_graph(self) -> dict:
        # The final graph must contain ALL nodes for the compiler to find them.
        all_nodes = self.statement_nodes + self.expression_nodes
        return {"nodes": all_nodes, "connections": []}


def decompile_python_to_json(python_code: str) -> dict:
    try:
        ast_tree = ast.parse(python_code)
    except SyntaxError as e:
        raise ValueError(f"Invalid Python code provided: {e}") from e
    decompiler = JSONDecompiler()
    decompiler.visit(ast_tree) 
    return decompiler.get_graph()
