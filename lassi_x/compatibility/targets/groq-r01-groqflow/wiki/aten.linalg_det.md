# aten.linalg_det

- Target: `groq-r01-groqflow`
- Family: `groq`
- Compiler: `groqflow`
- Inventory revision: `874f3a4e3cf90f54a92fe2bc1e6b8e4a5b5a1d58`

## Canonical compile cases

| Precision | Status | Input | Diagnostic |
|---|---|---|---|
| `fp16` / `canonical` | `compile_rejected` | A: shape=(3, 3) dtype=float16 | [91m Error: [0m[0mYou model contains ONNX operation(s) that are not supported by Groq Compiler:[0m [0m[0m[1mDet[0m[0m[0m [0mPlease replace these operation(s) in your model or contact[0m [0msales@groq.com to request improved operation support in Groq Compiler.[0m [0m[0m [0m ▄██████████████▄▐█▄▄▄▄█▌ ██████▌▄▌▄▐▐▌███▌▀▀██▀▀ ████▄█▌▄▌▄▐▐▌▀███▄▄█▌ ▄▄▄▄▄██████████████  [0m  |

> `compiled` applies only to the named case, precision, target, and compiler snapshot. It is not a runtime-correctness or performance result.
