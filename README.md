# LASSI-Agentic Flow

This repository implements an agentic workflow focused on code performance and efficiency optimization.

## Key Components

### LASSI MCP Server
- Portable toolset for performance engineering capable of:
  - Reading machine information (CPU, GPU, memory)
  - Compiling and executing code
  - Measuring execution latency plus power/energy consumption
  - Running gprof profiling (flat and callgraph)
- Tool specifications:
  <details>
    <summary>Available Tools</summary>

    | Tool | Description | Parameters |
    |------|-------------|------------|
    | `compile_source` | Compiles a source file using a specific compiler. | `path`, `compiler`, `kwds` (optional), `output` (optional) |
    | `compile_to_mlir` | Compiles a C/C++ source file to MLIR using cgeist. | `path`, `kwds` (optional), `output` (optional) |
    | `gprof_profiling` | Compiles with gprof and returns the callgraph info. | `path`, `compiler`, `kwds` (optional), `args` (optional) |
    | `execute_with_latency` | Runs executables and returns output plus execution time. | `path`, `args` (optional) |
    | `execute_with_profile` | Runs executables and returns output plus power profiling report. | `path`, `args` (optional) |
    | `push_callgraph_to_memory` | Pushes gprof callgraph to the Memory MCP server. | `path`, `compiler` (optional), `kwds` (optional), `args` (optional) |
    | `get_machine_info` | Reads CPU and RAM information. | None |
    | `get_gpu_info` | Retrieves GPU information using SMI tools. | None |
  </details>

### Workflow (RooCode Optimized)
1. **Analyst Agent** – maps the codebase and produces a technical specification.
2. **Initial Profiler** – establishes a performance baseline (latency, energy, callgraph).
3. **Planning Agent** – creates an optimization plan, strategies, and expected outcomes.
4. **Coding Agent** – applies optimizations via a non-destructive Git workflow (branches + PRs).
5. **QA Verifier** – guarantees functional equivalence versus the "Golden Master" output.
6. **Post-Optimization Profiler** – re-runs profiling to confirm improvements versus baseline.

<details>
  <summary>Workflow Diagram</summary>

  ![Mermaid plot](assets/mermaid.png)
</details>

## Installation

1. **Install Roo Code**
   - Documentation: https://docs.roocode.com/getting-started/installing
2. **Install Python dependencies**
   ```bash
   conda create --name LASSI python=3.12
   conda activate LASSI
   pip install -r requirements.txt
   ```
3. **Register the LASSI MCP server**
   ```bash
   python configure_MCP.py
   ```
4. **Install Roo MCP Marketplace dependencies**

   Add the `github` and `memory` MCPs from the Roo Code marketplace.
   - More info: https://docs.roocode.com/features/marketplace
5. **Clone the LASSI workflow (remote VS Code server example)**
   ```bash
   mkdir -p $HOME/.vscode-server/data/User/globalStorage/rooveterinaryinc.roo-cline/workflows
   cp workflow.json $HOME/.vscode-server/data/User/globalStorage/rooveterinaryinc.roo-cline/workflows/lassi-workflow.json
   cd ~/LASSI-TOOLS
   ```
   - More info: https://docs.roocode.com/features/custom-modes
6. **Select the LASSI Workflow from the Roo Code modes dropdown**

7. **Verify MCP availability**
   ```bash
   python LASSI_MCP.py
   ```
   - Note: Roo Code will automatically spawn the LASSI MCP server once it is registerd. This command is just for checking..

8. **Other Dependencies**

   Check presence of compiler and profiling tools.
   ```bash
   gcc --version
   g++ --version
   make --version
   gprof --version
   ```
   If missing, install eseential tools.
   - In Conda: no sudo required. Can create conglicts with Polygeist.
      ```bash
      conda install -c conda-forge gcc_linux-64 gxx_linux-64 make binutils_linux-64
      ```
   - With APT: sudo required.
      ```bash
      sudo apt update
      sudo apt install -y build-essential binutils
      ```

9. **Add LASSI Modes and Rules**
   
   Copy rules folder in main `.roo`
   ```bash
   ln -s ./rules ~/.roo
   ```

   Copy `custom_modes.yaml` into Roo's setting folder.
   With VS-Code remote:
   ```bash
   ln -s custom_modes.yaml .vscode-server/data/User/globalStorage/rooveterinaryinc.roo-cline/settings/
   ```

10. **MLIR DEPS**

   Clone Polygeist
   ```bash
   git clone --recursive https://github.com/llvm/Polygeist.git
   cd Polygeist
   ```
   Build LLVM (this takes a while).
   ```bash
   mkdir -p llvm-project/build-release
   cd llvm-project/build-release

   cmake -G Ninja ../llvm \
   -DLLVM_ENABLE_PROJECTS="mlir;clang" \
   -DLLVM_TARGETS_TO_BUILD="host" \
   -DLLVM_ENABLE_ASSERTIONS=OFF \
   -DCMAKE_BUILD_TYPE=Release

   ninja
   ninja check-mlir
   cd ../..
   ```
   Build Polygeist.
   ```bash
   mkdir -p build-release
   cd build-release

   cmake -G Ninja .. \
   -DMLIR_DIR=$PWD/../llvm-project/build-release/lib/cmake/mlir \
   -DCLANG_DIR=$PWD/../llvm-project/build-release/lib/cmake/clang \
   -DLLVM_TARGETS_TO_BUILD="host" \
   -DLLVM_ENABLE_ASSERTIONS=OFF \
   -DCMAKE_BUILD_TYPE=Release

   ninja
   ```
   Add to path. (Add to `.bashrc` for persistence.)
   ```bash
   export PATH="$HOME/Polygeist/build-release/bin:$PATH"
   ```
   Check installation.
   ```bash
   cgeist --version
   polygeist-opt --version
   ```
## Example Usage
> _"I want to optimize the performance of my @~/TEST/matmul.c script. Make it as fast as possible."_

### Tips
- Use mentions to pass files. (e.g. `@TEST/file.c`) https://docs.roocode.com/basic-usage/context-mentions
