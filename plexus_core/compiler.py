# plexus_core/compiler.py

import ast


class ASTCompiler:
    """
    Compiles a JSON-defined graph into an Abstract Syntax Tree (AST),
    which is then unparsed into executable Python code.
    """
    # CORRECT: Separate maps for different operation types.
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
        self._discover_nodes(self.graph.get('nodes', []))
        self.expression_cache = {}
        self.compiled_statements = set()

    def _discover_nodes(self, node_list: list):
        for node in node_list:
            if node['id'] in self.node_map:
                continue
            self.node_map[node['id']] = node
            if node.get('body'):
                self._discover_nodes(node['body'])
            if node.get('orelse'):
                self._discover_nodes(node['orelse'])

    def _get_input_as_ast(self, input_data: dict):
        if 'link' in input_data:
            link_id = input_data['link']
            if link_id not in self.node_map:
                raise ValueError(f"Node link '{link_id}' not found in graph.")
            if link_id not in self.expression_cache:
                self._build_node(self.node_map[link_id])
            return self.expression_cache[link_id]
        else:
            return ast.Constant(eval(input_data['value']))

    def _build_node(self, node: dict) -> ast.stmt | None:
        node_id = node['id']
        node_type = node['type']

        def get_input(name: str) -> dict:
            for i in node.get('inputs', []):
                if i['name'] == name:
                    return i
            raise ValueError(
                f"Node '{node_id}' is missing required input: '{name}'")

        if node_id not in self.expression_cache:
            if node_type == 'variable_assign':
                self.expression_cache[node_id] = ast.Name(
                    id=node['value'], ctx=ast.Load())
            elif node_type == 'binary_op':
                op_str = node['value']
                left = self._get_input_as_ast(get_input('left'))
                right = self._get_input_as_ast(get_input('right'))

                # FIX: Check which type of node to create.
                if op_str in self.BINOP_MAP:
                    op_class = self.BINOP_MAP[op_str]()
                    self.expression_cache[node_id] = ast.BinOp(
                        left=left, op=op_class, right=right)
                elif op_str in self.CMPOP_MAP:
                    op_class = self.CMPOP_MAP[op_str]()
                    # ast.Compare has a different structure!
                    self.expression_cache[node_id] = ast.Compare(
                        left=left, ops=[op_class], comparators=[right])
                else:
                    raise NotImplementedError(
                        f"Operator '{op_str}' is not implemented.")

        if node_id in self.compiled_statements:
            return None

        statement = None
        if node_type == 'variable_assign':
            target = ast.Name(id=node['value'], ctx=ast.Store())
            value = self._get_input_as_ast(get_input('value'))
            statement = ast.Assign(targets=[target], value=value)
        elif node_type == 'print':
            target = self._get_input_as_ast(get_input('target'))
            statement = ast.Expr(value=ast.Call(func=ast.Name(
                id='print', ctx=ast.Load()), args=[target], keywords=[]))
        elif node_type == 'if_statement':
            test = self._get_input_as_ast(get_input('test'))
            body = [stmt for n in node.get('body', []) if (
                stmt := self._build_node(n)) is not None]
            orelse = [stmt for n in node.get('orelse', []) if (
                stmt := self._build_node(n)) is not None]
            statement = ast.If(test=test, body=body, orelse=orelse)

        if statement:
            self.compiled_statements.add(node_id)
        return statement

    def compile(self) -> str:
        tree = ast.Module(body=[], type_ignores=[])
        for node in self.graph['nodes']:
            statement = self._build_node(node)
            if statement:
                tree.body.append(statement)
        ast.fix_missing_locations(tree)
        return ast.unparse(tree)


def build_ast_from_json(graph_json: dict) -> str:
    compiler = ASTCompiler(graph_json)
    return compiler.compile()
