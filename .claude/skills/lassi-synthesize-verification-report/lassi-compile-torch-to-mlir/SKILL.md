---
name: lassi-compile-torch-to-mlir
description: Lower a .pt PyTorch model to MLIR (torch / linalg / linalg-on-tensors / tosa / stablehlo) via torch-mlir. Use after lassi-export-model-to-pt to produce the dialect SODA / downstream tooling consumes.
allowed-tools:
  - Bash(python cli/lassi-compile-torch-to-mlir.py*)
  - Bash(python3 cli/lassi-compile-torch-to-mlir.py*)
  - Read
---

Loads `--model-path`, performs an optional dry forward pass, and lowers via torch-mlir using the chosen frontend (torchscript / fx / export) into the requested dialect.

## Invocation

```
python cli/lassi-compile-torch-to-mlir.py \
    --model-path foo.pt \
    --inputs '[{"shape":[1,3,224,224],"dtype":"float32"}]'  |  --inputs-file inputs.json \
    [--target torch|linalg|linalg-on-tensors|tosa|stablehlo] \
    [--frontend torchscript|fx|export] [--no-validate] [--output-path foo.mlir]
```

## Example

```
python cli/lassi-compile-torch-to-mlir.py --model-path build/foo.pt \
    --inputs '[{"shape":[1,3,224,224],"dtype":"float32"}]' \
    --target tosa --output-path build/foo.tosa.mlir
```

## Underlying impl

`lassi.integrations.torch_to_mlir.compile_torch_to_mlir_impl`
