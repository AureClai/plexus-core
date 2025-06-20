# plexus_core/__main__.py

import argparse
import json
import sys
from .compiler import build_ast_from_json
from .decompiler import decompile_python_to_json


def main():
    """Provides the command-line interface for the plexus-core package.

    This function sets up and parses command-line arguments using `argparse`
    to allow users to compile and decompile files directly from the terminal.
    It orchestrates the reading of input files, calling the core library
    functions, and writing the output to the specified file or printing it
    to the standard output.

    The CLI supports two main commands:
    - `compile`: Converts a Plexus JSON graph into a Python script.
    - `decompile`: Converts a Python script into a Plexus JSON graph.

    Error handling for file operations and library exceptions is also included.

    .. rubric:: Usage Examples

    .. code-block:: bash

        # Decompile a script and print JSON to the console
        python -m plexus_core decompile path/to/script.py

        # Decompile a script and save the output to a file
        python -m plexus_core decompile path/to/script.py -o graph.json

        # Compile a graph and save the output to a script
        python -m plexus_core compile path/to/graph.json -o script.py

    """
    parser = argparse.ArgumentParser(
        prog="plexus-core",
        description="A tool to compile and decompile between Python code and Plexus JSON graphs."
    )
    # Create subparsers for the two main commands: compile and decompile
    subparsers = parser.add_subparsers(dest="command", required=True)

    # --- Decompile Command ---
    parser_decompile = subparsers.add_parser(
        "decompile",
        help="Decompile a Python script (.py) into a Plexus JSON graph."
    )
    parser_decompile.add_argument(
        "input_file",
        help="The path to the input Python file."
    )
    parser_decompile.add_argument(
        "-o", "--output",
        help="The path to the output JSON file. If omitted, prints to console."
    )

    # --- Compile Command ---
    parser_compile = subparsers.add_parser(
        "compile",
        help="Compile a Plexus JSON graph into a Python script."
    )
    parser_compile.add_argument(
        "input_file",
        help="The path to the input JSON file."
    )
    parser_compile.add_argument(
        "-o", "--output",
        help="The path to the output Python file. If omitted, prints to console."
    )

    args = parser.parse_args()

    try:
        if args.command == "decompile":
            print(f"-> Decompiling {args.input_file}...", file=sys.stderr)
            with open(args.input_file, 'r') as f:
                python_code = f.read()

            graph = decompile_python_to_json(python_code)

            if args.output:
                with open(args.output, 'w') as f:
                    json.dump(graph, f, indent=2)
                print(
                    f"✅ Success! Graph saved to {args.soutput}", file=sys.stderr)
            else:
                # Pretty-print JSON to the console
                print(json.dumps(graph, indent=2))

        elif args.command == "compile":
            print(f"-> Compiling {args.input_file}...", file=sys.stderr)
            with open(args.input_file, 'r') as f:
                graph = json.load(f)

            python_code = build_ast_from_json(graph)

            if args.output:
                with open(args.output, 'w') as f:
                    f.write(python_code)
                print(
                    f"✅ Success! Code saved to {args.output}", file=sys.stderr)
            else:
                print(python_code)

    except FileNotFoundError:
        print(
            f"Error: Input file not found at '{args.input_file}'", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"An error occurred: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
