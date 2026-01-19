import subprocess
from pathlib import Path
from typing import List, Dict, Any, Optional

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

    def get_gprof_profile(self) -> str:
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

    def profile(self,
        kwds: str = "",
        args: str = "",
    ) -> str:
        """
        Compiles, executes, and profiles the source file.
        """
        # Add a space if kwds is not empty
        compile_flags = kwds + (" " if kwds else "") + "-pg -no-pie -fno-builtin"
        
        # Use .stem and .suffix from the Path object
        gprof_exe = self.source_file.full_path.parent / (self.source_file.file_name.stem + "_gprof.out")

        self.source_file.compile(
            kwds=compile_flags,
            output_file=gprof_exe
        )
        
        if not self.source_file.is_compiled():
            return "Compilation failed."

        # Execute the binary to generate gmon.out
        self.source_file.execute(args=args)
        
        return self.get_gprof_profile()
