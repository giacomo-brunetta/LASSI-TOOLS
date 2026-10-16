"""Export-friendly PyTorch translation of PolyBench mutual-information."""
import torch
from torch import nn
LASSI_PRECISION = {'storage': 'input dtype', 'operator': 'input dtype', 'accumulator': 'input dtype', 'output': 'input dtype'}

def build_inputs(device='cpu', dtype=torch.float64, fixture=None, dataset='default'):
    """Build the deterministic strictly-positive MINI joint distribution."""
    if fixture is not None:
        raise ValueError('mutual-information does not use fixtures')
    if dataset == 'default':
        dataset = 'large'
    dataset_sizes = {'large': 256}
    if dataset not in dataset_sizes:
        raise ValueError('only the mini dataset is supported')
    n = dataset_sizes[dataset]
    joint = torch.empty((n, n), device=device, dtype=dtype)
    independent = joint.new_tensor(0.5) / (n * n)
    diagonal = joint.new_tensor(0.5) / n
    joint.fill_(independent)
    return (joint + torch.eye(n, device=device, dtype=dtype) * diagonal,)

class MutualInformation(nn.Module):
    """Compute the MI live-out for a strictly-positive square joint matrix."""

    def forward(self, joint):
        marginal_x = joint.sum(dim=1)
        marginal_y = joint.sum(dim=0)
        log_ratio = torch.log(joint) - torch.log(marginal_x).unsqueeze(1) - torch.log(marginal_y).unsqueeze(0)
        mi = (joint * log_ratio).sum() / torch.log(joint.new_tensor(2.0))
        return mi.reshape(-1)

def make_model():
    return MutualInformation()
