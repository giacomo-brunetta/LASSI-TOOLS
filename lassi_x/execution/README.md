# Execution infrastructure

This package runs commands and manages workspace files on compute resources.
It contains both the caller-side backends and the worker-side implementation.

| Module | Responsibility |
| --- | --- |
| `base.py` | Common backend interface for commands, files, and host discovery |
| `context.py` | Backend lifecycle, resource routing, and tool-server registration |
| `local.py` | Execute directly on the harness host |
| `docker.py` | Execute commands inside disposable CPU containers |
| `academy.py` | Transport requests to workers through Academy/Globus |
| `worker.py` | `ExecutionWorker`, the Academy agent serving one compute resource |
| `workspace.py` | Shared command execution, file operations, and host discovery |
| `transfer.py` | File transfers with chunking and integrity checks |

Local execution calls workspace operations directly. Academy execution sends
requests to an `ExecutionWorker`, which calls the same operations on its host.
Docker uses workspace operations for host-side files and container invocation.

The former `lassi_x.remote` package is consolidated here. Worker imports now use
`lassi_x.execution.worker`; shared operations use `lassi_x.execution.workspace`.
Deploy matching package revisions on the harness and remote workers.
