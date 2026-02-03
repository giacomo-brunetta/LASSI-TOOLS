import argparse
import sys
from pathlib import Path
import os
# Resolve lassi dependency
skill_dir = os.path.dirname(os.path.abspath(__file__))
lassi_tools_dir = os.path.abspath(os.path.join(skill_dir, "..", "..", ".."))
if lassi_tools_dir not in sys.path:
    sys.path.insert(0, lassi_tools_dir)
from lassi.compiler import CompilerTool, Compiler

def main():
    parser = argparse.ArgumentParser(description="Compile source files to MLIR using cgeist.")
    parser.add_argument("--path", nargs="+", required=True, help="Path(s) to source file(s).")
    parser.add_argument("--kwds", help="Specific flags for cgeist.")
    parser.add_argument("--includes", nargs="*", help="Include directories.")
    parser.add_argument("--libraries", nargs="*", help="Library directories.")
    parser.add_argument("--output", help="Output MLIR file name.")

    args = parser.parse_args()

    target_paths = [Path(p).resolve() for p in args.path]
    output_path = Path(args.output).resolve() if args.output else None

    for p in target_paths:
        if not p.exists():
            print(f"MLIR generation failed: File not found at {p}")
            sys.exit(1)

    try:
        compiler_tool = CompilerTool(Compiler.CGEIST)
        result_path = compiler_tool.compile(
            files=target_paths,
            kwds=args.kwds,
            include_dirs=args.includes,
            library_dirs=args.libraries,
            output_file=output_path
        )
        print(f"MLIR generation successful. Output file: {result_path.name}")
    except Exception as e:
        print(f"MLIR generation failed: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()
