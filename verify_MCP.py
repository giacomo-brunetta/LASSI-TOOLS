import asyncio
import shutil
import json
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

async def main():
    # 1. Connect to the same Docker container (persisted volume)
    docker_path = shutil.which("docker")
    server_params = StdioServerParameters(
        command=docker_path,
        args=["run", "-i", "--rm", "-v", "mcp-memory-data:/app/dist", "mcp/memory"]
    )

    print("Connecting to Memory Server to verify data...")
    
    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            
            # 2. Call the 'read_graph' tool
            # (The official memory server usually exposes read_graph)
            result = await session.call_tool("read_graph", arguments={})
            
            # The result is usually a list of TextContent objects.
            # We need to parse the JSON string inside the text property.
            graph_data = json.loads(result.content[0].text)
            
            print(f"\n--- Graph Status ---")
            print(f"Total Entities: {len(graph_data.get('entities', []))}")
            print(f"Total Relations: {len(graph_data.get('relations', []))}")
            
            print(f"\n--- Inspecting Nodes & Latencies ---")
            for node in graph_data.get('entities', []):
                name = node.get('name')
                observations = node.get('observations', [])
                
                print(f"Node: {name}")
                
                # Check for our JSON attribute payload
                found_attrs = False
                for obs in observations:
                    try:
                        # Try to parse the observation as JSON
                        attrs = json.loads(obs)
                        if "self_time_sec" in attrs:
                            print(f"  └─ Latency: {attrs['self_time_sec']}s (Children: {attrs['children_time_sec']}s)")
                            found_attrs = True
                    except json.JSONDecodeError:
                        # It's just a normal text observation
                        pass
                
                if not found_attrs:
                    print(f"  └─ (No latency attributes found)")

if __name__ == "__main__":
    asyncio.run(main())