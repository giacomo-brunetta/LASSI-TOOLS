"""Blocked, non-mutating PyTorch translation of PolyBench Floyd-Warshall."""
import torch
LASSI_PRECISION = {'storage': 'fp64', 'operator': 'fp64', 'accumulator': 'fp64', 'output': 'fp64'}
_MINI_N = 2800
_TILE = 8
_PAD_SENTINEL = 1000000

def build_inputs(device='cpu', dtype=torch.float64, fixture=None, dataset='default'):
    """Build the reference's deterministic MINI_DATASET path matrix."""
    if dataset not in ('default', 'large'):
        raise ValueError('only the PolyBench MINI_DATASET profile is supported')
    if fixture is not None:
        raise ValueError('floyd-warshall has no input fixture')
    indices = torch.arange(_MINI_N, device=device, dtype=torch.int64)
    i = indices[:, None]
    j = indices[None, :]
    path = torch.remainder(i * j, 7) + 1
    blocked = (torch.remainder(i + j, 13) == 0) | (torch.remainder(i + j, 7) == 0) | (torch.remainder(i + j, 11) == 0)
    path = torch.where(blocked, torch.full_like(path, 999), path)
    return (path.to(dtype=dtype),)

class FloydWarshall(torch.nn.Module):
    """Tile-scheduled Floyd-Warshall with an explicit min-plus tile reduction."""

    def forward(self, path):
        if path.ndim != 2 or path.shape[0] != path.shape[1]:
            raise ValueError('path must be a square rank-2 tensor')
        n = path.shape[0]
        padded_n = (n + _TILE - 1) // _TILE * _TILE
        pad = padded_n - n
        work = path.clone()
        if pad:
            right = torch.full((n, pad), _PAD_SENTINEL, dtype=path.dtype, device=path.device)
            bottom = torch.full((pad, padded_n), _PAD_SENTINEL, dtype=path.dtype, device=path.device)
            work = torch.cat((torch.cat((work, right), dim=1), bottom), dim=0)
        tiles_per_side = padded_n // _TILE
        for pivot_tile in range(tiles_per_side):
            begin = pivot_tile * _TILE
            end = begin + _TILE
            real_pivots = min(_TILE, n - begin)
            diagonal = work[begin:end, begin:end]
            for local_k in range(real_pivots):
                diagonal = torch.minimum(diagonal, diagonal[:, local_k:local_k + 1] + diagonal[local_k:local_k + 1, :])
            work[begin:end, begin:end] = diagonal
            pivot_row = work[begin:end, :]
            row_candidates = diagonal[:, :real_pivots].unsqueeze(2) + pivot_row[:real_pivots, :].unsqueeze(0)
            work[begin:end, :] = torch.minimum(pivot_row, torch.amin(row_candidates, dim=1))
            pivot_column = work[:, begin:end]
            column_candidates = pivot_column[:, :real_pivots].unsqueeze(2) + diagonal[:real_pivots, :].unsqueeze(0)
            work[:, begin:end] = torch.minimum(pivot_column, torch.amin(column_candidates, dim=1))
            tiles = work.reshape(tiles_per_side, _TILE, tiles_per_side, _TILE)
            tiles = tiles.permute(0, 2, 1, 3)
            column_panel = tiles[:, pivot_tile, :, :real_pivots]
            row_panel = tiles[pivot_tile, :, :real_pivots, :]
            trailing_candidates = column_panel[:, None, :, :, None] + row_panel[None, :, None, :, :]
            trailing = torch.minimum(tiles, torch.amin(trailing_candidates, dim=3))
            tile_ids = torch.arange(tiles_per_side, device=path.device)
            non_pivot = (tile_ids[:, None] != pivot_tile) & (tile_ids[None, :] != pivot_tile)
            tiles = torch.where(non_pivot[:, :, None, None], trailing, tiles)
            work = tiles.permute(0, 2, 1, 3).reshape(padded_n, padded_n)
        return work[:n, :n].reshape(-1)

def make_model():
    return FloydWarshall()
