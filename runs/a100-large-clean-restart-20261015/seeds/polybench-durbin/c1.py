"""Export-friendly PyTorch translation of PolyBench Durbin."""
import torch
LASSI_PRECISION = {'storage': 'float64', 'operator': 'float64', 'accumulator': 'float64', 'output': 'float64'}

def build_inputs(device='cpu', dtype=torch.float64, fixture=None, dataset='default'):
    """Construct the C initializer r[i] = n + 1 - i for MINI_DATASET."""
    del fixture
    if dataset not in ('default', 'large'):
        raise ValueError(f'unsupported dataset: {dataset!r}')
    n = 2000
    r = (n + 1 - torch.arange(n, device=device)).to(dtype=dtype)
    return (r,)

class Durbin(torch.nn.Module):

    def forward(self, r):
        n = r.shape[0]
        indices = torch.arange(n, dtype=torch.int64, device=r.device)
        y = torch.cat((-r[:1], torch.zeros_like(r[1:])))
        alpha = -r[0]
        beta = r.new_ones(())
        k0 = torch.ones((), dtype=torch.int64, device=r.device)
        n_tensor = torch.tensor(n, dtype=torch.int64, device=r.device)

        def cond(k, state, alpha_value, beta_value):
            return k < n_tensor

        def body(k, state, alpha_value, beta_value):
            beta_value = (1 - alpha_value * alpha_value) * beta_value

            def sum_cond(i, total):
                return i < k

            def sum_body(i, total):
                source = (k - i - 1).reshape(1)
                term = r.gather(0, source)[0] * state.gather(0, i.reshape(1))[0]
                return (i + 1, total + term)
            _, total = torch.while_loop(sum_cond, sum_body, (torch.zeros((), dtype=torch.int64, device=r.device), r.new_zeros(())))
            alpha_value = -(r.gather(0, k.reshape(1))[0] + total) / beta_value
            active = indices < k
            reverse_indices = (k - indices - 1).clamp(min=0)
            new_prefix = state + alpha_value * state.gather(0, reverse_indices)
            state = torch.where(active, new_prefix, state)
            state = torch.where(indices == k, alpha_value.expand_as(state), state)
            return (k + 1, state, alpha_value, beta_value)
        _, y, _, _ = torch.while_loop(cond, body, (k0, y, alpha, beta))
        return y.reshape(-1)

def make_model():
    return Durbin()
