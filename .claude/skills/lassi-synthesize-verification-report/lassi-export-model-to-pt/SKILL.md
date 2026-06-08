---
name: lassi-export-model-to-pt
description: Load a PyTorch model class from a Python file and export it to a .pt file (torchscript / state_dict / full). Use after writing a PyTorch translation candidate to produce the artifact consumed by torch-mlir.
allowed-tools:
  - Bash(python cli/lassi-export-model-to-pt.py*)
  - Bash(python3 cli/lassi-export-model-to-pt.py*)
  - Read
---

Imports the named class from `--model-file`, instantiates it with `--init-args`, optionally loads `--weights-path`, and exports it. `torchscript` tries scripting first and falls back to tracing — `--input-shape` is required for tracing.

## Invocation

```
python cli/lassi-export-model-to-pt.py \
    --model-file PATH --class-name CLASS --output-path OUT.pt \
    [--init-args '{"k":v}' | --init-args-file init.json] \
    [--weights-path PATH] \
    [--export-type torchscript|state_dict|full] \
    [--input-shape '[1,3,224,224]' | --input-shape-file shape.json]
```

## Example

```
python cli/lassi-export-model-to-pt.py \
    --model-file examples/kernels/foo/foo_pt.py --class-name FooModel \
    --output-path build/foo.pt --input-shape '[1,3,224,224]'
```

## Underlying impl

`lassi.integrations.export_pt.export_model_to_pt_impl`
