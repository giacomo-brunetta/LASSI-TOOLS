# aten.adaptive_max_pool2d

- Target: `groq-r01-groqflow`
- Family: `groq`
- Compiler: `groqflow`
- Inventory revision: `874f3a4e3cf90f54a92fe2bc1e6b8e4a5b5a1d58`

## Canonical compile cases

| Precision | Status | Input | Diagnostic |
|---|---|---|---|
| `fp16` / `canonical` | `compile_rejected` | self: shape=(1, 2, 8, 8) dtype=float16; output_size: [4, 4] | [91m Error: [0m[0mAttempted use Groq Compiler to compile your model's ONNX file into Groq Alan Assembly (.aa)[0m [0mfiles. However, this operation did not succeed.[0m [0mPlease contact GroqFlow support to determine a path forwards.[0m [0mMore information may be available in the log file at [0m[1m~/.cache/lassi-x/groq-compat/compat-aten.adaptive_max_pool2d-3c80a2ec0757/log_compile.txt[0m[0m[0m [0m[0m [0m ▄██████████████▄▐█▄▄▄▄█▌ ██████▌▄▌▄▐▐▌███▌▀▀██▀▀ ████▄█▌▄▌▄▐▐▌▀███▄▄█▌ ▄▄... |

> `compiled` applies only to the named case, precision, target, and compiler snapshot. It is not a runtime-correctness or performance result.
