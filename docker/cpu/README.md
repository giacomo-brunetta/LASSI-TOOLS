# Minimal isolated CPU execution

The LLM agent and pipeline stay on the host. `execution.mode: docker` runs each
agent-issued command and candidate invocation in a fresh CPU container. The
trusted C oracle is still built/run on the host and numerical comparison stays
outside the candidate container. Requires Docker Engine/Desktop running and a
non-root macOS/Linux host user; the daemon must be local to the mounted files.

From the repository root:

```sh
docker build -f docker/cpu/Dockerfile -t lassi-x-cpu:0.1 .
python docker/cpu/smoke_test.py
```

Then set in your run YAML:

```yaml
execution:
  mode: docker
  docker:
    image: lassi-x-cpu:0.1
    cpus: 2
    memory_mb: 4096
    pids_limit: 128
```

```sh
lassi-x run my-run.yaml --until cpu-verified
```

For the benchmark suite, prepare a new campaign instead of editing the hashed
existing one:

```sh
python examples/cpu-ablation-suite/suite.py prepare \
  --models-config examples/polybench-jacobi-2d/run-luna-a100.yaml \
  --execution docker --output runs/cpu-suite-mini-luna-docker
python examples/cpu-ablation-suite/suite.py run \
  runs/cpu-suite-mini-luna-docker/suite.json --execute \
  --only polybench-3mm direct-dft
```

`--check-oracles` is C-only and still executes on the host. Docker mode is CPU-only;
for accelerator forks switch execution to the appropriate accelerator backend and
import the immutable CPU baseline as usual.

## Boundary and limits

- No network, Docker socket, credentials, home directory, repository bind mount,
  sibling candidate workspace or oracle mount enters the execution container.
- Read-only root filesystem, all capabilities dropped, no privilege escalation,
  host user's non-root UID/GID, CPU/RAM/process limits and bounded temporary storage.
- Only the current workspace is mounted. During validation it is read-only except
  `.lassi/` outputs. During agent commands it is writable, with `reference/` read-only.
- Container state and `/tmp` disappear after each command; workspace files persist.
  Keep multi-step shell/build commands in one invocation when they depend on `/tmp`.
- Host environment is not forwarded to the container. Only explicitly allowed
  thread-count settings can be overridden; defaults are one thread.
- Timeout/cancellation cleanup explicitly removes the named container, not merely
  its Docker client. Abrupt orchestrator death can still leave a running container;
  inspect names beginning `lassi-cpu-` and remove only the specific abandoned one.

This is not a sandbox for the orchestrator or model worker. Model/provider state,
credentials and agent skills still live on the host. It does not introduce sealed
holdout inputs, prevent a candidate from fabricating output, cap workspace output
disk usage, or provide cross-run hardware locks. Candidates can alter their own
workspace during generation but cannot normally see siblings from inside Docker.
Use an isolated host/VM for actively hostile code. Never grant agents Docker access.

The image contains CPU Torch, NumPy, Pydantic, GCC and the repository's runtime code,
not model credentials. Runtime package versions are fixed; base-image/package-manager
dependencies are not fully reproducible. Rebuild after runtime source changes, keep
the same built image across comparisons, and use its `sha256:` image ID (or registry
digest) as `execution.docker.image` to avoid a mutable tag. Containers never pull
images automatically. This initial image excludes GPU runtimes and extra libraries
such as SciPy; that is a deliberate execution-environment limit, not a Torch limit.

The runtime policy uses Docker's standard [container-run controls](https://docs.docker.com/reference/cli/docker/container/run/).
