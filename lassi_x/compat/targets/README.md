# Compatibility targets

Each directory is one exact compiler target. `target.yaml` is the runnable probe configuration;
`snapshot.json` and `wiki/` appear only after results have been published.

| Target | Configuration | Published snapshot |
|---|---:|---:|
| `a100-sami-inductor` | yes | no |
| `alcf-cs3-cerebras-pytorch` | yes | yes |
| `graphcore-pod64-poptorch` | yes | yes |
| `groq-r01-groqflow` | yes | yes |
| `torch-mlir-tosa` | yes | yes |

The A100 configuration is not a checkpoint by itself. Do not infer A100 operator support until a
snapshot has been generated and committed in that directory.

Each snapshot records the checker identity used by the current internal subsystem. The adjacent
`target.yaml` is the authoritative configuration for a new run.
