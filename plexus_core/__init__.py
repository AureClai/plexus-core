# plexus_core/__init__.py

from .compiler import ASTCompiler, build_ast_from_json
from .decompiler import JSONDecompiler, decompile_python_to_json
from .inspector import generate_nodes_from_module, generate_nodes_from_module_name
from .tools.drawio_generator import generate_drawio_xml_from_json

# Define what gets imported with 'from plexus_core import *'
__all__ = [
    'ASTCompiler', 
    'build_ast_from_json', 
    'JSONDecompiler', 
    'decompile_python_to_json',
    'generate_nodes_from_module',
    'generate_nodes_from_module_name',
    'generate_drawio_xml_from_json'
]

__version__ = "0.4.0" # Bump the version
