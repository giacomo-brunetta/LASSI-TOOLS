"""Export-friendly PyTorch translation of the PolyBench mutual-information kernel."""
import torch
LASSI_PRECISION = {'storage': 'input dtype', 'operator': 'input dtype', 'accumulator': 'input dtype', 'output': 'input dtype'}

def build_inputs(device='cpu', dtype=torch.float64, fixture=None, dataset='default'):
    """Construct the C initializer's strictly positive diagonal mixture."""
    del fixture
    if dataset not in ('default', 'large'):
        raise ValueError(f'unsupported dataset profile: {dataset!r}')
    n = 256
    independent = 0.5 / (n * n)
    diagonal = 0.5 / n
    joint = torch.full((n, n), independent, device=device, dtype=dtype)
    joint = joint + torch.eye(n, device=device, dtype=dtype) * diagonal
    return (joint,)

class MutualInformation(torch.nn.Module):

    def forward(self, joint):
        n = joint.shape[-1]
        ones = joint.new_ones((n,))
        marginal_x = joint @ ones
        marginal_y = joint.transpose(0, 1) @ ones
        ones_flat = joint.reshape(-1).new_ones((joint.numel(),))
        joint_term = (joint * torch.log(joint)).reshape(-1) @ ones_flat
        x_term = marginal_x * torch.log(marginal_x) @ ones
        y_term = marginal_y * torch.log(marginal_y) @ ones
        return ((joint_term - x_term - y_term) / torch.log(ones[0] + ones[0])).reshape(-1)

def make_model():
    return MutualInformation()
