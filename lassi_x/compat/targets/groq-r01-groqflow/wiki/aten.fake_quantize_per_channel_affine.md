# aten.fake_quantize_per_channel_affine

- Target: `groq-r01-groqflow`
- Family: `groq`
- Compiler: `groqflow`
- Inventory revision: `874f3a4e3cf90f54a92fe2bc1e6b8e4a5b5a1d58`

## Canonical compile cases

| Precision | Status | Input | Diagnostic |
|---|---|---|---|
| `fp16` / `canonical` | `compile_rejected` | self: shape=(2, 3) dtype=float16; scale: shape=(3,) dtype=float32; zero_point: shape=(3,) dtype=int32; axis: 1; quant_min: 0; quant_max: 255 | [91m Error: [0m[0mAttempted use Groq Compiler to compile your model's ONNX file into Groq Alan Assembly (.aa)[0m [0mfiles. However, this operation did not succeed.[0m [0mPlease contact GroqFlow support to determine a path forwards.[0m [0mMore information may be available in the log file at [0m[1m~/.cache/lassi-x/groq-compat/compat-aten.fake_quantize_per_channel_affine-73666a690592/log_compile.txt[0m[0m[0m [0m[0m [0m ▄██████████████▄▐█▄▄▄▄█▌ ██████▌▄▌▄▐▐▌███▌▀▀██▀▀ ████▄█▌▄▌▄▐... |

> `compiled` applies only to the named case, precision, target, and compiler snapshot. It is not a runtime-correctness or performance result.
