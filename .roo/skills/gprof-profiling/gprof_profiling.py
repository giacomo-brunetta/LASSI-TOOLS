import argparse
import sys
from pathlib import Path
import os
# Resolve lassi dependency
skill_dir = os.path.dirname(os.path.abspath(__file__))
lassi_tools_dir = os.path.abspath(os.path.join(skill_dir, "..", "..", ".."))
if lassi_tools_dir not in sys.path:
    sys.path.insert(0, lassi_tools_dir)
from lassi.gprof import GProf
from lassi.compiler import CompilerTool

def main():
    parser = argparse.ArgumentParser(description="Profile source files using gprof.")
    parser.add_argument("--path", nargs="+", required=True, help="Path(s) to source file(s).")
    parser.add_argument("--compiler", help="Compiler to use (e.g., 'gcc', 'nvcc').")
    parser.add_argument("--kwds", help="Compiler flags (e.g., '-O3 -Wall').")
    parser.add_argument("--includes", nargs="*", help="Include directories.")
    parser.add_argument("--libraries", nargs="*", help="Library directories.")
    parser.add_argument("--args", default="", help="Command line arguments for the executable.")

    args = parser.parse_args()

    target_path = Path(args.path[0]).resolve()
    extra_files = [Path(p).resolve() for p in args.path[1:]] if len(args.path) > 1 else None
    
    try:
        compiler_tool = CompilerTool.from_string(args.compiler.lower()) if args.compiler else None
        gprofile = GProf(target_path, compiler_tool=compiler_tool)

        result = gprofile.profile(
            args=args.args,
            kwds=args.kwds if args.kwds else "",
            include_dirs=args.includes,
            library_dirs=args.libraries,
            extra_files=extra_files,
        )
        print(result)
    except Exception as e:
        print(f"Profiling failed: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()
