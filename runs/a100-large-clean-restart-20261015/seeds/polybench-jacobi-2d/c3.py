import torch
LASSI_PRECISION = {'storage': 'input dtype', 'operator': 'input dtype', 'accumulator': 'input dtype', 'output': 'input dtype'}
_MINI_N = 1300
_TSTEPS = 500

def build_inputs(device='cpu', dtype=torch.float64, fixture=None, dataset='default'):
    """Construct the deterministic MINI_DATASET A and B arrays from the C source."""
    if dataset not in ('default', 'large'):
        raise ValueError('jacobi-2d candidate supports only the MINI_DATASET profile')
    if fixture is not None:
        raise ValueError('jacobi-2d does not use input fixtures')
    indices = torch.arange(_MINI_N, device=device, dtype=dtype)
    i = indices[:, None]
    j = indices[None, :]
    n_value = torch.as_tensor(_MINI_N, device=device, dtype=dtype)
    a = (i * (j + 2) + 2) / n_value
    b = (i * (j + 3) + 3) / n_value
    return (a, b)

class Jacobi2DDenseStencil(torch.nn.Module):

    def forward(self, a, b):
        if not isinstance(a, torch.Tensor) or not isinstance(b, torch.Tensor):
            raise TypeError('A and B must be torch tensors')
        if a.ndim != 2 or b.ndim != 2:
            raise ValueError('A and B must be rank-2 tensors')
        if a.shape != b.shape or a.shape[0] != a.shape[1]:
            raise ValueError('A and B must have equal square shapes')
        if a.shape[0] < 3:
            raise ValueError('Jacobi-2d requires n >= 3')
        if a.device != b.device or a.dtype != b.dtype:
            raise ValueError('A and B must have the same device and dtype')
        a_state = a.clone()
        b_state = b.clone()
        n = a.shape[0]
        m = n * n
        flat = torch.arange(m, device=a.device, dtype=torch.long)
        row = torch.div(flat, n, rounding_mode='floor')
        col = torch.remainder(flat, n)
        interior = (row > 0) & (row < n - 1) & (col > 0) & (col < n - 1)
        boundary = ~interior
        offsets = torch.stack((torch.zeros((), device=a.device, dtype=torch.long), -torch.ones((), device=a.device, dtype=torch.long), torch.ones((), device=a.device, dtype=torch.long), torch.full((), n, device=a.device, dtype=torch.long), torch.full((), -n, device=a.device, dtype=torch.long)))
        source_indices = flat[:, None] + offsets[None, :]
        row_matches_source = flat[:, None, None] == source_indices[None, :, :]
        stencil_mask = interior[:, None] & row_matches_source.any(dim=-1)
        stencil = stencil_mask.to(dtype=a.dtype) * a.new_tensor(0.2)
        identity_mask = flat[:, None] == flat[None, :]
        preserve = (boundary[:, None] & identity_mask).to(dtype=a.dtype)
        for _ in range(_TSTEPS):
            b_state = (stencil @ a_state.reshape(m, 1) + preserve @ b_state.reshape(m, 1)).reshape(n, n)
            a_state = (stencil @ b_state.reshape(m, 1) + preserve @ a_state.reshape(m, 1)).reshape(n, n)
        return a_state.reshape(-1)

def make_model():
    return Jacobi2DDenseStencil()
