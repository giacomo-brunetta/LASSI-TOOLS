# Live Groq result

The complete static `256 x 256` mutual-information graph compiled and executed
successfully on `groq-r01-gn-09.ai.alcf.anl.gov` on August 31, 2026. The
environment reported Torch `2.1.0+cpu`; GroqFlow did not expose a package
version. GroqFlow traced an FP32 input tensor, which is not by itself a claim
about native arithmetic precision.

The first run built the model from scratch and saved it under build name
`lassi-mutual-information-256-v1`. A second run loaded that build from the
GroqFlow cache and exercised the added dense case.

| Validation input | Groq result (bits) | FP64 reference (bits) | Absolute error (bits) |
|---|---:|---:|---:|
| Uniform diagonal | 8.000000000 | 8.000000000 | 0.000e+00 |
| Independent uniform | 0.000000000 | 0.000000000 | 0.000e+00 |
| 50% diagonal + 50% uniform | 3.023437500 | 3.018448260 | 4.989e-03 |

The Groq SDK's `GroqModel.benchmark(repetitions=20)` reported 87.891 us on the
initial run and 91.200 us on the cached run. The benchmark used the diagonal
input supplied during compilation. These are device SDK measurements of this
one static graph and shape, not host wall-clock timings or general performance
claims.

Evidence level:

- all nontrivial ATen operations had canonical compile evidence in the
  `groq-r01-groqflow` wiki snapshot;
- the entire composed model compiled, so this is stronger than per-operation
  evidence;
- three inputs executed on Groq hardware and were compared with an independent
  FP64 Shannon-formula reference;
- no arbitrary-shape or malformed-input behavior was tested.
