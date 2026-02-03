import argparse
import sys
from pathlib import Path
from lassi.compiler import CompilerTool

def main():
    parser = argparse.ArgumentParser(description="Compile source files using LASSI tools.")
    parser.add_argument("--path", nargs="+", required=True, help="Path(s) to source file(s).")
    parser.add_argument("--compiler", required=True, help="Compiler to use (e.g., 'gcc', 'nvcc').")
    parser.add_argument("--kwds", help="Compiler flags.")
    parser.add_argument("--includes", nargs="*", help="Include directories.")
    parser.add_argument("--libraries", nargs="*", help="Library directories.")
    parser.add_argument("--output", help="Output binary name.")

    args = parser.parse_args()

    target_paths = [Path(p).resolve() for p in args.path]
    output_path = Path(args.output).resolve() if args.output else None

    for p in target_paths:
        if not p.exists():
            print(f"Compilation failed: File not found at {p}")
            sys.exit(1)

    try:
        compiler_tool = CompilerTool.from_string(args.compiler.lower())
        result_path = compiler_tool.compile(
            files=target_paths,
            kwds=args.kwds,
            include_dirs=args.includes,
            library_dirs=args.libraries,
            output_file=output_path
        )
        print(f"Compilation successful. Binary created at: {result_path.name}")
    except Exception as e:
        print(f"Compilation failed: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()
