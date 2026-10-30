"""Check completed transfer timing without requiring a local CUDA device."""

import pytest
import torch

from lassi_x import measure_worker


def test_host_timer_waits_for_all_copies_and_replays_fresh_inputs(monkeypatch):
    pending = []
    reads = []

    class Buffer:
        def __init__(self, value):
            self.value = value

        def copy_(self, source, *, non_blocking):
            assert non_blocking
            pending.append(lambda: setattr(self, "value", source.value))

    def synchronize(device):
        assert device == "cuda:1"
        while pending:
            pending.pop(0)()

    def clock():
        reads.append(len(pending))
        return len(reads) * 1_000_000

    device_inputs = (Buffer(0), Buffer(0))
    host_inputs = (Buffer(3), Buffer(7))
    device_outputs = (Buffer(0), Buffer(0))
    host_outputs = (Buffer(-1), Buffer(-1))
    calls = []

    def model(*inputs):
        calls.append(True)
        pending.append(lambda: setattr(device_outputs[0], "value", sum(v.value for v in inputs)))
        pending.append(lambda: setattr(device_outputs[1], "value", inputs[0].value * 2))
        return device_outputs

    monkeypatch.setattr(measure_worker.torch.cuda, "synchronize", synchronize)
    monkeypatch.setattr(measure_worker.time, "perf_counter_ns", clock)
    for value, expected in [(3, (10, 6)), (5, (12, 10))]:
        host_inputs[0].value = value
        elapsed = measure_worker._time_host_to_host_call(
            model, device_inputs, host_inputs, host_outputs, device="cuda:1"
        )
        assert elapsed == pytest.approx(0.001)
        assert tuple(v.value for v in host_outputs) == expected
    assert len(calls) == 2
    assert reads == [0, 0, 0, 0]


@pytest.mark.hardware
@pytest.mark.skipif(not torch.cuda.is_available(), reason="requires CUDA")
def test_transfer_call_returns_all_outputs_for_changed_inputs():
    device = "cuda:0"
    with torch.cuda.device(device), torch.no_grad():
        inputs = (torch.zeros(16, device=device), torch.zeros(16, device=device))
        host_inputs = (torch.full((16,), 2.0, pin_memory=True), torch.ones(16, pin_memory=True))
        model = torch.cuda.make_graphed_callables(lambda x, y: (x + y, x - y), inputs)
        host_outputs = (torch.empty(16, pin_memory=True), torch.empty(16, pin_memory=True))
        for value in (2.0, 4.0):
            host_inputs[0].fill_(value)
            elapsed = measure_worker._time_host_to_host_call(
                model, inputs, host_inputs, host_outputs, device=device
            )
            assert elapsed > 0
            assert torch.equal(host_outputs[0], torch.full((16,), value + 1))
            assert torch.equal(host_outputs[1], torch.full((16,), value - 1))
