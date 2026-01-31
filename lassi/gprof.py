import subprocess
import re
import json
from pathlib import Path
from typing import List, Dict, Any, Optional, Union, Iterable

from lassi.compiler import Language, CompilerTool
from lassi.source_file import SourceFile

def generate_profile_table(profile_data: List[Dict[str, Any]]) -> str:
    """
    Converts a list of gprof dictionaries into a Markdown table.
    """
    if not profile_data:
        return "No profiling data available."

    # Sort data by percent_time descending
    sorted_data = sorted(profile_data, key=lambda x: x.get('percent_time', 0), reverse=True)

    # Table Header
    lines = [
        "| Function Name | % Time | Self (s) | Calls | ms/call |",
        "| :--- | :---: | :---: | :---: | :---: |"
    ]

    for entry in sorted_data:
        name = entry.get('name', 'unknown')
        percent_time = entry.get('percent_time', 0.0)
        self_sec = entry.get('self_sec', 0.0)
        calls = entry.get('calls', '-')
        ms_per_call = entry.get('self_ms_per_call', '-')

        # Bold the function if it takes more than 50% of the time
        if isinstance(percent_time, (int, float)) and percent_time > 50:
            name = f"**{name}**"
        
        line = (
            f"| {name} | {percent_time}% | "
            f"{self_sec}s | {calls} | "
            f"{ms_per_call} |"
        )
        lines.append(line)

    return "\n".join(lines)

def parse_flat_profile(gprof_output: str) -> List[Dict[str, Any]]:
    """
    Parses the flat profile section of gprof output.
    """
    # Locate the Flat Profile section
    if "Flat profile:" not in gprof_output:
        return []

    lines = gprof_output.split('\n')
    start_parsing = False
    results = []

    for line in lines:
        line = line.strip()
        if not line:
            if start_parsing:
                break  # End of table
            continue
            
        # Headers end here; data starts after the column names
        if "time" in line and "seconds" in line:
            start_parsing = True
            continue
        
        if start_parsing:
            if "Copyright" in line or line.startswith("["):
                break
            
            # gprof output format:
            # % time  cumulative  self  calls  self ms/call  total ms/call  name
            # But calls and ms/call can be empty.
            
            parts = line.split()
            if len(parts) < 3:
                continue

            try:
                entry = {
                    "percent_time": float(parts[0]),
                    "cumulative_sec": float(parts[1]),
                    "self_sec": float(parts[2]),
                }
                
                # Check if we have calls information
                # If we have 7 parts, everything is there.
                # If we have 4 parts, it's %time, cumulative, self, name.
                # If we have more than 4, it's more complex.
                
                if len(parts) >= 7:
                    entry["calls"] = int(parts[3])
                    entry["self_ms_per_call"] = float(parts[4])
                    entry["total_ms_per_call"] = float(parts[5])
                    entry["name"] = " ".join(parts[6:])
                elif len(parts) == 4:
                    entry["calls"] = None
                    entry["self_ms_per_call"] = None
                    entry["total_ms_per_call"] = None
                    entry["name"] = parts[3]
                else:
                    # Best effort for other cases
                    entry["name"] = parts[-1]
                
                results.append(entry)
            except (ValueError, IndexError):
                continue

    return results

def parse_gprof_to_memory_schema(gprof_output: str):
    """
    Parses gprof text into mcp-memory entities and relations.
    Now includes a pre-cleaning step to strip file headers.
    """
    
    # 1. CLEANING REGEX: Remove everything before the table header
    # This strips command lines, granularity info, and preamble text.
    # We look for "index", followed by "%", followed by "time" with variable spacing.
    gprof_output = re.sub(
        r"(?s)^.*?(?=index\s+%\s+time)", 
        "", 
        gprof_output, 
        flags=re.DOTALL
    )

    # 2. Split into blocks based on dashed lines
    blocks = re.split(r'-{10,}', gprof_output)
    
    entities_map = {}
    relations = []

    for block in blocks:
        lines = block.strip().split('\n')
        if not lines: continue

        # Identify Focus Line
        focus_idx = -1
        for i, line in enumerate(lines):
            # Skip the header line itself if it appears in the block
            if "index" in line and "%" in line and "time" in line: continue
            
            if re.match(r'^\s*\[(\d+)\]', line):
                focus_idx = i
                break
        
        if focus_idx == -1: continue

        # --- 3. Parse Node & Attributes ---
        match = re.search(r'\[(\d+)\]\s+([\d\.]+)?\s*([\d\.]+)?\s*([\d\.]+)?\s+(?:[\d/]+)?\s+([^\s]+)', lines[focus_idx])
        if match:
            idx, pct, self_t, child_t, name = match.groups()
            
            # Attributes as JSON string
            attributes = {
                "gprof_index": int(idx) if idx else None,
                "percent_time": float(pct) if pct else 0.0,
                "self_time_sec": float(self_t) if self_t else 0.0,
                "children_time_sec": float(child_t) if child_t else 0.0
            }
            json_observation = json.dumps(attributes)

            entities_map[name] = {
                "name": name,
                "entityType": "function",
                "observations": [json_observation]
            }
            
            # Helper for edge weights
            def extract_calls(txt):
                m = re.search(r'\s(\d+)(?:/\d+)?\s+[^\s]+\s*(?:\[\d+\])?$', txt)
                return m.group(1) if m else None

            # --- 4. Incoming Edges (Callers) ---
            for i in range(0, focus_idx):
                line = lines[i].strip()
                if not line or ("index" in line and "%" in line): continue

                if "<spontaneous>" in line:
                    relations.append({"from": "ROOT", "to": name, "relationType": "spawns"})
                else:
                    parts = line.split()
                    if len(parts) >= 2:
                        caller = parts[-2] if parts[-1].startswith('[') else parts[-1]
                        calls = extract_calls(line)
                        rel_type = f"calls ({calls})" if calls else "calls"

                        if caller not in entities_map:
                            entities_map[caller] = {
                                "name": caller,
                                "entityType": "function",
                                "observations": ["{\"status\": \"stub_node\"}"]
                            }
                        relations.append({"from": caller, "to": name, "relationType": rel_type})

            # --- 5. Outgoing Edges (Callees) ---
            for i in range(focus_idx + 1, len(lines)):
                line = lines[i].strip()
                parts = line.split()
                if len(parts) >= 2:
                    callee = parts[-2] if parts[-1].startswith('[') else parts[-1]
                    calls = extract_calls(line)
                    rel_type = f"calls ({calls})" if calls else "calls"

                    if callee not in entities_map:
                        entities_map[callee] = {
                            "name": callee,
                            "entityType": "function",
                            "observations": ["{\"status\": \"stub_node\"}"]
                        }
                    relations.append({"from": name, "to": callee, "relationType": rel_type})

    return list(entities_map.values()), relations

class GProf:
    """
    A class to handle gprof profiling for a source file.
    """

    def __init__(self,
                 target: Path,
                 lang: Optional[Language] = None,
                 compiler_tool: Optional[CompilerTool] = None
                 ):
        
        # Ensure target is a Path
        target = Path(target)
        
        # SourceFile expects file_name to be a Path for .suffix/.stem access
        # and full_path = folder_path / file_name
        self.source_file = SourceFile(
            file_name=Path(target.name),
            folder_path=target.parent,
            lang=lang,
            compiler_tool=compiler_tool
        )

    def get_gprof_flat_profile(self) -> str:
        """
        Runs gprof on the compiled executable and returns a Markdown table.
        """
        if not self.source_file.executable:
            return "Executable not found. Did you compile and run first?"

        # Ensure we are pointing to the executable correctly
        exe_path = self.source_file.executable.resolve()
        
        cmd = ["gprof", str(exe_path), "gmon.out", "-p"]

        print(f"Profiling with gprof: {' '.join(cmd)}")

        gprof_result = subprocess.run(
            cmd,
            capture_output=True,
            text=True
        )

        if gprof_result.returncode != 0:
            return f"gprof failed: {gprof_result.stderr.strip()}"

        flat_profile_data = parse_flat_profile(gprof_result.stdout)
        return generate_profile_table(flat_profile_data)

    def get_call_graph_profile(self) -> str:
        """
        Runs gprof on the compiled executable and returns call graph data.
        """
        if not self.source_file.executable:
            return "Executable not found. Did you compile and run first?"

        exe_path = self.source_file.executable.resolve()
        
        cmd = ["gprof", str(exe_path), "gmon.out", "-q"]

        print(f"Profiling with gprof (call graph): {' '.join(cmd)}")

        gprof_result = subprocess.run(
            cmd,
            capture_output=True,
            text=True
        )

        if gprof_result.returncode != 0:
            return f"gprof failed: {gprof_result.stderr.strip()}"

        call_graph_data = parse_gprof_to_memory_schema(gprof_result.stdout)
        # For simplicity, just returning a placeholder string
        return call_graph_data

    def profile(self,
        kwds: str = "",
        args: str = "",
        include_dirs: Optional[Union[Path, Iterable[Path]]] = None,
        library_dirs: Optional[Union[Path, Iterable[Path]]] = None,
        extra_files: Optional[Union[Path, Iterable[Path]]] = None,
        type: str = "flat"
    ) -> str:
        """
        Compiles, executes, and profiles the source file.
        """
        # Add a space if kwds is not empty
        compile_flags = (kwds if kwds else "") + (" " if kwds else "") + "-pg -no-pie -fno-builtin"
        
        # Use .stem and .suffix from the Path object
        gprof_exe = self.source_file.full_path.parent / (self.source_file.file_name.stem + "_gprof.out")

        self.source_file.compile(
            kwds=compile_flags,
            include_dirs=include_dirs,
            library_dirs=library_dirs,
            extra_files=extra_files,
            output_file=gprof_exe
        )
        
        if not self.source_file.is_compiled():
            return "Compilation failed."

        # Execute the binary to generate gmon.out
        self.source_file.execute(args=args)
        
        if type == "flat":
            return self.get_gprof_flat_profile()
        elif type == "callgraph":
            # Call graph parsing not implemented
            return "Call graph profiling not implemented yet."
        elif type == "both":
            flat_profile = self.get_gprof_flat_profile()
            call_graph = "Call graph profiling not implemented yet."
            return flat_profile + "\n\n" + call_graph
        else:
            return f"Unknown profiling type: {type}"
