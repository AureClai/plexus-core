# plexus-core 🧩

<p align="center"><img src="https://github.com/AureClai/plexus-core/tree/main/img/logo.png" alt="plexus-core logo" width="300"></p>

**A powerful Python library for bi-directional translation between Python code and a JSON node graph.**

[![PyPI version](https://img.shields.io/pypi/v/plexus-core.svg)](https://pypi.org/project/plexus-core/)
[![Python Version](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

_(Note: The PyPI badge is a placeholder for when the package is published.)_

`plexus-core` is a dependency-free Python library that uses the built-in `ast` module to serve as a powerful translation engine. It can convert a defined JSON graph into executable Python code and decompile Python code back into the JSON graph structure.

This library forms the logical heart of applications that require a robust, bi-directional relationship between code and a visual graph representation.

## ✨ Core Features

- **Compile JSON to Python:** Translates a JSON-defined node graph into clean, executable Python code.
- **Decompile Python to JSON:** Reverses the process, parsing Python scripts to generate the corresponding JSON graph structure.
- **Intelligent Linking:** The decompiler automatically detects variable usage to create connections between nodes.
- **Core Node Support:** The engine currently supports a crucial set of nodes for building logic:
  - Variable Assignment
  - `print()` calls
  - Arithmetic (`+`, `-`, `*`, `/`) and Comparison (`==`, `>=`, `<`, etc.)
  - `if/else` conditional statements with nested blocks.

## 🔧 Installation

Install the package using pip.

```bash
pip install plexus-core
```

(Note: This package is not yet published to PyPI. For now, please use the "Installation for Development" method below.)

## ⚙️ Usage

### As a Command-Line Tool

After installation, you can use `plexus-core` directly from your teminal.

```bash
# Get help for the tool and its commands
python -m plexus_core -h
python -m plexus_core compile -h

# Compile a JSON file and print the Python code to the console
python -m plexus_core compile path/to/your/graph.json

# Decompile a Python script and save the output to a new JSON file
python -m plexus_core decompile path/to/your/script.py -o new_graph.json
```

### As Python Library

You can use the plexus-core functions directly in any Python script after installation.

#### Example 1: Compiling JSON to Python

```python
from plexus_core import build_ast_from_json
import json

# Define a graph for:
# age = 21
# if age >= 18: print("OK")
graph = {
    "nodes": [
        {"id": "a", "type": "variable_assign", "value": "age", "inputs": [{"name": "value", "value": "21"}]},
        {"id": "b", "type": "binary_op", "value": ">=", "inputs": [{"name": "left", "link": "a"}, {"name": "right", "value": "18"}]},
        {"id": "c", "type": "if_statement", "inputs": [{"name": "test", "link": "b"}],
            "body": [{"id": "d", "type": "print", "inputs": [{"name": "target", "value": "'OK'"}]}],
            "orelse": []
        }
    ]
}

python_code = build_ast_from_json(graph)
print("--- Generated Python Code ---")
print(python_code)
```

#### Example 2: Decompiling Python to JSON

```python
from plexus_core import decompile_python_to_json
import json

python_code = """
price = 100
if price > 50:
    print("Expensive")
else:
    print("Cheap")
"""

graph = decompile_python_to_json(python_code)
print("--- Generated JSON Graph ---")
print(json.dumps(graph, indent=2))
```

### Example 3: Inspecting a module

```python
from plexus_core import generate_nodes_from_module_name
import json
import math

# Generate node definitions from the built-in 'math' module
math_nodes = generate_nodes_from_module_name("math")

# Find the definition for the 'sin' function
sin_node_def = next(n for n in math_nodes if n['func_name'] == 'sin')

print("--- Inspected Node Definition for 'math.sin' ---")
print(json.dumps(sin_node_def, indent=2))
```

## 🧑‍💻 Development & Testing

To contribute or run the tests locally, please follow these steps.

1. Clone the repository:

```bash
git clone [https://github.com/AureClai/plexus-core.git](https://github.com/AureClai/plexus-core.git)
cd plexus-core
```

2. Create and activate a virtual environment:

```bash
python -m venv venv
venv\Scripts\activate  # On Windows
# source venv/bin/activate  # On macOS/Linux
```

3. Install in editable mode and for testing:

```bash
pip install pytest
pip install -e .
```

4. Run the test suite:

```bash
pytest
```

## 📜 License

This project is licensed under the MIT License.

## 🗺️ Project Roadmap
The core engine is now feature-rich and stable. The next steps will focus on refining the existing feature set and preparing for integration into a larger application.

- [x] Full if/elif/else Decompiler Support
- [x] Enhanced Error Handling & Validation
- [x] for Loop Support
- [x] Generic Function Call Support
- [x] Module Introspection for Node Generation
- [ ] Function Definition Support: Allow users to define their own functions within the graph.
- [ ] Comprehensive Docstrings: Perform a final pass to add detailed docstrings to all methods.
- [ ] Phase 2 - API Layer: Begin development of a Flask/FastAPI wrapper to expose the engine's functionality over HTTP.
