# aten.stft

- Target: `graphcore-pod64-poptorch`
- Family: `ipu`
- Compiler: `poptorch`
- Inventory revision: `874f3a4e3cf90f54a92fe2bc1e6b8e4a5b5a1d58`

## Canonical compile cases

| Precision | Status | Input | Diagnostic |
|---|---|---|---|
| `fp16` / `canonical` | `needs_fixture` | — | RuntimeError: stft(torch.HalfTensor[2, 3], n_fft=2, hop_length=1, win_length=2, window=torch.HalfTensor{[2, 3]}, normalized=0, onesided=0, return_complex=0) : expected a 1D window tensor of size equal to win_length=2, but got window with size [2, 3] |
| `fp32` / `canonical` | `needs_fixture` | — | RuntimeError: stft(torch.FloatTensor[2, 3], n_fft=2, hop_length=1, win_length=2, window=torch.FloatTensor{[2, 3]}, normalized=0, onesided=0, return_complex=0) : expected a 1D window tensor of size equal to win_length=2, but got window with size [2, 3] |

> `compiled` applies only to the named case, precision, target, and compiler snapshot. It is not a runtime-correctness or performance result.
