# plexus_core/inspector.py

import inspect
import importlib
from types import ModuleType, BuiltinFunctionType

def generate_nodes_from_module(module: ModuleType) -> list[dict]:
    """
    Inspects a Python module and generates a list of Plexus node definitions
    for each public function found.

    :param module: The loaded Python module object to inspect.
    :type module: ModuleType
    :return: A list of dictionaries, where each dictionary represents a
             function and can be used to generate a UI node.
    :rtype: list[dict]
    """
    node_definitions = []
    
    # FIX: Determine the correct module name for display, accommodating class-based mocks.
    module_name_for_display = module.__name__
    if inspect.isclass(module) and '__name__' in module.__dict__:
        module_name_for_display = module.__dict__['__name__']

    # Iterate over all members of the module
    for name, member in inspect.getmembers(module):
        # Check for both regular functions and C-based built-ins.
        if not (inspect.isfunction(member) or inspect.isbuiltin(member)):
            continue
            
        # Skip private functions (by convention)
        if name.startswith('_'):
            continue

        try:
            sig = inspect.signature(member)
            doc = inspect.getdoc(member) or "No documentation available."

            # --- Build the inputs for the node ---
            inputs = []
            for param in sig.parameters.values():
                # We will only support simple positional/keyword arguments for now
                if param.kind in (inspect.Parameter.POSITIONAL_OR_KEYWORD, inspect.Parameter.POSITIONAL_ONLY):
                    inputs.append({
                        "name": param.name,
                        "type_hint": str(param.annotation) if param.annotation != inspect.Parameter.empty else None,
                        "required": param.default == inspect.Parameter.empty
                    })
                else:
                    # If we find *args, **kwargs, etc., we can't support this function yet.
                    raise TypeError(f"Unsupported parameter kind: {param.kind}")


            # --- Build the outputs for the node ---
            outputs = []
            if sig.return_annotation != inspect.Signature.empty:
                outputs.append({
                    "name": "return",
                    "type_hint": str(sig.return_annotation)
                })

            # --- Assemble the final node definition ---
            node_def = {
                "node_type": "call_function", # This node becomes a generic function call
                "display_name": f"{module_name_for_display}.{name}",
                "func_name": name,
                "module": module_name_for_display, # Use the corrected name here as well
                "doc": doc,
                "inputs": inputs,
                "outputs": outputs
            }
            node_definitions.append(node_def)
            
        except (ValueError, TypeError):
            # Some functions might not be inspectable, or they might have parameter 
            # types we don't support (like *args). We can safely skip them.
            continue
    
    return node_definitions


def generate_nodes_from_module_name(module_name: str) -> list[dict]:
    """
    A convenience wrapper to load a module by its string name and then
    generate node definitions from it.

    :param module_name: The name of the module to import (e.g., "math").
    :type module_name: str
    :raises ImportError: If the module cannot be found.
    :return: A list of Plexus node definitions.
    :rtype: list[dict]
    """
    try:
        module = importlib.import_module(module_name)
        return generate_nodes_from_module(module)
    except ImportError as e:
        print(f"Error: Could not import module '{module_name}'")
        raise e
