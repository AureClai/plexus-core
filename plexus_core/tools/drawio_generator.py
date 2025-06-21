# plexus_core/tools/drawio_generator.py

import json
from xml.etree.ElementTree import Element, SubElement, tostring
from xml.dom import minidom
import html
import zlib
import base64
import urllib.parse

class DrawIOBlueprintGenerator:
    """
    Converts a Plexus JSON graph into a Draw.io XML file with a visual
    style inspired by Unreal Engine's Blueprints, showing both execution
    and data flow.
    """
    # --- Style Definitions ---
    STYLE_HEADER_MAP = {
        "variable_assign": "fillColor=#005c91;",
        "call_function": "fillColor=#007d6b;",
        "if_statement": "fillColor=#9a2424;",
        "for_loop": "fillColor=#8213a1;",
        "binary_op": "fillColor=#4e6482;",
        "default": "fillColor=#3F3F3F;"
    }
    STYLE_EXEC_EDGE = "edgeStyle=orthogonalEdgeStyle;rounded=0;orthogonalLoop=1;jettySize=auto;html=1;strokeColor=#FFFFFF;strokeWidth=3;"
    STYLE_DATA_EDGE = "edgeStyle=orthogonalEdgeStyle;rounded=0;orthogonalLoop=1;jettySize=auto;html=1;strokeColor=#6296C0;strokeWidth=1.5;"
    
    NODE_WIDTH = 220
    X_SPACING = 300
    Y_SPACING = 60

    def __init__(self, graph_json: dict):
        self.graph = graph_json
        self.node_map = {node['id']: node for node in graph_json.get('nodes', []) if 'id' in node}
        self.root_xml = Element('mxGraphModel', {'grid': '1', 'gridSize': '10', 'guides': '1', 'tooltips': '1', 'connect': '1', 'arrows': '1'})
        
        root_cell = SubElement(self.root_xml, 'root')
        SubElement(root_cell, 'mxCell', id='0')
        SubElement(root_cell, 'mxCell', id='1', parent='0')
        
        self.node_positions = {}
        self.node_heights = {}
        # FIX: The attribute name must be 'statement_nodes' to match what other methods use.
        self.statement_nodes = self._find_top_level_statements()

    def _is_statement(self, node: dict) -> bool:
        """Determines if a node type can be a statement."""
        return node.get("type") in ["variable_assign", "call_function", "if_statement", "for_loop"]
    
    def _find_top_level_statements(self) -> list:
        """Finds nodes that are not linked to as data inputs, which are the start of execution chains."""
        all_node_ids = set(self.node_map.keys())
        linked_ids = set()
        for node in self.node_map.values():
            for an_input in node.get('inputs', []):
                if an_input.get('link'):
                    linked_ids.add(an_input['link'])
        
        top_level_ids = all_node_ids - linked_ids
        # Maintain the original order from the JSON file for top-level statements
        return [node for node in self.graph.get('nodes', []) if node.get('id') in top_level_ids and self._is_statement(node)]

    def _generate_html_label(self, node: dict) -> str:
        node_type = node.get('type', 'node')
        header_color = self.STYLE_HEADER_MAP.get(node_type, self.STYLE_HEADER_MAP['default'])
        
        if node_type == "if_statement": header_text = "Branch"
        elif node_type == "for_loop": header_text = "For Each Loop"
        else: header_text = f"{node.get('func_name') or node.get('value') or node_type.replace('_', ' ').title()}"
        
        header_html = f'<td colspan="3" style="padding:8px;text-align:left;background-color:{header_color};border-bottom:1px solid #000000;"><font color="#ffffff"><b>&#9654; {html.escape(header_text)}</b></font></td>'

        inputs_html, outputs_html = "", ""
        if self._is_statement(node):
            inputs_html += f'<tr><td port="in_exec" align="left">&#9654;</td><td align="left" style="padding:0 5px;"></td></tr>'
            if node_type == 'if_statement':
                outputs_html += f'<tr><td align="right">True</td><td port="out_exec_true" align="right" style="padding:0 5px;">&#9654;</td></tr>'
                outputs_html += f'<tr><td align="right">False</td><td port="out_exec_false" align="right" style="padding:0 5px;">&#9654;</td></tr>'
            elif node_type == 'for_loop':
                outputs_html += f'<tr><td align="right">Loop Body</td><td port="out_exec_loop" align="right" style="padding:0 5px;">&#9654;</td></tr>'
                outputs_html += f'<tr><td align="right">Completed</td><td port="out_exec_completed" align="right" style="padding:0 5px;">&#9654;</td></tr>'
            else:
                 outputs_html += f'<tr><td align="right"> </td><td port="out_exec" align="right" style="padding:0 5px;">&#9654;</td></tr>'
        
        for an_input in node.get('inputs', []):
            input_name = html.escape(an_input.get("name", ""))
            inputs_html += f'<tr><td port="in_{input_name}" align="left">&#9679;</td><td align="left" style="padding:0 5px;">{input_name}</td></tr>'

        if node_type in ['variable_assign', 'binary_op', 'call_function', 'for_loop']:
            output_name = "return" if node_type == 'call_function' else 'value'
            if node_type == 'for_loop': output_name = 'Array Element'
            outputs_html += f'<tr><td align="right">{output_name}</td><td port="out_data" align="right" style="padding:0 5px;">&#9679;</td></tr>'

        body_html = f'<tr><td valign="top"><table cellpadding="2" style="font-size:11px;color:#C0C0C0;">{inputs_html}</table></td><td></td><td valign="top"><table cellpadding="2" style="font-size:11px;color:#C0C0C0;">{outputs_html}</table></td></tr>'
        table = f'<table style="width:100%;border-collapse:collapse;">{header_html}{body_html}</table>'
        return ''.join(line.strip() for line in table.split('\n'))
    
    def _calculate_node_height(self, node: dict) -> int:
        num_inputs = len(node.get('inputs', []))
        num_outputs = 1
        if self._is_statement(node): num_inputs += 1
        if node.get('type') in ['if_statement', 'for_loop']: num_outputs = 2
        return 50 + max(num_inputs, num_outputs) * 20

    def _layout_dependency_nodes(self, node_id: str, x: int, y: int):
        if node_id not in self.node_map: return
        node = self.node_map[node_id]
        
        current_y = y
        for an_input in node.get('inputs', []):
            link_id = an_input.get('link')
            if link_id and link_id not in self.node_positions:
                child_node = self.node_map.get(link_id)
                if child_node:
                    child_x = x - self.X_SPACING
                    self.node_positions[link_id] = (child_x, current_y)
                    self._layout_dependency_nodes(link_id, child_x, current_y)
                    current_y += self.node_heights.get(link_id, 100) + self.Y_SPACING

    def _layout_execution_flow(self, exec_sequence, x, y):
        current_x, current_y = x, y
        max_y_in_branch = y
        
        for node_data in exec_sequence:
            node_id = node_data['id']
            if node_id in self.node_positions: continue
            
            self.node_positions[node_id] = (current_x, current_y)
            self._layout_dependency_nodes(node_id, current_x, current_y)
            
            node_height = self.node_heights.get(node_id, 100)
            node = self.node_map[node_id]
            
            branch_y_start = current_y + node_height + self.Y_SPACING
            if node.get('type') == 'if_statement':
                true_branch_y = self._layout_execution_flow(node.get('body', []), current_x + self.X_SPACING, current_y)
                false_branch_y = self._layout_execution_flow(node.get('orelse', []), current_x + self.X_SPACING, true_branch_y)
                max_y_in_branch = max(max_y_in_branch, false_branch_y)
            elif node.get('type') == 'for_loop':
                 max_y_in_branch = max(max_y_in_branch, self._layout_execution_flow(node.get('body', []), current_x + self.X_SPACING, current_y))
            
            current_y += node_height + self.Y_SPACING
            max_y_in_branch = max(max_y_in_branch, current_y)
            
        return max_y_in_branch

    def _calculate_layout(self):
        for node_id, node in self.node_map.items():
            self.node_heights[node_id] = self._calculate_node_height(node)
        self._layout_execution_flow(self.statement_nodes, 0, 0)
        
    def _generate_nodes_xml(self):
        for node_id, node in self.node_map.items():
            label_html = self._generate_html_label(node)
            style = "shape=plain;html=1;verticalAlign=top;align=left;spacing=4;fillColor=#282828;strokeColor=#000000;fontColor=#FFFFFF;rounded=1;"
            x, y = self.node_positions.get(node_id, (0, 0))
            height = self.node_heights.get(node_id, 80)
            
            SubElement(self.root_xml.find('root'), 'mxCell', {
                'id': node_id, 'value': label_html, 'style': style, 'vertex': '1', 'parent': '1'
            }).append(Element('mxGeometry', {'x': str(x), 'y': str(y), 'width': str(self.NODE_WIDTH), 'height': str(height), 'as': 'geometry'}))

    def _generate_edges_xml(self):
        # --- Data Edges ---
        for node_id, node in self.node_map.items():
            for i, an_input in enumerate(node.get('inputs', [])):
                link_id = an_input.get('link')
                if link_id and link_id in self.node_map:
                    edge_id = f"data-edge-{link_id}-{node_id}-{i}"
                    SubElement(self.root_xml.find('root'), 'mxCell', { 'id': edge_id, 'style': self.STYLE_DATA_EDGE, 'edge': '1', 'parent': '1', 'source': link_id, 'target': node_id })
        
        # --- Execution Edges ---
        exec_connections = []
        def find_next_statement(start_index):
            if start_index < len(self.statement_nodes) - 1:
                return self.statement_nodes[start_index + 1]['id']
            return None

        for i, node_data in enumerate(self.statement_nodes):
            node_id = node_data['id']
            node_type = node_data['type']
            next_node_id = find_next_statement(i)

            if node_type == 'if_statement':
                if node_data.get('body'): exec_connections.append((node_id, node_data['body'][0]['id']))
                if node_data.get('orelse'): exec_connections.append((node_id, node_data['orelse'][0]['id']))
            elif node_type == 'for_loop':
                if node_data.get('body'): exec_connections.append((node_id, node_data['body'][0]['id']))
                if next_node_id: exec_connections.append((node_id, next_node_id)) # 'Completed' exec
            elif next_node_id:
                exec_connections.append((node_id, next_node_id))
        
        for i, (source, target) in enumerate(exec_connections):
             SubElement(self.root_xml.find('root'), 'mxCell', {'id': f'exec-edge-{i}', 'style': self.STYLE_EXEC_EDGE, 'edge': '1', 'parent': '1', 'source': source, 'target': target})

    def generate_xml(self) -> str:
        """The main method to generate the full Draw.io XML string."""
        self._calculate_layout()
        self._generate_nodes_xml()
        self._generate_edges_xml()

        mxfile = Element('mxfile', {'host': 'plexus.dev', 'agent': '1.0', 'type': 'device'})
        diagram = SubElement(mxfile, 'diagram', {'id': 'diagram-1', 'name': 'Plexus Blueprint'})
        
        graph_xml_string = tostring(self.root_xml, 'utf-8')
        compressed = zlib.compress(graph_xml_string, wbits=-15)
        encoded_bytes = base64.b64encode(compressed)
        encoded_str = encoded_bytes.decode('ascii')
        url_encoded = urllib.parse.quote(encoded_str)
        
        diagram.text = url_encoded
        
        xml_str = tostring(mxfile, 'unicode')
        dom = minidom.parseString(xml_str)
        return dom.toprettyxml(indent="  ")


def generate_drawio_xml_from_json(graph_json: dict) -> str:
    generator = DrawIOBlueprintGenerator(graph_json)
    return generator.generate_xml()
