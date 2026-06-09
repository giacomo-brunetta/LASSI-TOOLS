# Pipeline Context

This file is the seed instruction for the analyst-planner-coder chain.
Every agent consumes the prior artifact and writes the next one.

## Repository
- root: /Users/giacomobrunetta/Projects/LASSI-TOOLS/graph
- config: /Users/giacomobrunetta/Projects/LASSI-TOOLS/graph/graph_code_test.json

## Target source
- reference (read-only): test.c
- optimization target:   optimized.c

## Build
- compiler: clang
- correctness flags: -O0 -lm
- performance flags: -O3 -lm

## Workload
- benchmark args: '400 400 400'
- benchmark runs: 5
- target speedup (strict, %): > 0.00

## Golden behavior to preserve
- 8 golden case(s) captured from the reference build.
- The optimized variant must reproduce stdout byte-for-byte for every case.
- Sample inputs:
- args=''
- args='2 2 2'
- args='4 4 4'
- args='5 3 5'
- args='3 5 7'
