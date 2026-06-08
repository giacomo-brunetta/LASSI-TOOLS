---
name: lassi-build-sanitized
description: Compile C/C++ with strict warnings and sanitizer instrumentation (address/undefined/leak/memory/thread) at one or more optimization levels. Use as the first verification gate when validating a C/C++ change.
allowed-tools:
  - Bash(clang *)
  - Bash(clang++ *)
  - Bash(gcc *)
  - Bash(g++ *)
  - Read
---

Compile the source with a strict warning baseline plus the requested sanitizers, at each requested `-O` level. Any compile failure or sanitizer-injected runtime failure means the candidate doesn't pass this gate.

## Recommended flag set

- **Warnings (treat as errors):** `-Wall -Wextra -Wpedantic -Werror`
- **Sanitizers (mix as needed):**
  - `-fsanitize=address` (ASan: heap/stack OOB, UAF)
  - `-fsanitize=undefined` (UBSan: signed overflow, shift OOB, etc.)
  - `-fsanitize=leak` (LSan; implied by ASan on Linux)
  - `-fsanitize=memory` (MSan: uninit reads; **must NOT mix with ASan**)
  - `-fsanitize=thread` (TSan: data races; **must NOT mix with ASan**)
- **Debug + frame pointers (better stack traces):** `-g -fno-omit-frame-pointer`

## Invocation pattern

For each opt level you care about, compile and link:

```bash
clang -std=c11 -Wall -Wextra -Wpedantic -Werror \
      -fsanitize=address,undefined -fno-omit-frame-pointer -g \
      -O2 src/foo.c -o build/foo.O2.san
```

(For C++, use `clang++ -std=c++17 ...`.)

Then run the resulting binary against a representative input — sanitizer hits cause non-zero exit with a diagnostic on stderr.

## Example loop

```bash
for opt in O0 O2 O3; do
  for san in "address,undefined"; do
    clang -std=c11 -Wall -Wextra -Wpedantic -Werror \
          -fsanitize=$san -fno-omit-frame-pointer -g \
          -$opt src/foo.c -o build/foo.$opt.${san//,/+}
  done
done
```

## Notes

- Apple-clang on macOS supports ASan/UBSan; **MSan and TSan are Linux-only** in practice.
- If the source contains undefined symbols or expects a driver, prefer `--build-mode shared_library` style: add `-shared -fPIC` and link as `libfoo.so`.
- Reproducer rule: on a sanitizer hit, save the failing input + the exact compile/run command before moving on.
