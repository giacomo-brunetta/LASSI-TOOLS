import subprocess
import sys

def stdio_safe_subprocess_run(cmd: list[str], timeout=60) -> subprocess.CompletedProcess:
    """Run a subprocess capturing both stdout and stderr, logging failures to stderr."""
    try:
        completed_process = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout
        )
        return completed_process

    except subprocess.TimeoutExpired as e:
        print(f"Command '{' '.join(cmd)}' timed out: {str(e)}", file=sys.stderr)
        raise

    except Exception as e:
        print(f"An error occurred while running command '{' '.join(cmd)}': {str(e)}", file=sys.stderr)
        raise