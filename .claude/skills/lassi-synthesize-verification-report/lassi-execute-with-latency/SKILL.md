---
name: lassi-execute-with-latency
description: Run a binary once and report wall-clock latency plus stdout/stderr. Use for a quick timing check, not statistically-stable benchmarking (use lassi-run-benchmark for that).
allowed-tools:
  - Bash(time *)
  - Bash(/usr/bin/time *)
  - Bash(./*)
---

Wraps the binary in `/usr/bin/time -p`, which prints `real/user/sys` seconds after the program exits.

## Invocation

```
/usr/bin/time -p <bin> <args...>
```

stdout/stderr from the binary are interleaved as usual; the three timing lines appear on stderr after the program exits.

## Example

```
/usr/bin/time -p ./build/sgemm 512 512 512
```

Capture stdout to a file when needed:

```
/usr/bin/time -p ./build/sgemm 512 512 512 > out.txt
```

## Notes

- `/usr/bin/time -p` is portable across macOS and Linux and prints POSIX-format timing. The shell builtin `time` on bash/zsh is fine too but format differs.
- For repeated runs / statistical stability use `hyperfine` (or invoke `lassi-run-benchmark` which wraps it).
