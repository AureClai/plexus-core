# plexus-core 🧩

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

## Roadmap for Polishing `plexus-core`

**Objective:** To enchance the feature set, robustness, and quality of the `plexus-core`library, ensuring it is production-ready.

### ✅ Phase 1: Core Engine (Initial Version) - Completed

- [x] Bi-directional compiler/decompiler structure.
- [x] Support for variables, print, math/comparison, and basic if/else.
- [x] Full test suite for core functionality and consistency.
- [x] Executable CLI via python -m plexus_core.
- [x] Professional documentation (README.md) and examples.

### 🏃 Phase 1.5: Polishing the Core (Current Focus)

This phase focuses on maturing the existing engine.

#### Stage 1: Solidifying Existing Features (High Priority)

- [x] **Full `if/elif/else` Decompiler Support:**
  - Our current visit_If decompiler handles simple if/else cases. We need to upgrade it to correctly parse:
    - `if` statements without an else block.
    - `elif` clauses (which are represented in the AST as a nested if statement in the `orelse` block of the parent if).
- [x] **Enhanced Error Handling & Validation:**
  - Improve the compiler's error messages for malformed JSON. Instead of a generic KeyError, raise a descriptive ValueError (e.g., "Node 'node-5' of type 'print' is missing required 'inputs' field.").
  - Add checks in the decompiler for unsupported Python syntax, providing a clear message to the user instead of failing silently.

#### Stage 2: Expanding Node Support (Medium Priority)

- [ ] **Loop Support: for Loops:**

  - This is the most important feature for making the tool practically useful.
  - JSON Definition: Define a for_loop node type (e.g., { "type": "for_loop", "target": "item", "iter_link": "my_list_node", "body": [...] }).
  - Compiler: Implement the ast.For node generation.
  - Decompiler: Implement the visit_For method to parse for loops back into the JSON graph.

- [ ] **Generic Function Calls:**

  - Right now, we only explicitly handle print(). We should generalize this.
  - JSON Definition: Create a call_function node type (e.g., { "type": "call_function", "func_name": "my_func", "inputs": [...] }).
  - Compiler/Decompiler: Update the logic to handle generating and parsing generic ast.Call nodes.

#### Stage 3: Advanced Features & Refinements (Future Polish)

- [ ] **Function Definition Support:**

  - Allow users to define their own functions within the graph.
  - JSON Definition: This would require a function_def node containing a name, arguments, and a body of nodes.
  - Decompiler: This is a significant challenge, as it requires more advanced scope management in the variable_providers map.

- [ ] **Comprehensive Docstrings & Code Comments:**

  - Perform a full pass over compiler.py and decompiler.py to add detailed docstrings to all methods and clarify complex logical blocks with inline comments. This greatly improves long-term maintainability.
