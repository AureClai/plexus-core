# examples/run_decompiler.py

import json
from plexus_core import decompile_python_to_json
import os

# Define file paths relative to this script
INPUT_FILE = "input_script.py"
SUB_DIRECTORY = "files_generated"
OUTPUT_FILE = "generated_graph.json"
CURRENT_DIR = os.path.dirname(__file__)


def main():
    """Reads a Python script, decompiles it, and saves the JSON graph."""
    print(f"--- Running Plexus Decompiler ---")

    # Read the input Python code
    input_path = os.path.join(CURRENT_DIR, INPUT_FILE)
    print(f"Reading Python code from: {input_path}")
    with open(input_path, 'r') as f:
        python_code = f.read()

    # Decompile the code to a JSON graph
    graph = decompile_python_to_json(python_code)

    # Save the generated code to a file
    if not os.path.exists(os.path.join(CURRENT_DIR, SUB_DIRECTORY)):
        os.makedirs(os.path.join(CURRENT_DIR, SUB_DIRECTORY))
        print(f"Creating directory: {SUB_DIRECTORY}")
    else:
        print(f"Directory {SUB_DIRECTORY} already exists.")
    output_path = os.path.join(CURRENT_DIR, SUB_DIRECTORY, OUTPUT_FILE)
    print(f"Saving generated JSON graph to: {output_path}")
    with open(output_path, 'w') as f:
        json.dump(graph, f, indent=2)

    print("\nDecompilation complete!")
    print(f"Run 'cat {OUTPUT_FILE}' or open it to see the result.")


if __name__ == "__main__":
    main()
