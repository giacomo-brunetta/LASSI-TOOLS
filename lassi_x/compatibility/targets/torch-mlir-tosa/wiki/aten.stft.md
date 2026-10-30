# aten.stft

- Status: ❌ Unsupported
- Error: stft(torch.FloatTensor[2, 3], n_fft=1, hop_length=0, win_length=1, window=torch.FloatTensor{[2, 3]}, normalized=0, onesided=0, return_complex=0) : expected hop_length > 0, but got hop_length=0

## Attempts

- `float32_default`: unsupported; dtype=float32; error=stft(torch.FloatTensor[2, 3], n_fft=1, hop_length=0, win_length=1, window=torch.FloatTensor{[2, 3]}, normalized=0, onesided=0, return_complex=0) : expected hop_length > 0, but got hop_length=0
  spec=self: shape=(2, 3) dtype=float32; n_fft: 1; hop_length: None; win_length: None; window: shape=(2, 3) dtype=float32; normalized: False; onesided: False; return_complex: False
- `int32_default`: unsupported; dtype=int32; error=stft(torch.IntTensor[2, 3], n_fft=1, hop_length=0, win_length=1, window=torch.IntTensor{[2, 3]}, normalized=0, onesided=0, return_complex=0) : expected a tensor of floating point or complex values
  spec=self: shape=(2, 3) dtype=int32; n_fft: 1; hop_length: None; win_length: None; window: shape=(2, 3) dtype=int32; normalized: False; onesided: False; return_complex: False
  note=Retried with int32 tensors to detect dtype-sensitive coverage.
