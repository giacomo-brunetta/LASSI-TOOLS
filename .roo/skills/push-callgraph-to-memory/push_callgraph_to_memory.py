import argparse
import sys
import asyncio
import json
import shutil
from pathlib import Path
from lassi.gprof import GProf
from lassi.compiler import CompilerTool
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

async def push_callgraph():
    parser = argparse.ArgumentParser(description="Generate gprof callgraph and push to memory.")
    parser.add_argument("--path", nargs="+", required=True, help="Path(s) to source file(s).")
    parser.add_argument("--compiler", help="Compiler to use.")
    parser.add_argument("--kwds", help="Compiler flags.")
    parser.add_argument("--includes", nargs="*", help="Include directories.")
    parser.add_argument("--libraries", nargs="*", help="Library directories.")
    parser.add_argument("--args", default="", help="Command line arguments for execution.")

    args = parser.parse_args()

    if len(args.path) == 1:
        target_path = Path(args.path[0]).resolve()
        extra_files = None
    else:
        target_path = Path(args.path[0]).resolve()
        extra_files = [Path(p).resolve() for p in args.path[1:]]
    
    gprofile = GProf(
        target_path,
        compiler_tool=CompilerTool.from_string(args.compiler.lower()) if args.compiler else None
    )

    compile_flags = (args.kwds + " " if args.kwds else "") + "-pg -no-pie -fno-builtin"
    gprof_exe = gprofile.source_file.full_path.parent / (gprofile.source_file.file_name.stem + "_gprof.out")

    gprofile.source_file.compile(
        kwds=compile_flags,
        include_dirs=args.includes,
        library_dirs=args.libraries,
        extra_files=extra_files,
        output_file=gprof_exe
    )
    
    if not gprofile.source_file.is_compiled():
        print("Compilation failed.")
        sys.exit(1)

    gprofile.source_file.execute(args=args.args)

    if not gprofile.source_file.executable:
        print("Executable not found.")
        sys.exit(1)

    exe_path = gprofile.source_file.executable.resolve()
    cmd = ["gprof", str(exe_path), "gmon.out", "-q"]

    import subprocess
    gprof_result = subprocess.run(cmd, capture_output=True, text=True)

    if gprof_result.returncode != 0:
        print(f"gprof failed: {gprof_result.stderr.strip()}")
        sys.exit(1)

    from lassi.gprof import parse_gprof_to_memory_schema
    entities, relations = parse_gprof_to_memory_schema(gprof_result.stdout)

    unique_rels = []
    seen = set()
    for r in relations:
        key = (r['from'], r['to'], r['relationType'])
        if key not in seen:
            seen.add(key)
            unique_rels.append(r)

    docker_path = shutil.which("docker")
    if not docker_path:
        print("Docker not found. Cannot connect to memory server.")
        sys.exit(1)

    server_params = StdioServerParameters(
        command=docker_path,
        args=["run", "-i", "--rm", "-v", "mcp-memory-data:/app/dist", "mcp/memory"]
    )

    try:
        async with stdio_client(server_params) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
                
                nodes_pushed = 0
                edges_pushed = 0

                if entities:
                    await session.call_tool("create_entities", arguments={"entities": entities})
                    nodes_pushed = len(entities)
                
                if unique_rels:
                    await session.call_tool("create_relations", arguments={"relations": unique_rels})
                    edges_pushed = len(unique_rels)

                print(f"Successfully pushed callgraph to memory: {nodes_pushed} nodes, {edges_pushed} edges.")
    except Exception as e:
        print(f"Failed to push to memory server: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(push_callgraph())
