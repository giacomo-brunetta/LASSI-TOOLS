# Comparison tools

These external tools are Git submodules pinned to the commits recorded in the
parent repository. Their upstream sources and licenses remain in their own repositories.

| Directory | Upstream | Intended comparison |
| --- | --- | --- |
| `tenspiler/` | [tenspiler/tenspiler](https://github.com/tenspiler/tenspiler) | Translation to PyTorch using its PyTorch code generator |
| `herbie/` | [herbie-fp/herbie](https://github.com/herbie-fp/herbie) | Phase 2 expression optimization using the integrated Pherbie approach |

From the LASSI-TOOLS repository root:

```sh
git submodule update --init --recursive
git submodule status --recursive
```

Fetching sources does not build or install either tool. Follow the upstream setup
instructions in isolated environments, outside LASSI's locked Python environment.
Tenspiler requires its compiler and synthesis dependencies; Herbie has its own
Racket and native dependencies. Their builds are not part of the normal quality CI.

The framework does not yet provide end-to-end comparison adapters for these tools.
Generated implementations require independent validation against the original C
references. A pinned modern Herbie revision includes Pherbie functionality; it does
not by itself reproduce the historical ARITH 2021 experiment.
