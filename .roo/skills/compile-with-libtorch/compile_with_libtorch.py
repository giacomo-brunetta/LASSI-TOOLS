import argparse
import sys
from pathlib import Path
from lassi.compiler import CompilerTool, Compiler

def main():
    parser = argparse.ArgumentParser(description="Compile C++ files with LibTorch.")
    parser.add_argument("--path", nargs="+", required=True, help="Path(s) to source file(s).")
    parser.add_argument("--kwds", help="Flags for GPP.")
    parser.add_argument("--includes", nargs="*", help="Include directories.")
    parser.add_argument("--libraries", nargs="*", help="Library directories.")
    parser.add_argument("--output", help="Output file name.")

    args = parser.parse_args()

    target_paths = [Path(p).resolve() for p in args.path]
    output_path = Path(args.output).resolve() if args.output else None

    for p in target_paths:
        if not p.exists():
            print(f"Compilation failed: File not found at {p}")
            sys.exit(1)

    try:
        torch_paths = CompilerTool.find_torchlib_paths()
        torch_inc = torch_paths["TORCH_INC"]
        torch_api_inc = torch_paths["TORCH_API_INC"]
        torch_lib = torch_paths["TORCH_LIB"]

        includes = list(args.includes) if args.includes else []
        includes.extend([str(torch_inc), str(torch_api_inc)])

        libraries = list(args.libraries) if args.libraries else []
        libraries.append(str(torch_lib))

        abi_flag = "-D_GLIBCXX_USE_CXX11_ABI=1"
        std_flag = "-std=c++17"

        flag_parts = []
        if args.kwds:
            flag_parts.append(args.kwds.strip())
        flag_parts.extend(["-O3", std_flag, abi_flag])
        
        lib_link_flags = [
            "-ltorch",
            "-ltorch_cpu",
            "-ltorch_cuda",
            "-lc10",
            "-lpthread",
            "-ldl",
            "-lrt",
            f"-Wl,-rpath,{torch_lib}",
        ]
        flag_parts.extend(lib_link_flags)

        kwds = " ".join(flag_parts)

        compiler_tool = CompilerTool(Compiler.GPP)
        result_path = compiler_tool.compile(
            files=target_paths,
            kwds=kwds,
            include_dirs=includes,
            library_dirs=libraries,
            output_file=output_path
        )
        print(f"Compilation successful. Binary created at: {result_path.name}")
    except Exception as e:
        print(f"Compilation failed: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()
