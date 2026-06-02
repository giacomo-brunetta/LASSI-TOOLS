import subprocess
import sys

def stdio_safe_subprocess_run(cmd: list[str], timeout=60) -> subprocess.CompletedProcess:
    """
    Runs a subprocess command and captures output for the MCP tool.
    Logs errors to stderr to avoid breaking the MCP connection.
    """
    try:
        # capture_output=True automatically sets stdout and stderr to subprocess.PIPE.
        completed_process = subprocess.run(
            cmd,
            capture_output=True, 
            text=True,
            timeout=timeout
        )
        return completed_process

    except subprocess.TimeoutExpired as e:
        # Standard print() goes to stdout, which breaks MCP.
        print(f"Command '{' '.join(cmd)}' timed out: {str(e)}", file=sys.stderr)
        raise

    except Exception as e:
        print(f"An error occurred while running command '{' '.join(cmd)}': {str(e)}", file=sys.stderr)
        raise