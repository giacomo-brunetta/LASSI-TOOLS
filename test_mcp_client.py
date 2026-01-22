import asyncio
import re
import json
import shutil
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

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

# --- Execution ---
async def main():
    # Example showing dirty input that gets cleaned
    gprof_data = """Call graph (explanation follows)


granularity: each sample hit covers 4 byte(s) for 0.21% of 4.85 seconds

index % time    self  children    called     name
                4.85    0.00       1/1           main [2]
[1]    100.0    4.85    0.00       1         matrix_multiply [1]
-----------------------------------------------
                                                 <spontaneous>
[2]    100.0    0.00    4.85                 main [2]
                4.85    0.00       1/1           matrix_multiply [1]
                0.00    0.00       1/1           init_matrices [3]
-----------------------------------------------
                0.00    0.00       1/1           main [2]
[3]      0.0    0.00    0.00       1         init_matrices [3]
-----------------------------------------------
)"""
    
    print("Parsing...")
    entities, relations = parse_gprof_to_memory_schema(gprof_data)
    
    # Deduplicate relations
    unique_rels = []
    seen = set()
    for r in relations:
        key = (r['from'], r['to'], r['relationType'])
        if key not in seen:
            seen.add(key)
            unique_rels.append(r)

    print(f"Entities to create: {len(entities)}")
    print(f"Relations to create: {len(unique_rels)}")
    
    # Connect to Docker
    docker_path = shutil.which("docker")
    server_params = StdioServerParameters(
        command=docker_path,
        args=["run", "-i", "--rm", "-v", "mcp-memory-data:/app/dist", "mcp/memory"]
    )

    print("Connecting to MCP Memory Server...")
    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            
            if entities:
                await session.call_tool("create_entities", arguments={"entities": entities})
                print(f"Pushed {len(entities)} nodes.")
            
            if unique_rels:
                await session.call_tool("create_relations", arguments={"relations": unique_rels})
                print(f"Pushed {len(unique_rels)} edges.")

if __name__ == "__main__":
    asyncio.run(main())