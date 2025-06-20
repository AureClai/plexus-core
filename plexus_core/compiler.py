# plexus_core/compiler.py

import ast


class ASTCompiler:
    """Compiles a JSON-defined graph into an Abstract Syntax Tree (AST)."""
    BINOP_MAP = {
        "+": ast.Add, "-": ast.Sub, "*": ast.Mult, "/": ast.Div,
    }
    CMPOP_MAP = {
        "==": ast.Eq, "!=": ast.NotEq, "<": ast.Lt,
        "<=": ast.LtE, ">": ast.Gt, ">=": ast.GtE,
    }

    def __init__(self, graph_json: dict):
        self.graph = graph_json
        self.node_map = {}
        if 'nodes' not in self.graph or not isinstance(self.graph['nodes'], list):
            raise ValueError(
                "Input JSON must contain a 'nodes' key with a list of nodes.")
        self._discover_nodes(self.graph.get('nodes', []))
        self.expression_cache = {}
        self.compiled_statements = set()

    def _discover_nodes(self, node_list: list):
        for node in node_list:
            try:
                node_id = node['id']
                if node_id in self.node_map:
                    continue
                self.node_map[node_id] = node
                if node.get('body'):
                    self._discover_nodes(node['body'])
                if node.get('orelse'):
                    self._discover_nodes(node['orelse'])
            except KeyError:
                raise ValueError(
                    f"A node in the graph is missing a required 'id' field. Node data: {node}")

    def _get_input_as_ast(self, input_data: dict) -> ast.expr:
        if 'link' in input_data:
            link_id = input_data['link']
            if link_id not in self.node_map:
                raise ValueError(f"Node link '{link_id}' not found in graph.")
            linked_node = self.node_map[link_id]
            if linked_node.get('type') == 'for_loop':
                return ast.Name(id=linked_node['target_variable'], ctx=ast.Load())
            if link_id not in self.expression_cache:
                self._build_expression(linked_node)
            return self.expression_cache[link_id]
        elif 'value' in input_data:
            try:
                return ast.parse(input_data['value'], mode='eval').body
            except (SyntaxError, IndexError):
                raise ValueError(
                    f"Could not parse literal value: {input_data['value']}")
        else:
            raise ValueError(
                f"Input dictionary is malformed. Must contain 'link' or 'value'. Got: {input_data}")

    def _build_expression(self, node: dict):
        node_id = node['id']
        if node_id in self.expression_cache:
            return

        node_type = node.get('type')
        if not node_type:
            raise ValueError(f"Node '{node_id}' is missing a 'type' field.")

        def get_input(name: str) -> dict:
            for i in node.get('inputs', []):
                if i.get('name') == name:
                    return i
            raise ValueError(
                f"Node '{node_id}' of type '{node_type}' is missing required input: '{name}'")

        if node_type == 'variable_assign':
            self.expression_cache[node_id] = ast.Name(
                id=node['value'], ctx=ast.Load())
        elif node_type == 'binary_op':
            op_str = node['value']
            left = self._get_input_as_ast(get_input('left'))
            right = self._get_input_as_ast(get_input('right'))
            if op_str in self.BINOP_MAP:
                self.expression_cache[node_id] = ast.BinOp(
                    left=left, op=self.BINOP_MAP[op_str](), right=right)
            elif op_str in self.CMPOP_MAP:
                self.expression_cache[node_id] = ast.Compare(
                    left=left, ops=[self.CMPOP_MAP[op_str]()], comparators=[right])
        elif node_type == 'call_function':
            func_name = node['func_name']
            func_ast = ast.Name(id=func_name, ctx=ast.Load())
            args = sorted(node.get('inputs', []), key=lambda i: i['name'])
            arg_asts = [self._get_input_as_ast(arg) for arg in args]
            self.expression_cache[node_id] = ast.Call(
                func=func_ast, args=arg_asts, keywords=[])

    def _build_statement(self, node: dict) -> ast.stmt | None:
        node_id = node['id']
        if node_id in self.compiled_statements:
            return None

        node_type = node.get('type')
        if not node_type:
            raise ValueError(f"Node '{node_id}' is missing a 'type' field.")

        def get_input(name: str) -> dict:
            for i in node.get('inputs', []):
                if i.get('name') == name:
                    return i
            raise ValueError(
                f"Node '{node_id}' of type '{node_type}' is missing required input: '{name}'")

        statement = None
        if node_type == 'variable_assign':
            self._build_expression(node)
            target = ast.Name(id=node['value'], ctx=ast.Store())
            value = self._get_input_as_ast(get_input('value'))
            statement = ast.Assign(targets=[target], value=value)
        elif node_type == 'call_function':
            self._build_expression(node)
            statement = ast.Expr(value=self.expression_cache[node_id])
        elif node_type == 'if_statement':
            test = self._get_input_as_ast(get_input('test'))
            body = [stmt for n in node.get('body', []) if (
                stmt := self._build_statement(n)) is not None]
            orelse = [stmt for n in node.get('orelse', []) if (
                stmt := self._build_statement(n)) is not None]
            if not body:
                body = [ast.Pass()]
            statement = ast.If(test=test, body=body, orelse=orelse)
        elif node_type == 'for_loop':
            target_var_name = node['target_variable']
            target_ast = ast.Name(id=target_var_name, ctx=ast.Store())
            iter_ast = self._get_input_as_ast(get_input('iter'))
            body = [stmt for n in node.get('body', []) if (
                stmt := self._build_statement(n)) is not None]
            if not body:
                body = [ast.Pass()]
            statement = ast.For(target=target_ast,
                                iter=iter_ast, body=body, orelse=[])

        if statement:
            self.compiled_statements.add(node_id)
        return statement

    def compile(self) -> str:
        # FIX: Correctly initialize ast.Module for compatibility.
        tree = ast.Module(body=[], type_ignores=[])

        # FIX: Intelligently determine which nodes are top-level statements
        linked_ids = set()
        for node in self.graph['nodes']:
            for an_input in node.get('inputs', []):
                if 'link' in an_input:
                    linked_ids.add(an_input['link'])

        for node in self.graph['nodes']:
            # A node is a top-level statement if nothing links to it.
            if node['id'] not in linked_ids:
                stmt = self._build_statement(node)
                if stmt:
                    tree.body.append(stmt)

        ast.fix_missing_locations(tree)
        return ast.unparse(tree)


def build_ast_from_json(graph_json: dict) -> str:
    compiler = ASTCompiler(graph_json)
    return compiler.compile()
