---
name: lassi-synthesize-tosa-with-soda
description: Run the shared soda-tools Makefile from an output folder that already contains `01_tosa.mlir`, stopping at the chosen stage (linalg / llvm-mode-ll / bambu-verilog / bambu-sim). Use to drive HLS synthesis once a TOSA MLIR is ready.
allowed-tools:
  - Bash(python cli/lassi-synthesize-tosa-with-soda.py*)
  - Bash(python3 cli/lassi-synthesize-tosa-with-soda.py*)
  - Read
---

Invokes soda-tools' shared Makefile with `STOP_STAGE=<stage>` from inside the output folder. A command log is always written to `<output_dir>/log.txt`.

## Invocation

```
python cli/lassi-synthesize-tosa-with-soda.py \
    --output-dir DIR \
    [--stage linalg|llvm-mode-ll|bambu-verilog|bambu-sim] \
    [--build-mode baseline|transformed]
```

## Example

```
python cli/lassi-synthesize-tosa-with-soda.py \
    --output-dir build/foo --stage bambu-verilog --build-mode transformed
```

## Underlying impl

`lassi.integrations.soda.synthesize_tosa_with_soda_impl`
