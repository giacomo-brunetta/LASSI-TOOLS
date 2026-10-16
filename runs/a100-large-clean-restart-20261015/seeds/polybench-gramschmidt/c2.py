import torch
LASSI_PRECISION = {'storage': 'input dtype', 'operator': 'input dtype', 'accumulator': 'input dtype', 'output': 'input dtype'}

def build_inputs(device='cpu', dtype=torch.float64, fixture=None, dataset='default'):
    if fixture is not None:
        raise ValueError('gramschmidt does not use an input fixture')
    if dataset not in {'default', 'large'}:
        raise ValueError(f'unsupported dataset: {dataset}')
    m, n = (1000, 1200)
    rows = torch.arange(m, device=device, dtype=torch.int64).unsqueeze(1)
    cols = torch.arange(n, device=device, dtype=torch.int64).unsqueeze(0)
    a = (rows * cols % m).to(dtype) / m * 100 + 10
    r0 = torch.zeros((n, n), device=device, dtype=dtype)
    q0 = torch.zeros((m, n), device=device, dtype=dtype)
    return (a, r0, q0)

def _source_order_sum(values):
    return torch.cumsum(values, dim=0)[-1]

class GramSchmidt(torch.nn.Module):

    def forward(self, a, r0, q0):
        work = a.clone()
        r = r0.clone()
        q = q0.clone()
        n = work.shape[1]
        cols = torch.arange(n, device=work.device)
        rows = torch.arange(n, device=work.device)
        for k in range(n):
            column = work[:, k]
            diag = torch.sqrt(_source_order_sum(column * column))
            qk = column / diag
            r_all = _source_order_sum(qk[:, None] * work)
            candidate = work - qk[:, None] * r_all[None, :]
            future = cols > k
            work = torch.where(future[None, :], candidate, work)
            r_row = torch.where(future, r_all, torch.where(cols == k, diag, torch.zeros_like(r_all)))
            r = torch.where(rows[:, None] == k, r_row[None, :], r)
            q = torch.where(cols == k, qk[:, None], q)
        return (r.reshape(-1), q.reshape(-1))

def make_model():
    return GramSchmidt()
